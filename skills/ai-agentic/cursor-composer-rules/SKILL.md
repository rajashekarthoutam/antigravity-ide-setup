---
name: cursor-composer-rules
description: Fast multi-file editing rules, diff-first invariants, and semantic indexing specs for Cursor and VS Code AI extensions.
---

# Cursor & VS Code AI Extension Invariant Rules

Optimizes autonomous coding agents operating within Cursor (Composer, Agent Mode) and VS Code (Roo-Code, Cline, GitHub Copilot).

---

## Core Invariants

1. **Diff-First Mutation**:
   Never rewrite entire 500+ line files when modifying a function or class. Emit surgical unified diffs or targeted symbol replacements to preserve editor undo stacks and reduce token load by 90%+.

2. **Semantic Indexing Before Searching**:
   Leverage `.cursorrules` / `.vscode/` settings with high-efficiency indexing:
   - Exclude noisy build artifacts (`dist/`, `build/`, `.ruff_cache/`, `node_modules/`).
   - Query indexed symbols (`xerj` / `get_symbol`) instead of brute-force grep across thousands of files.

3. **Multi-File Atomicity**:
   When refactoring across multiple files:
   - Create a pre-refactoring snapshot (`create_checkpoint`).
   - Verify every file modification compiles cleanly before moving to the next.
   - If tests fail, roll back cleanly (`restore_checkpoint`) rather than chaining speculative fixes.

4. **Terminal Silence Invariant**:
   Never let terminal outputs flood chat context. Pipe heavy test outputs or compiler traces through local System-1 triage (`system1_triage`) to keep the editor interface responsive.
