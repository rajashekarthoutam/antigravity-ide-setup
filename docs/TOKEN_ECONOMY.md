# 90%+ Infinite-Horizon Token Economy Specification

Standard single-turn AST tools reduce individual file reads, yet continuous multi-turn sessions still suffer **quadratic $O(T^2)$ input token growth** as logs, duplicate tool calls, stale file dumps, and verbose outputs accumulate.

This suite eliminates that explosion via **six orthogonal zero-LLM layers** orchestrated across `mcp/infinite_context.py`, `mcp/code_nav.py`, and `mcp/server.py`:

## Layer 1: Static KV-Cache Prefix & Epoch Alignment
- `AGENTS.md` is strictly static and `< 600` tokens (verified well below `1,000` limit) with zero volatile timestamps, dates, or random nonces (`cache_prefix_audit`).
- Within an epoch (`turns_since_epoch < epoch_size and delta_tokens <= token_budget`), `compact_conversation_loop` operates append-only on `[prefix_end:]`, leaving earlier bytes identical for maximum provider KV-cache reuse.

## Layer 2: Preventative SQLite FTS5 Virtualization (`ContextVirtualizer` + CLI `--exec` / `--pipe`)
- Outputs exceeding `1,200` chars or `35` lines (via `infinite_context_compact` or `python mcp/infinite_context.py --exec "<cmd>"` / `--pipe`) are redacted (`redact_secrets`) and persisted into short-lived WAL SQLite FTS5 (`context_vault.db`, bounded FIFO `<= 2,000` rows) under content-addressed handles (`ctx://<sha256[:12]>`).
- Only the `cli_compress` digest enters prompt context; historical lines remain searchable on demand via BM25 (`search_virtual_context`) and readable in bounded `<= 150`-line slices (`fetch_virtual_slice`).

## Layer 3: Deterministic CPU CLI Noise Filter (`cli_compress` & `system1_triage`)
- Strips ANSI escape codes, `\r` spinner frames, package download bars, and repetitive passing dot/progress noise locally on CPU.
- **Strict Preservation Contract**: Unconditionally keeps stack traces, assertion errors, summary pass/fail counts, exit codes, and unified diff headers (`---`, `+++`, `@@`).

## Layer 4: DCP Deduplication, Observation Masking & Anchored Capsule
At epoch compaction boundaries:
1. Drops earlier duplicate `(tool, args)` read/search observations.
2. Supersedes stale file read/write observations targeting modified paths.
3. Purges oversized args (`CodeContent`, large `content`) from errored calls older than 2 turns while retaining distilled root cause (`extract_error_tail`).
4. Masks tool outputs outside `window=4` as 1-line references (`[masked:<tool>(<target>) -> <tokens>tok, handle=ctx://...]`).
5. Folds pre-window narrative turns into a bounded **Anchored State Capsule** (`<= 450` tokens: `intent`, `files`, `decisions`, `errors`, `handles`, `next`).

## Layer 5: Code-Mode Schemas (`<= 10` Upfront) & In-Code Filtering
- `mcp/server.py` exposes only **9** upfront `@app.tool()` schemas.
- All 26 capabilities are importable on demand inside `execute_code_sandbox()` via `discover_mcp_tools()` -> `from tools_api.<module> import ...`.
- Large JSON/CSV/log files are filtered inside Python via `filter_and_loop_data()` (`<= 25` matches returned).

## Layer 6: AST Slices, Diff Re-Reads, TOON & Content-Hash Cache
- Targeted reading via `pagerank_repo_map`, `get_file_outline`, `get_symbol`, `diff_re_read`, and `code_graph_impact_probe`.
- Tabular JSON serialized cleanly into compact TOON (`to_toon`) and zlib-compressed in `cache_lookup_or_store`.

## Metric Transparency
`compact_conversation_loop` reports **raw physical token compression** (`raw_tokens_before`, `raw_tokens_after`, `raw_reduction_pct`, `cumulative_reduction_pct`) separately from advisory billing metrics (`estimated_kv_cache_hit_pct`, `advisory_effective_cost_tokens`).
