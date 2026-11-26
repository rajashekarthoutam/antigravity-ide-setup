---
name: elephant-goldfish-model
description: "Google's Elephant-Goldfish Model (EGM) for spec-driven architecture and adversarial design review. Use when designing complex hardware, firmware, or software systems before writing code: the Elephant (deep-context session) drafts concepts_brief.md and design_draft.md, then fresh-context Goldfish subagents review cold with zero prior memory to catch blind spots and edge cases."
---

# Elephant-Goldfish Model (EGM)

Inspired by Google Distinguished Engineer Dave Rensin's **Elephant-Goldfish Model**, separate deep-context architectural synthesis from zero-memory adversarial review so baked-in assumptions never leak into production code.

## Roles

1. **The Elephant (Deep-Context Architect)**
   - Holds full project history, user requirements, hardware/firmware constraints, and `search_memories` context.
   - Collaborates with the user through `/egm-brainstorm` and `/egm-draft` to produce:
     - `concepts_brief.md` (problem statement, constraints, non-goals)
     - `design_draft.md` (architecture, interfaces, failure modes, verification plan)

2. **The Goldfish (Fresh-Context Adversarial Reviewer)**
   - Invoked via `invoke_subagent` with **zero prior conversation history** (`goldfish-reviewer`).
   - Receives **only** `design_draft.md` and the exact referenced source files—simulating a new engineer reading the spec cold.
   - Aggressively hunts for unstated assumptions, timing/CDC hazards, race conditions, missing error paths, and security gaps.

## Execution Workflow

1. **Brainstorm (Elephant)**: Clarify requirements and constraints; record key decisions in `concepts_brief.md`.
2. **Draft (Elephant)**: Write `design_draft.md` with explicit interfaces, invariants, and verification criteria.
3. **Cold Review (Goldfish)**: Spawn `goldfish-reviewer` with zero shared conversation context to audit `design_draft.md`.
4. **Converge & Gate**: Address every Goldfish finding in `design_draft.md` and obtain user approval before editing code.
5. **Verify**: Run deterministic tests (`python tests/test_ide_setup.py` or project test suite) after implementation.
