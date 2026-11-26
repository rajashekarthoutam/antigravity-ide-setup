# AGENTS.md — God-Mode Master Contract

Static KV-cache-locked prefix (zero volatile dates/UUIDs; strictly `< 600` tokens).

## 1. Safety & EGM Gate
1. **EGM**: For architectural changes, draft `concepts_brief.md` + `design_draft.md` and run `goldfish-reviewer` before editing code.
2. **Read-Before-Write**: Inspect target symbols/callers/tests before edits.
3. **Deterministic Verification**: Verify via linter, parser, and tests (`exit 0`); never retry failed commands byte-identically.

## 2. 90%+ Token Reduction & Output Discipline
1. **Preventative CLI Compression**: Wrap noisy shell runs (`tests`, `builds`, `diffs`, `logs > 35 lines`) with `python mcp/infinite_context.py --exec "<cmd>"` (or `--pipe`) so full output goes to FTS5 (`ctx://<hash>`) with only compressed diagnostics in chat.
2. **AST & Targeted Reads**: Call `pagerank_repo_map`, `get_file_outline`, `get_symbol`, or `diff_re_read` first; bound direct reads (`<= 150` lines).
3. **Code Mode (`<= 10` schemas)**: Use `discover_mcp_tools(query)` + `mcp/tools_api/` inside `execute_code_sandbox()`; filter large datasets via `filter_and_loop_data()`.
4. **Epoch & Cache Lock**: Keep context append-only within epochs (`infinite_context_compact`); keep replies concise (`2–5` lines + links/diffs unless deep detail is requested) to minimize output-token quota burn.
5. **Memory & Skills**: Recall state via `search_memories()` / `search_virtual_context()` (`ctx://`); load domain skills on demand via `search_skills()` and validate via `evaluate_skill()`.
6. **0-Token Triage & Checkpoints**: Route stack traces through `system1_triage()` / `cli_compress()`; snapshot risky edits with `create_checkpoint()`.
