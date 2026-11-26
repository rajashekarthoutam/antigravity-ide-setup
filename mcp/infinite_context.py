"""
Infinite-Horizon Context Engine for Antigravity IDE.

Orchestrates Epoch-Aligned KV-Cache Preservation, Preventative FTS5 Virtualization,
DCP Cleanup (dedup, write-supersede, old error arg purging), JetBrains Observation
Masking, and Anchored State Capsule folding while keeping raw and billing metrics separated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from context_vault import (
    ContextVirtualizer,
    fetch_virtual_slice,
    search_virtual_context,
    virtualize_output,
)
from text_filters import (
    DEFAULT_VIRTUALIZE_CHARS,
    DEFAULT_VIRTUALIZE_LINES,
    cli_compress,
    count_tokens_safe,
    elide_output,
    extract_error_tail,
    redact_secrets,
    resolve_home_dir,
    resolve_vault_db_path,
)

COMPACT_OB_CHARS = 600
MAX_CAPSULE_TOKENS = 450

_PATH_TOKEN_RE = re.compile(r"[A-Za-z]:[\\/][^\s'\"]+|[A-Za-z0-9_./-]+\.[A-Za-z]{1,8}")
_DECISION_RE = re.compile(
    r"\b(?:decided|decision|use|using|switched|fixed|replaced|enforced|resolved|chosen|keep)\b",
    re.IGNORECASE,
)

__all__ = [
    "COMPACT_OB_CHARS",
    "DEFAULT_VIRTUALIZE_CHARS",
    "DEFAULT_VIRTUALIZE_LINES",
    "MAX_CAPSULE_TOKENS",
    "ContextVirtualizer",
    "cli_compress",
    "compact_conversation_loop",
    "count_tokens_safe",
    "elide_output",
    "extract_error_tail",
    "fetch_virtual_slice",
    "redact_secrets",
    "resolve_home_dir",
    "resolve_vault_db_path",
    "run_compressed",
    "search_virtual_context",
    "virtualize_output",
]


def _extract_text_and_meta(msg: Any) -> dict[str, Any]:
    """Normalize OpenAI, Anthropic, Antigravity transcript, or simple turn dicts."""
    if isinstance(msg, str):
        return {
            "role": "user",
            "content": msg,
            "tool": "",
            "args": {},
            "target": "",
            "is_error": False,
            "handle": "",
        }
    if not isinstance(msg, dict):
        return {
            "role": "assistant",
            "content": str(msg),
            "tool": "",
            "args": {},
            "target": "",
            "is_error": False,
            "handle": "",
        }

    role = str(msg.get("role") or msg.get("source") or "assistant").lower()
    raw_content = msg.get("content", "")
    if isinstance(raw_content, list):
        parts = []
        for blk in raw_content:
            if isinstance(blk, dict):
                parts.append(
                    str(blk.get("text") or blk.get("content") or json.dumps(blk))
                )
            else:
                parts.append(str(blk))
        content = "\n".join(parts)
    else:
        content = str(raw_content or "")
    if msg.get("thinking") and not content:
        content = str(msg["thinking"])

    tool = str(msg.get("tool") or msg.get("name") or "")
    args = msg.get("args") if isinstance(msg.get("args"), dict) else {}
    if not tool and isinstance(msg.get("tool_calls"), list) and msg["tool_calls"]:
        tc = msg["tool_calls"][0]
        if isinstance(tc, dict):
            fn = tc.get("function") if isinstance(tc.get("function"), dict) else tc
            tool = str(fn.get("name") or "")
            raw_a = fn.get("arguments") or fn.get("args")
            if isinstance(raw_a, str):
                try:
                    raw_a = json.loads(raw_a)
                except Exception:
                    raw_a = {"raw": raw_a}
            if isinstance(raw_a, dict):
                args = raw_a

    target = str(
        msg.get("target")
        or args.get("TargetFile")
        or args.get("file_path")
        or args.get("path")
        or ""
    )
    if not target and content:
        m = _PATH_TOKEN_RE.search(content)
        if m and ("/" in m.group(0) or "\\" in m.group(0) or tool):
            target = m.group(0)

    is_error = bool(msg.get("is_error")) or (
        role == "tool"
        and bool(
            re.search(
                r"\b(?:error|traceback|failed|exception)\b", content, re.IGNORECASE
            )
        )
    )
    return {
        "role": role,
        "content": content,
        "tool": tool,
        "args": args,
        "target": target,
        "is_error": is_error,
        "handle": str(msg.get("handle") or ""),
    }


def _serialize_message(m: dict[str, Any]) -> str:
    extra = ""
    if m.get("tool"):
        arg_str = json.dumps(m.get("args", {}), sort_keys=True) if m.get("args") else ""
        extra = f" [{m['tool']} {arg_str}]"
    return f"{m['role']}{extra}: {m['content']}"


def _messages_tokens(msgs: list[dict[str, Any]]) -> int:
    return sum(count_tokens_safe(_serialize_message(m)) + 4 for m in msgs)


def _format_capsule_text(capsule: dict[str, Any], epoch_id: int) -> str:
    """Serialize Anchored State Capsule in compact bounded format (<= MAX_CAPSULE_TOKENS)."""
    payload = {
        "epoch": epoch_id,
        "intent": (capsule.get("intent") or "")[:180],
        "files": (capsule.get("modified_files") or [])[-10:],
        "decisions": [d[:110] for d in (capsule.get("decisions") or [])[-4:]],
        "errors": [e[:140] for e in (capsule.get("active_errors") or [])[-3:]],
        "handles": (capsule.get("handles") or [])[-8:],
        "next": (capsule.get("next_step") or "")[:160],
    }
    text = f"[epoch:{epoch_id}] ARCHIVED_STATE " + json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    )
    if count_tokens_safe(text) > MAX_CAPSULE_TOKENS:
        payload["decisions"] = payload["decisions"][-2:]
        payload["files"] = payload["files"][-6:]
        payload["handles"] = payload["handles"][-4:]
        text = f"[epoch:{epoch_id}] ARCHIVED_STATE " + json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        )
    return text


def _update_capsule(
    prev_capsule: dict[str, Any],
    historical: list[dict[str, Any]],
    new_handles: list[str],
) -> dict[str, Any]:
    capsule = {
        "intent": str(prev_capsule.get("intent") or ""),
        "modified_files": list(prev_capsule.get("modified_files") or []),
        "decisions": list(prev_capsule.get("decisions") or []),
        "active_errors": list(prev_capsule.get("active_errors") or []),
        "handles": list(prev_capsule.get("handles") or []),
        "next_step": str(prev_capsule.get("next_step") or ""),
    }
    for m in historical:
        content = m.get("content", "")
        if content.startswith("[epoch:"):
            continue
        if not capsule["intent"] and m["role"] == "user" and content.strip():
            capsule["intent"] = content.strip().splitlines()[0][:180]
        if m.get("target") and m["target"] not in capsule["modified_files"]:
            capsule["modified_files"].append(m["target"])
        if m.get("is_error"):
            sig = extract_error_tail(content, 140)
            if sig not in capsule["active_errors"]:
                capsule["active_errors"].append(sig)
        elif m["role"] in ("assistant", "model") and content:
            if "all tests pass" in content.lower() or "exit code 0" in content.lower():
                capsule["active_errors"] = []
            for ln in content.splitlines():
                if _DECISION_RE.search(ln) and len(ln.strip()) > 12:
                    clean_d = ln.strip()[:110]
                    if clean_d not in capsule["decisions"]:
                        capsule["decisions"].append(clean_d)
        if m["role"] in ("user", "assistant", "model") and content.strip():
            capsule["next_step"] = content.strip().splitlines()[-1][:160]

    for h in new_handles:
        if h and h not in capsule["handles"]:
            capsule["handles"].append(h)

    capsule["modified_files"] = capsule["modified_files"][-12:]
    capsule["decisions"] = capsule["decisions"][-6:]
    capsule["active_errors"] = capsule["active_errors"][-3:]
    capsule["handles"] = capsule["handles"][-10:]
    return capsule


def compact_conversation_loop(
    messages: list[Any],
    window: int = 4,
    token_budget: int = 6000,
    epoch_size: int = 12,
    state: dict[str, Any] | None = None,
    force: bool = False,
    vault_db: str | Path | None = None,
    virtualizer: ContextVirtualizer | None = None,
) -> dict[str, Any]:
    """
    Compact a continuous bloated multi-turn conversation while preserving active
    recent turns, Anchored State Capsule continuity, and KV-cache prefix alignment.
    """
    norm_msgs = [_extract_text_and_meta(m) for m in (messages or [])]
    virt = virtualizer or ContextVirtualizer(db_path=vault_db)
    win = max(1, int(window or 4))
    ep_size = max(2, int(epoch_size or 12))
    budget = max(500, int(token_budget or 6000))

    prev = dict(state or {})
    epoch_id = int(prev.get("epoch_id", 0))
    prefix_end = min(int(prev.get("prefix_end_index", 0)), len(norm_msgs))
    last_out_len = int(prev.get("last_output_len", 0))
    has_capsule = bool(norm_msgs and norm_msgs[0]["content"].startswith("[epoch:"))

    if not prev:
        raw_turns_added = len(norm_msgs)
        turns_since_epoch = len(norm_msgs)
        cumulative_before = _messages_tokens(norm_msgs)
        cumulative_after = 0
        total_turns_seen = len(norm_msgs)
    else:
        base_len = last_out_len if has_capsule else int(prev.get("last_input_len", 0))
        raw_turns_added = max(0, len(norm_msgs) - base_len)
        turns_since_epoch = int(prev.get("turns_since_epoch", 0)) + raw_turns_added
        total_turns_seen = int(prev.get("total_turns_seen", 0)) + raw_turns_added
        added_slice = norm_msgs[base_len:] if base_len < len(norm_msgs) else []
        prev_raw_total = int(prev.get("last_raw_snapshot_tokens", 0))
        new_raw_snapshot = prev_raw_total + _messages_tokens(added_slice)
        cumulative_before = int(prev.get("cumulative_raw_before", 0)) + new_raw_snapshot
        cumulative_after = int(prev.get("cumulative_raw_after", 0))

    working_msgs: list[dict[str, Any]] = []
    scan_start = prefix_end if (prev and has_capsule) else 0
    for idx, m in enumerate(norm_msgs):
        m_copy = dict(m)
        is_new_turn = idx >= (last_out_len if prev else 0)
        if (
            is_new_turn
            and (m_copy["role"] == "tool" or m_copy["tool"])
            and len(m_copy["content"]) > DEFAULT_VIRTUALIZE_CHARS
        ):
            res = virt.virtualize_output(
                m_copy["content"],
                label=m_copy["tool"] or m_copy["target"] or "tool_output",
                command=m_copy["tool"],
            )
            m_copy["content"] = res["digest"]
            if res.get("handle"):
                m_copy["handle"] = res["handle"]
        working_msgs.append(m_copy)

    raw_tokens_before = _messages_tokens(norm_msgs)
    uncompacted_tokens = _messages_tokens(working_msgs[scan_start:])
    should_compact = (
        force or turns_since_epoch >= ep_size or uncompacted_tokens > budget
    )

    new_handles: list[str] = []
    capsule = dict(prev.get("capsule") or {})

    if not should_compact:
        out_msgs = working_msgs
        compacted = False
        new_prefix_end = prefix_end
    else:
        compacted = True
        epoch_id += 1
        turns_since_epoch = 0

        split_idx = max(0, len(working_msgs) - win)
        historical = working_msgs[:split_idx]
        recent = working_msgs[split_idx:]

        recent_keys: set[tuple[str, str]] = set()
        recent_targets: set[str] = set()
        for rm in recent:
            if rm.get("tool"):
                recent_keys.add(
                    (rm["tool"], json.dumps(rm.get("args", {}), sort_keys=True))
                )
            if rm.get("target"):
                recent_targets.add(rm["target"])

        processed_hist: list[dict[str, Any]] = []
        seen_hist_calls: dict[tuple[str, str], int] = {}
        for idx, hm in enumerate(historical):
            if hm["content"].startswith("[epoch:"):
                continue
            hm_clean = dict(hm)
            if hm_clean.get("tool") and hm_clean.get("args"):
                call_key = (
                    hm_clean["tool"],
                    json.dumps(hm_clean["args"], sort_keys=True),
                )
                if hm_clean.get("is_error") and idx < len(working_msgs) - 2:
                    if any(
                        isinstance(v, str) and len(v) > 200
                        for v in hm_clean["args"].values()
                    ):
                        hm_clean["args"] = {"purged": True}
                    hm_clean["content"] = extract_error_tail(hm_clean["content"], 180)
                if call_key in recent_keys:
                    continue
                seen_hist_calls[call_key] = idx
            if (
                hm_clean.get("target")
                and hm_clean["target"] in recent_targets
                and hm_clean["role"] == "tool"
            ):
                continue

            if (hm_clean["role"] == "tool" or hm_clean["tool"]) and len(
                hm_clean["content"]
            ) > COMPACT_OB_CHARS:
                v_res = virt.virtualize_output(
                    hm_clean["content"],
                    label=hm_clean["tool"] or hm_clean["target"] or "historical_output",
                    threshold_chars=COMPACT_OB_CHARS,
                    threshold_lines=16,
                )
                if v_res.get("handle"):
                    new_handles.append(v_res["handle"])
                    hm_clean["handle"] = v_res["handle"]
                hm_clean["content"] = (
                    f"[masked:{hm_clean['tool'] or 'tool'}({hm_clean['target'] or '-'}) "
                    f"-> {v_res['raw_tokens']}tok, handle={v_res.get('handle') or 'inline'}]"
                )
            elif hm_clean.get("handle"):
                new_handles.append(str(hm_clean["handle"]))
            processed_hist.append(hm_clean)

        final_hist: list[dict[str, Any]] = []
        for idx, hm in enumerate(processed_hist):
            if hm.get("tool") and hm.get("args") and not hm.get("is_error"):
                ck = (hm["tool"], json.dumps(hm["args"], sort_keys=True))
                if seen_hist_calls.get(ck, idx) != idx:
                    continue
            final_hist.append(hm)

        capsule = _update_capsule(capsule, final_hist, new_handles)
        capsule_msg = {
            "role": "system",
            "content": _format_capsule_text(capsule, epoch_id),
            "tool": "",
            "args": {},
            "target": "",
            "is_error": False,
            "handle": "",
        }

        bounded_recent: list[dict[str, Any]] = []
        for rm in recent:
            rm_c = dict(rm)
            if (rm_c["role"] == "tool" or rm_c["tool"]) and len(
                rm_c["content"]
            ) > DEFAULT_VIRTUALIZE_CHARS:
                v_res = virt.virtualize_output(
                    rm_c["content"],
                    label=rm_c["tool"] or rm_c["target"] or "recent_output",
                )
                rm_c["content"] = v_res["digest"]
                if v_res.get("handle"):
                    new_handles.append(v_res["handle"])
                    rm_c["handle"] = v_res["handle"]
            bounded_recent.append(rm_c)

        out_msgs = [capsule_msg] + bounded_recent
        new_prefix_end = 1

    raw_tokens_after = _messages_tokens(out_msgs)
    if not prev:
        cumulative_after = raw_tokens_after
        raw_snapshot = raw_tokens_before
    else:
        cumulative_after += raw_tokens_after
        tail = (
            norm_msgs[last_out_len:]
            if has_capsule
            else norm_msgs[int(prev.get("last_input_len", 0)) :]
        )
        raw_snapshot = int(
            prev.get("last_raw_snapshot_tokens", raw_tokens_before)
        ) + _messages_tokens(tail)
        raw_tokens_before = max(raw_tokens_before, raw_snapshot)

    reduction_pct = (
        round((1.0 - (raw_tokens_after / raw_tokens_before)) * 100.0, 2)
        if raw_tokens_before > 0
        else 0.0
    )
    cum_reduction_pct = (
        round((1.0 - (cumulative_after / cumulative_before)) * 100.0, 2)
        if cumulative_before > 0
        else reduction_pct
    )

    compare_bound = min(last_out_len, len(out_msgs)) if (not compacted and prev) else 0
    prefix_slice = out_msgs[:compare_bound] if compare_bound > 0 else []
    prefix_digest_now = hashlib.sha256(
        json.dumps(prefix_slice, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    prev_full_hash = str(prev.get("output_prefix_hash", ""))
    if (
        prev
        and not compacted
        and compare_bound > 0
        and prev_full_hash
        and prefix_digest_now == prev_full_hash
    ):
        cached_tokens = _messages_tokens(prefix_slice)
        kv_hit_pct = (
            round((cached_tokens / raw_tokens_after) * 100.0, 2)
            if raw_tokens_after > 0
            else 0.0
        )
    else:
        cached_tokens = 0
        kv_hit_pct = 0.0

    uncached_tokens = max(0, raw_tokens_after - cached_tokens)
    effective_billed_tokens = round(uncached_tokens + cached_tokens * 0.10)

    next_state = {
        "epoch_id": epoch_id,
        "total_turns_seen": total_turns_seen,
        "turns_since_epoch": turns_since_epoch,
        "prefix_end_index": new_prefix_end,
        "prefix_hash": hashlib.sha256(
            json.dumps(out_msgs[:new_prefix_end], sort_keys=True).encode("utf-8")
        ).hexdigest()[:16],
        "output_prefix_hash": hashlib.sha256(
            json.dumps(out_msgs, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16],
        "last_output_len": len(out_msgs),
        "last_input_len": len(norm_msgs),
        "last_raw_snapshot_tokens": raw_snapshot,
        "cumulative_raw_before": cumulative_before,
        "cumulative_raw_after": cumulative_after,
        "capsule": capsule,
        "virtual_handles": list(
            dict.fromkeys(list(prev.get("virtual_handles") or []) + new_handles)
        )[-25:],
    }

    return {
        "status": "COMPACTED" if compacted else "APPENDED_EPOCH",
        "compacted": compacted,
        "epoch_id": epoch_id,
        "messages": out_msgs,
        "state": next_state,
        "capsule": capsule,
        "metrics": {
            "raw_tokens_before": raw_tokens_before,
            "raw_tokens_after": raw_tokens_after,
            "raw_reduction_pct": reduction_pct,
            "cumulative_raw_before": cumulative_before,
            "cumulative_raw_after": cumulative_after,
            "cumulative_reduction_pct": cum_reduction_pct,
            "estimated_kv_cache_hit_pct": kv_hit_pct,
            "advisory_effective_cost_tokens": effective_billed_tokens,
        },
    }


def run_compressed(
    command: str,
    label: str = "",
    threshold_chars: int = DEFAULT_VIRTUALIZE_CHARS,
    threshold_lines: int = DEFAULT_VIRTUALIZE_LINES,
    vault_db: str | Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Execute a shell command, redact secrets, virtualize oversized stdout/stderr into
    SQLite FTS5 (`ctx://`), and return a compressed diagnostic summary + exit code.
    Prevents bloated terminal output from ever entering live IDE conversation context.
    """
    res = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    combined = "\n".join(
        part for part in (res.stdout.strip(), res.stderr.strip()) if part
    )
    virt = ContextVirtualizer(db_path=vault_db).virtualize_output(
        content=combined,
        label=label or command.split()[0] if command.split() else "cmd",
        command=command,
        threshold_chars=threshold_chars,
        threshold_lines=threshold_lines,
    )
    return {
        "exit_code": res.returncode,
        "command": command,
        **virt,
    }


def _cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compress/virtualize noisy CLI output into ctx:// FTS5 vault before IDE context."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--exec", dest="exec_cmd", help="Shell command string to execute compressed."
    )
    group.add_argument(
        "--pipe", action="store_true", help="Compress and virtualize stdin stream."
    )
    parser.add_argument("--label", default="", help="Vault entry label.")
    parser.add_argument("--threshold", type=int, default=DEFAULT_VIRTUALIZE_CHARS)
    args = parser.parse_args(argv)

    if args.exec_cmd:
        res = run_compressed(
            args.exec_cmd,
            label=args.label,
            threshold_chars=args.threshold,
        )
        header = f"[exit={res['exit_code']}]"
        if res.get("handle"):
            print(f"{header} {res['digest']}")
        else:
            print(f"{header}\n{res['digest']}" if res["digest"] else header)
        return int(res["exit_code"])

    raw_stdin = sys.stdin.read()
    res = virtualize_output(
        raw_stdin,
        label=args.label or "stdin_stream",
        threshold_chars=args.threshold,
    )
    print(res["digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())
