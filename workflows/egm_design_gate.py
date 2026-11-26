"""
Native Antigravity Workflow: Elephant-Goldfish Model (EGM) Design Gate.
Separates deep-context architectural drafting (Elephant) from fresh-context
cold adversarial review (Goldfish) before any implementation begins.
"""

from pathlib import Path
from typing import Any


def build_goldfish_review_brief(
    design_draft_path: str, referenced_files: list[str] | None = None
) -> dict[str, Any]:
    """
    Constructs a zero-memory handoff payload for the Goldfish reviewer subagent.
    Only passes the design draft and explicit file paths—never prior chat history.
    """
    draft = Path(design_draft_path)
    if not draft.exists():
        return {
            "status": "ERROR",
            "error": f"Design draft not found: {design_draft_path}",
        }

    files = referenced_files or []
    return {
        "status": "READY",
        "protocol": "Google-Elephant-Goldfish-Model-v1",
        "reviewer_agent": "goldfish-reviewer",
        "zero_memory_enforced": True,
        "inputs": {
            "design_draft": str(draft),
            "referenced_files": files,
        },
        "gate_criteria": [
            "Zero unstated assumptions",
            "Explicit failure modes and recovery paths",
            "Deterministic verification plan defined",
        ],
    }


if __name__ == "__main__":
    print("EGM Design Gate workflow module loaded cleanly.")
