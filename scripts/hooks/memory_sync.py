"""
Memory Sync & Continuous Cross-Session Telemetry
Synchronizes persistent memory across ~/.gemini/config/memory.json and .agents/memory/ markdown files.
Allows instant search, addition, and automatic ADR syncing without conversational token bloat.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _resolve_memory_file(for_write: bool = False) -> Path:
    base = os.environ.get("GOD_MODE_HOME", "").strip()
    gemini_dir = Path(base).expanduser() if base else (Path.home() / ".gemini")
    primary = gemini_dir / "config" / "memory.json"
    legacy = gemini_dir / "config" / "god_mode_mem0.json"
    if for_write or primary.exists():
        return primary
    return legacy if legacy.exists() else primary


MEMORY_FILE = _resolve_memory_file()
WORKSPACE_MEMORY_DIR = (
    Path(__file__).resolve().parent.parent.parent / ".agents" / "memory"
)


def load_memories() -> list[dict[str, Any]]:
    target = (
        MEMORY_FILE if MEMORY_FILE.exists() else _resolve_memory_file(for_write=False)
    )
    if target.exists():
        try:
            with open(target, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                return data.get("memories", [])
        except Exception:
            return []
    return []


def save_memories(memories: list[dict[str, Any]]) -> None:
    target = _resolve_memory_file(for_write=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump({"memories": memories}, f, indent=2, ensure_ascii=False)


def add_memory_entry(
    content: str, metadata: str = "general", user_id: str = "default"
) -> dict[str, Any]:
    memories = load_memories()
    next_id = (
        max((int(m["id"]) for m in memories if isinstance(m.get("id"), int)), default=0)
        + 1
    )
    entry = {
        "id": next_id,
        "content": content,
        "user_id": user_id,
        "metadata": metadata,
    }
    memories.append(entry)
    save_memories(memories)
    return entry


def search_memories(query: str) -> list[dict[str, Any]]:
    memories = load_memories()
    terms = [t.lower() for t in query.split() if len(t) > 2]
    if not terms:
        return memories[-5:]

    scored = []
    for m in memories:
        c = (m.get("content", "") + " " + m.get("metadata", "")).lower()
        score = sum(1 for t in terms if t in c)
        if score > 0:
            scored.append((score, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:8]]


def sync_to_markdown() -> str:
    """Syncs structured memories to .agents/memory/ files for zero-token local context loading."""
    memories = load_memories()
    if not memories:
        return "No memories to sync."

    WORKSPACE_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    decisions_file = WORKSPACE_MEMORY_DIR / "decisions.md"
    anti_patterns_file = WORKSPACE_MEMORY_DIR / "anti_patterns.md"

    # Read existing content to avoid duplicate appends
    existing_decisions = (
        decisions_file.read_text(encoding="utf-8") if decisions_file.exists() else ""
    )
    existing_anti = (
        anti_patterns_file.read_text(encoding="utf-8")
        if anti_patterns_file.exists()
        else ""
    )

    decisions_added = 0
    anti_added = 0

    new_decisions = []
    new_anti = []

    for m in memories:
        content = m.get("content", "")
        meta = m.get("metadata", "").lower()
        if (
            meta in ("architecture", "checkpoint", "token_optimization", "adr")
            and content[:40] not in existing_decisions
        ):
            new_decisions.append(f"- **[ID-{m['id']} {meta.upper()}]**: {content}\n")
            decisions_added += 1
        elif (
            meta in ("reflexion", "trap", "bug", "anti_pattern")
            and content[:40] not in existing_anti
        ):
            new_anti.append(f"- **[ID-{m['id']} {meta.upper()}]**: {content}\n")
            anti_added += 1

    if new_decisions:
        with open(decisions_file, "a", encoding="utf-8") as f:
            f.write("\n## Continuous Memory Sync\n" + "".join(new_decisions))

    if new_anti:
        with open(anti_patterns_file, "a", encoding="utf-8") as f:
            f.write("\n## Continuous Memory Sync\n" + "".join(new_anti))

    return f"Synced continuous memories: +{decisions_added} to decisions.md, +{anti_added} to anti_patterns.md."


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Continuous Memory Sync & Query"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new persistent memory")
    add_parser.add_argument("content", help="Memory content to persist")
    add_parser.add_argument(
        "--meta",
        default="general",
        help="Category tag (architecture, checkpoint, etc.)",
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search persistent memories")
    search_parser.add_argument("query", help="Keywords to query")

    # List command
    subparsers.add_parser("list", help="List recent memories")

    # Sync command
    subparsers.add_parser("sync", help="Sync memories into .agents/memory/ files")

    args = parser.parse_args()

    if args.subcommand == "add":
        entry = add_memory_entry(args.content, metadata=args.meta)
        print(
            f"[MEMORY SAVED] ID {entry['id']} [{entry['metadata']}]: {entry['content']}"
        )
    elif args.subcommand == "search":
        results = search_memories(args.query)
        print(f"--- Search Results for '{args.query}' ({len(results)} matches) ---")
        for m in results:
            print(
                f"[{m.get('metadata', 'note').upper()}] (ID: {m['id']}) {m['content']}"
            )
    elif args.subcommand == "list":
        memories = load_memories()
        print(f"--- Total Persistent Memories: {len(memories)} ---")
        for m in memories[-10:]:
            print(
                f"[{m.get('metadata', 'note').upper()}] (ID: {m['id']}) {m['content']}"
            )
    elif args.subcommand == "sync":
        print(sync_to_markdown())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
