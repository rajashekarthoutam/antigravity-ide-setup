---
name: infinite-context-loop
description: Cuts per-turn tokens by 90%+ in continuous, long-running, or bloated chat loops using the Infinite-Horizon Context Engine (`infinite_context_compact`, SQLite FTS5 virtualization, Observation Masking, CLI compression, and epoch-aligned KV-cache preservation). Use when agent loops run many turns, inspect large logs/files, or experience context bloat.
---

# Infinite-Horizon 90%+ Token Reduction Loop

Keep multi-turn agent loops fast, accurate, and O(1)-bounded without breaking prompt KV-cache hits or losing diagnostic state.

## Architecture (5 Zero-LLM Layers)

1. **Preventative Output Virtualization (`mode="virtualize"` / CLI `--exec`)**:
   - Wrap verbose shell commands with `python mcp/infinite_context.py --exec "<cmd>"` (or `--pipe`) so stdout/stderr > `1,200` chars or `35` lines is redacted and stored in local WAL SQLite FTS5 (`ctx://<hash12>`), returning only a compact error/tail digest and preserving the exit code.
   - Inject only the compressed digest (`cli_compress` + `elide_output`) and `ctx://` handle into chat context so raw 10KB+ logs never enter transcript history.
2. **Deterministic CLI Noise Filter (`mode="cli_compress"`)**:
   - Strip ANSI escape codes, `\r` spinner frames, package download progress, and passing-test noise while unconditionally preserving stack traces, failing assertions, summary counts, and unified diffs.
3. **Epoch-Aligned Compaction (`mode="compact"`)**:
   - Stay append-only **within** an epoch (`turns_since_epoch < epoch_size and delta_tokens <= token_budget`) so stable prefix bytes preserve 85–95% KV-cache reuse.
   - Compact **at epoch boundaries** via: duplicate read elimination, stale write superseding, purging oversized args from old errored calls (keeping root cause), JetBrains Observation Masking outside `window=4`, and folding old prose into a bounded **Anchored State Capsule** (`<= 450` tokens).
4. **On-Demand BM25 FTS5 Recall (`mode="search"` / `mode="fetch"`)**:
   - Query archived details using `search_virtual_context(query)` and fetch exact bounded windows (`<= 150` lines) via `fetch_virtual_slice(handle, start_line, end_line)`.

## Verification Steps

Run deterministic validation and inspect `raw_reduction_pct`, `cumulative_reduction_pct`, and `estimated_kv_cache_hit_pct`:

```bash
python -m unittest discover -s tests -v
```

Confirm:
- `raw_reduction_pct >= 90.0` across bloated multi-turn loops
- All active errors, file targets, and recent `window` turns remain accessible
- Exit code `0` on full test suite and linter (`ruff check mcp --config config/ruff.toml`)
