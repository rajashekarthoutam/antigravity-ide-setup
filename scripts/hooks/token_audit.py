"""
Token Audit & Telemetry Tracker for Antigravity IDE
Computes exact token consumption per turn, per chat session, and across all workspace chats.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import tiktoken
except Exception:
    tiktoken = None  # type: ignore[assignment]

_ENC = None
_ENC_UNAVAILABLE = False


def _default_brain_dir() -> Path:
    base = os.environ.get("GOD_MODE_HOME", "").strip()
    gemini_root = Path(base).expanduser() if base else (Path.home() / ".gemini")
    for variant in ("antigravity", "antigravity-ide"):
        candidate = gemini_root / variant / "brain"
        if candidate.exists():
            return candidate
    return gemini_root / "antigravity" / "brain"


DEFAULT_BRAIN_DIR = _default_brain_dir()


def count_tokens_in_text(text: str) -> int:
    if not text:
        return 0
    global _ENC, _ENC_UNAVAILABLE
    if not _ENC_UNAVAILABLE and _ENC is None and tiktoken is not None:
        try:
            _ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENC_UNAVAILABLE = True
    if _ENC is not None:
        return len(_ENC.encode(text, disallowed_special=()))
    return max(1, (len(text) + 3) // 4)


def parse_transcript(transcript_file: Path) -> dict[str, Any]:
    total_tokens = 0
    steps_count = 0
    last_turn_tokens = 0

    if not transcript_file.exists():
        return {
            "total_tokens": 0,
            "steps": 0,
            "last_turn_tokens": 0,
        }

    lines = []
    with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                lines.append(line_str)

    steps_count = len(lines)
    step_tokens: list[int] = []

    for line in lines:
        try:
            data = json.loads(line)
            text = ""
            if "content" in data and isinstance(data["content"], str):
                text += data["content"] + "\n"
            if "thinking" in data and isinstance(data["thinking"], str):
                text += data["thinking"] + "\n"
            if "tool_calls" in data:
                text += json.dumps(data["tool_calls"]) + "\n"
            toks = count_tokens_in_text(text)
            step_tokens.append(toks)
            total_tokens += toks
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    # Last turn tokens = sum of tokens in the latest model step and preceding user input
    if step_tokens:
        last_turn_tokens = (
            sum(step_tokens[-2:]) if len(step_tokens) >= 2 else step_tokens[-1]
        )

    return {
        "total_tokens": total_tokens,
        "steps": steps_count,
        "last_turn_tokens": last_turn_tokens,
    }


def get_all_sessions(brain_dir: Path = DEFAULT_BRAIN_DIR) -> dict[str, Any]:
    if not brain_dir.exists():
        return {"sessions": {}, "total_tokens": 0, "active_session_id": ""}

    sessions = {}
    total_workspace_tokens = 0
    active_session_id = ""
    latest_mtime = 0.0

    for item in brain_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            tpath = item / ".system_generated" / "logs" / "transcript.jsonl"
            if tpath.exists():
                mtime = tpath.stat().st_mtime
                data = parse_transcript(tpath)
                data["last_modified"] = mtime
                sessions[item.name] = data
                total_workspace_tokens += data["total_tokens"]
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    active_session_id = item.name

    return {
        "sessions": sessions,
        "total_tokens": total_workspace_tokens,
        "active_session_id": active_session_id,
    }


def format_summary() -> str:
    audit = get_all_sessions()
    active_id = audit["active_session_id"]
    active_data = audit["sessions"].get(
        active_id, {"total_tokens": 0, "last_turn_tokens": 0, "steps": 0}
    )

    lines = [
        "==================================================",
        "  ANTIGRAVITY IDE TOKEN & USAGE TELEMETRY",
        "==================================================",
        f"Active Chat ID   : {active_id}",
        f"Turn Consumption : ~{active_data['last_turn_tokens']:,} tokens",
        f"Chat Session Total: {active_data['total_tokens']:,} tokens ({active_data['steps']} steps)",
        f"Workspace Total  : {audit['total_tokens']:,} tokens across {len(audit['sessions'])} sessions",
        "--------------------------------------------------",
        "CONVERSATION BREAKDOWN:",
    ]
    for cid, sdata in audit["sessions"].items():
        tag = " (ACTIVE)" if cid == active_id else ""
        lines.append(
            f" - {cid}{tag}: {sdata['total_tokens']:,} tokens [{sdata['steps']} steps]"
        )

    lines.extend(
        [
            "--------------------------------------------------",
            "ANTIGRAVITY USAGE & LIMITS PANEL:",
            " - Slash Commands: Type '/usage' or '/quota' in chat for live capacity.",
            " - AI Credits    : Type '/credits' to view balance and monthly overage.",
            " - Statusline    : Type '/statusline' to show live credits in bottom bar.",
            " - Refresh Window: Rolling 5-Hour limit + weekly cap (Pro/Ultra).",
            "==================================================",
        ]
    )
    return "\n".join(lines)


def checkpoint_session(summary: str | None = None) -> str:
    audit = get_all_sessions()
    active_id = audit["active_session_id"]
    active_data = audit["sessions"].get(active_id)
    if not active_data:
        return "No active session found to checkpoint."

    base = os.environ.get("GOD_MODE_HOME", "").strip()
    gemini_root = Path(base).expanduser() if base else (Path.home() / ".gemini")
    mem_file = gemini_root / "config" / "memory.json"
    memories = []
    if mem_file.exists():
        try:
            with open(mem_file, "r", encoding="utf-8-sig") as f:
                memories = json.load(f).get("memories", [])
        except Exception:
            memories = []

    content = summary or (
        f"Session checkpoint ({active_id[:8]}): Completed {active_data['steps']} steps, "
        f"accumulated {active_data['total_tokens']:,} tokens. Context flushed to memory."
    )

    next_id = (
        max((int(m["id"]) for m in memories if isinstance(m.get("id"), int)), default=0)
        + 1
    )
    entry = {
        "id": next_id,
        "content": content,
        "user_id": "default",
        "metadata": "checkpoint",
    }
    memories.append(entry)

    mem_file.parent.mkdir(parents=True, exist_ok=True)
    with open(mem_file, "w", encoding="utf-8") as f:
        json.dump({"memories": memories}, f, indent=2, ensure_ascii=False)

    return (
        f"[CHECKPOINT PERSISTED] ID: {entry['id']} | Tokens shedding potential: {active_data['total_tokens']:,}\n"
        f"Action: Press Ctrl+Shift+L (New Chat) or run '/clear'. Agent will retrieve state via search_memories."
    )


def reset_workspace(brain_dir: Path = DEFAULT_BRAIN_DIR) -> str:
    import shutil

    if not brain_dir.exists():
        return "Brain directory not found."
    archive_dir = brain_dir / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    audit = get_all_sessions(brain_dir)
    active_id = audit["active_session_id"]
    moved = 0
    tokens_freed = 0
    for item in list(brain_dir.iterdir()):
        if (
            item.is_dir()
            and not item.name.startswith(".")
            and item.name != "tempmediaStorage"
            and item.name != active_id
        ):
            try:
                tokens_freed += (
                    audit["sessions"].get(item.name, {}).get("total_tokens", 0)
                )
                dest = archive_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
                shutil.move(str(item), str(dest))
                moved += 1
            except Exception:
                continue
    return f"Archived {moved} historical sessions ({tokens_freed:,} tokens pruned to .archive). Workspace reset."


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--badge":
            audit = get_all_sessions()
            active_id = audit["active_session_id"]
            active_data = audit["sessions"].get(
                active_id, {"total_tokens": 0, "last_turn_tokens": 0}
            )
            print(
                f"[Tokens: ~Turn: {active_data['last_turn_tokens']:,} | Session: {active_data['total_tokens']:,} | Workspace: {audit['total_tokens']:,} | Limits: '/usage']"
            )
        elif arg == "--checkpoint":
            custom_summary = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
            print(checkpoint_session(custom_summary))
        elif arg in ("--reset", "reset"):
            print(reset_workspace())
        else:
            print(format_summary())
    else:
        print(format_summary())
