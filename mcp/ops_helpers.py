"""
Operational Utilities for God-Mode MCP:
Workspace Token Audit, TOON Serializer, Content-Hash Cache, Checkpoints,
Preflight Linters, and Cross-Platform Installer/Doctor Runners.

Pure helper module (imports only from `text_filters` and `infinite_context`).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Any

from infinite_context import cli_compress, count_tokens_safe, resolve_home_dir

_BASE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BASE_DIR.parent if _BASE_DIR.name == "mcp" else _BASE_DIR

_DEFAULT_CACHE_SENTINEL = Path(
    os.path.expanduser(r"~\.gemini\config\god_mode_tool_cache.json")
)
_DEFAULT_CP_SENTINEL = Path(os.path.expanduser(r"~\.gemini\checkpoints"))
_TOOL_OUTPUT_CACHE: dict[str, Any] = {}


def _resolve_cache_path(override: Path | None = None) -> Path:
    if override and override != _DEFAULT_CACHE_SENTINEL:
        return override
    return resolve_home_dir() / "config" / "god_mode_tool_cache.json"


def _resolve_cp_dir(override: Path | None = None) -> Path:
    if override and override != _DEFAULT_CP_SENTINEL:
        return override
    return resolve_home_dir() / "checkpoints"


def audit_workspace_tokens() -> dict[str, Any]:
    """Audits token consumption across Antigravity conversation transcripts."""
    try:
        home_base = resolve_home_dir()
        brain_dirs = [
            home_base / "antigravity" / "brain",
            home_base / "antigravity-ide" / "brain",
        ]
        existing = [d for d in brain_dirs if d.exists()]
        if not existing:
            return {
                "error": "Brain directory not found",
                "checked": [str(d) for d in brain_dirs],
            }

        sessions: dict[str, dict[str, int]] = {}
        total_tokens = 0
        active_session = ""
        latest_mtime = 0.0
        for brain_dir in existing:
            for item in brain_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    tpath = item / ".system_generated" / "logs" / "transcript.jsonl"
                    if not tpath.exists():
                        continue
                    mtime = tpath.stat().st_mtime
                    s_tokens = 0
                    steps = 0
                    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            try:
                                d = json.loads(line)
                                text = (
                                    (d.get("content") or "")
                                    + "\n"
                                    + (d.get("thinking") or "")
                                )
                                if "tool_calls" in d:
                                    text += "\n" + json.dumps(d["tool_calls"])
                                s_tokens += count_tokens_safe(text)
                                steps += 1
                            except (json.JSONDecodeError, KeyError, TypeError):
                                continue
                    sessions[item.name] = {"tokens": s_tokens, "steps": steps}
                    total_tokens += s_tokens
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        active_session = item.name

        return {
            "active_session": active_session,
            "active_tokens": sessions.get(active_session, {}).get("tokens", 0),
            "workspace_total_tokens": total_tokens,
            "sessions": sessions,
        }
    except Exception as e:
        return {"error": str(e)}


def llmtrim_compress(raw_text: str, preset: str = "agent") -> str:
    """Compresses terminal logs or text via llmtrim (with 0-LLM `cli_compress` fallback)."""
    try:
        from llmtrim import Provider, compress  # type: ignore[import-not-found]

        payload = json.dumps({"contents": [{"parts": [{"text": raw_text}]}]})
        res = compress(payload, Provider.GOOGLE, preset)
        data = json.loads(res.request_json)
        compressed = data["contents"][0]["parts"][0]["text"]
        saved_pct = round(
            (1 - res.input_tokens_after / max(res.input_tokens_before, 1)) * 100
        )
        return (
            f"[llmtrim optimized: {res.input_tokens_before} -> "
            f"{res.input_tokens_after} tokens (-{saved_pct}%)]:\n{compressed}"
        )
    except Exception:
        compressed = cli_compress(raw_text)
        before = count_tokens_safe(raw_text)
        after = count_tokens_safe(compressed)
        pct = round((1 - after / max(before, 1)) * 100)
        return f"[cli_compress: {before} -> {after} tokens (-{pct}%)]:\n{compressed}"


def guardrail_scan_dir(dir_path: str = ".") -> str:
    """Directs agents to AST probes rather than raw recursive directory dumps."""
    return (
        f"[DIRECTORY GUARDRAIL ACTIVE for '{dir_path}']:\n"
        "1. Language & complexity stats: 'repo_shape_probe'\n"
        "2. PageRank architectural map (1,024 token budget): 'pagerank_repo_map'\n"
        "3. File structural outline: 'get_file_outline'"
    )


def ruff_fix_preflight(target_file: str) -> str:
    """Runs `ruff check --fix` and `ruff format` locally in 5ms (0 LLM tokens)."""
    ruff_resolved = shutil.which("ruff")
    ruff_bin = (
        Path(ruff_resolved)
        if ruff_resolved
        else (Path(sys.executable).parent / "Scripts" / "ruff.exe")
    )
    if not ruff_bin.exists():
        return "Ruff binary not found."
    try:
        res1 = subprocess.run(
            [str(ruff_bin), "check", "--fix", target_file],
            capture_output=True,
            text=True,
            check=False,
        )
        res2 = subprocess.run(
            [str(ruff_bin), "format", target_file],
            capture_output=True,
            text=True,
            check=False,
        )
        return (
            f"[Ruff Pre-Flight Complete]:\n{res1.stdout.strip()}\n"
            f"{res2.stdout.strip() or 'Code formatted.'}"
        )
    except Exception as e:
        return f"Ruff execution error: {e}"


def cache_prefix_audit(rules_path: str = "") -> dict[str, Any]:
    """Audits rule files for static KV-cache prefix compliance (< 1,000 tokens, zero timestamps)."""
    target = (
        Path(rules_path)
        if rules_path
        else (resolve_home_dir() / "config" / "AGENTS.md")
    )
    if not target.exists():
        return {"error": f"File {target} does not exist."}

    content = target.read_text(encoding="utf-8", errors="replace")
    tokens = count_tokens_safe(content)
    issues = []
    if re.search(r"\b(202\d-\d\d-\d\d|\d\d:\d\d:\d\d)\b", content):
        issues.append("Dynamic timestamp detected: breaks KV-cache alignment.")
    if re.search(r"\b(random|uuid|seed|datetime\.now)\b", content, re.IGNORECASE):
        issues.append("Dynamic random/time token detected.")
    if tokens >= 1000:
        issues.append(f"Rule footprint is {tokens} tokens (budget: < 1,000).")
    return {
        "status": "OPTIMAL" if not issues else "NEEDS_OPTIMIZATION",
        "tokens": tokens,
        "issues": issues,
        "cache_eligible": len(issues) == 0,
    }


def create_checkpoint(
    checkpoint_id: str = "",
    files: list[str] | None = None,
    cp_root: Path | None = None,
) -> str:
    """Snapshots modified files to checkpoints directory for instant zero-token rollback."""
    cid = checkpoint_id.strip() or f"cp_{int(time.time())}"
    cp_dir = _resolve_cp_dir(cp_root) / cid
    cp_dir.mkdir(parents=True, exist_ok=True)

    if not files:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            files = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
        except Exception:
            files = []

    if not files:
        return f"[Checkpoint {cid}]: No files specified or modified to checkpoint."

    snapshotted = []
    manifest = []
    for f in files:
        src = Path(f).resolve()
        if src.exists() and src.is_file():
            rel = os.path.relpath(src, os.getcwd()).replace("\\", "/")
            dest = cp_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            snapshotted.append(rel)
            manifest.append({"orig": str(src), "rel": rel})

    (cp_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return (
        f"[Checkpoint Created]: '{cid}'\nSnapshotted {len(snapshotted)} file(s):\n- "
        + "\n- ".join(snapshotted[:10])
    )


def restore_checkpoint(checkpoint_id: str, cp_root: Path | None = None) -> str:
    """Restores files from a checkpoint back to original locations."""
    cp_dir = _resolve_cp_dir(cp_root) / checkpoint_id.strip()
    manifest_file = cp_dir / "manifest.json"
    if not manifest_file.exists():
        return f"Error: Checkpoint '{checkpoint_id}' not found at {cp_dir}."
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        restored = []
        for item in manifest:
            src = cp_dir / item["rel"]
            orig = Path(item["orig"])
            if src.exists():
                orig.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, orig)
                restored.append(item["rel"])
        return (
            f"[Checkpoint Restored]: '{checkpoint_id}'\nRolled back {len(restored)} file(s):\n- "
            + "\n- ".join(restored)
        )
    except Exception as e:
        return f"Error restoring checkpoint: {e}"


def _to_toon_value(obj: Any, indent: int = 0) -> str:
    """Serializes JSON-compatible Python data into compact TOON format."""
    pad = "  " * indent
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            keys = list(obj[0].keys())
            if all(list(x.keys()) == keys for x in obj):
                header = f"[{len(obj)}]{{{','.join(keys)}}}:"
                rows = [
                    f"{pad}  "
                    + ",".join(str(x.get(k, "")).replace("\n", " ") for k in keys)
                    for x in obj
                ]
                return header + "\n" + "\n".join(rows)
        return "\n".join(f"{pad}- {_to_toon_value(x, indent + 1)}" for x in obj)
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                lines.append(f"{pad}{k}{_to_toon_value(v, indent + 1)}")
            elif isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(_to_toon_value(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {v}")
        return "\n".join(lines)
    return str(obj)


def to_toon(json_data: str) -> str:
    """Converts verbose JSON payloads into TOON (Token-Oriented Object Notation)."""
    try:
        parsed = json.loads(json_data)
    except json.JSONDecodeError as e:
        return f"TOON_ERROR: Invalid JSON ({e})"
    return _to_toon_value(parsed)


def cache_lookup_or_store(
    cache_key: str,
    payload: str = "",
    mode: str = "get",
    compress: bool = True,
    cache_override: Path | None = None,
) -> dict[str, Any]:
    """Persistent compressed content-hash tool output cache on disk (TOON + zlib)."""
    cache_path = _resolve_cache_path(cache_override)
    if mode == "clear":
        _TOOL_OUTPUT_CACHE.clear()
        if cache_path.exists():
            cache_path.unlink()
        return {"status": "CLEARED"}

    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _TOOL_OUTPUT_CACHE.update(data)
        except Exception:
            pass

    if mode == "stats":
        return {
            "entries": len(_TOOL_OUTPUT_CACHE),
            "disk_bytes": cache_path.stat().st_size if cache_path.exists() else 0,
            "cache_file": str(cache_path),
        }

    key_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:16]
    if mode == "set":
        data_to_store = payload
        if compress and payload.lstrip().startswith(("{", "[")):
            toon_str = to_toon(payload)
            if not toon_str.startswith("TOON_ERROR"):
                data_to_store = toon_str
        raw_bytes = data_to_store.encode("utf-8")
        if compress and len(raw_bytes) > 128:
            z_b64 = base64.b64encode(zlib.compress(raw_bytes, level=6)).decode("ascii")
            _TOOL_OUTPUT_CACHE[key_hash] = {"z": z_b64, "raw_len": len(raw_bytes)}
            stored_bytes = len(z_b64)
        else:
            _TOOL_OUTPUT_CACHE[key_hash] = {"v": data_to_store}
            stored_bytes = len(raw_bytes)
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            if len(_TOOL_OUTPUT_CACHE) > 500:
                keys = list(_TOOL_OUTPUT_CACHE.keys())[-500:]
                trimmed = {k: _TOOL_OUTPUT_CACHE[k] for k in keys}
                _TOOL_OUTPUT_CACHE.clear()
                _TOOL_OUTPUT_CACHE.update(trimmed)
            cache_path.write_text(
                json.dumps(_TOOL_OUTPUT_CACHE, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass
        return {
            "status": "STORED",
            "key_hash": key_hash,
            "raw_bytes": len(payload.encode("utf-8")),
            "stored_bytes": stored_bytes,
            "persisted_to_disk": cache_path.exists(),
        }

    if key_hash in _TOOL_OUTPUT_CACHE:
        entry = _TOOL_OUTPUT_CACHE[key_hash]
        if isinstance(entry, dict) and "z" in entry:
            val = zlib.decompress(base64.b64decode(entry["z"])).decode("utf-8")
        elif isinstance(entry, dict) and "v" in entry:
            val = entry["v"]
        else:
            val = str(entry)
        return {"status": "HIT", "key_hash": key_hash, "payload": val}

    return {"status": "MISS", "key_hash": key_hash}


def auto_setup_environment(force: bool = True) -> dict[str, Any]:
    """Runs the OS-appropriate installer cleanly in headless mode."""
    is_win = os.name == "nt"
    if is_win:
        script = _REPO_ROOT / "installer" / "setup.ps1"
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-NonInteractive",
        ]
        if force:
            cmd.append("-Force")
    else:
        script = _REPO_ROOT / "installer" / "setup.sh"
        cmd = ["bash", str(script), "--yes"]
        if force:
            cmd.append("--force")

    if not script.exists():
        return {"status": "ERROR", "error": f"Installer not found: {script}"}

    res = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
    return {
        "status": "OK" if res.returncode == 0 else "ERROR",
        "exit_code": res.returncode,
        "platform": "windows" if is_win else "posix",
        "output_tail": res.stdout.splitlines()[-20:],
        "stderr": res.stderr.strip()[:500] if res.stderr else "",
    }


def clear_chat_history(keep_latest: bool = True) -> dict[str, Any]:
    """Removes old Antigravity conversation & brain logs across antigravity/antigravity-ide."""
    home_base = resolve_home_dir()
    removed_items = 0
    freed_bytes = 0
    for variant in ("antigravity", "antigravity-ide"):
        agy_root = home_base / variant
        for sub in ("conversations", "brain"):
            target_dir = agy_root / sub
            if not target_dir.exists():
                continue
            entries = sorted(
                [p for p in target_dir.iterdir() if not p.name.startswith(".")],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            to_delete = entries[1:] if keep_latest and entries else entries
            for item in to_delete:
                try:
                    if item.is_dir():
                        size = sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )
                        shutil.rmtree(item)
                    else:
                        size = item.stat().st_size
                        item.unlink()
                    freed_bytes += size
                    removed_items += 1
                except Exception:
                    continue

    return {
        "status": "OK",
        "removed_items": removed_items,
        "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        "kept_latest": keep_latest,
    }


def run_health_doctor() -> dict[str, Any]:
    """Runs `scripts/setup/doctor.ps1` or `doctor.sh` and returns verification summary."""
    is_win = os.name == "nt"
    script = (
        _REPO_ROOT / "scripts" / "setup" / ("doctor.ps1" if is_win else "doctor.sh")
    )
    if not script.exists():
        return {"status": "ERROR", "error": f"Doctor script not found: {script}"}

    cmd = (
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
        if is_win
        else ["bash", str(script)]
    )
    res = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
    return {
        "status": "OK" if res.returncode == 0 else "WARN",
        "exit_code": res.returncode,
        "summary": res.stdout.splitlines()[-15:],
    }
