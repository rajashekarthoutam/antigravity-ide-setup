# Antigravity Native Workflows

Native Antigravity Python workflows orchestrated via `run_workflow` (or imported inside sandbox scripts).

## 1. `code_review.py` (Multi-Dimensional Adversarial Review)

1. Dispatches specialized reviewers (`code-reviewer`, `<language>-reviewer`, `security-reviewer`) concurrently via `parallel()`.
2. Deduplicates findings across dimensions while keeping strictest severity.
3. Routes `CRITICAL`/`HIGH` findings to an adversarial `verifier` skeptic (`REFUTE_MIN_CONFIDENCE = 0.8`).
4. Fails closed (`CHANGES_REQUESTED`) on unrefuted blockers or failed dimensions.

## 2. `autonomous_repair.py` (Autonomous TDD Bug Repair)

1. Runs failing command in sandbox & triages root cause via `system1_triage` (`autonomous-debugger`).
2. Formulates hypotheses & evaluates caller blast radius via `code_graph_impact_probe` (`architect`).
3. Snapshots state (`create_checkpoint`) and applies minimal repair (`swe-bench-runner`).
4. Runs full test suite + linter (`verifier`).

## 3. `egm_design_gate.py` (Google Elephant-Goldfish Model)

Builds zero-memory handoff briefs (`build_goldfish_review_brief`) so `goldfish-reviewer` audits `design_draft.md` cold before code edits begin.

## 4. `token_saving_pipeline.py` (Infinite-Horizon 90%+ Token Pipeline)

Plans minimal-token file/dataset/log inspection routing to `infinite_context_compact`, `filter_and_loop_data`, `get_file_outline`, `cli_compress`, `to_toon`, and `compact_conversation_loop`.
