# God-Mode 90%+ Token Economy Rules

Apply these 6 layered zero-waste optimizations on every engineering session:

1. **KV-Cache Prefix Locking & Epoch Alignment (85–95% Prefix Reuse)**
   - Keep `AGENTS.md` and system prompts strictly static and `< 1,000` tokens (no dates, UUIDs, or volatile counters).
   - Keep conversation appends append-only within epochs (`epoch_size=12`); compact only at epoch boundaries via `infinite_context_compact`.

2. **Infinite-Horizon Output Virtualization (`ContextVirtualizer` + `cli_compress`)**
   - Virtualize any output `> 1,200` chars or `35` lines into SQLite FTS5 (`ctx://<hash12>`), redacting secrets automatically.
   - Inject only compressed error/diff digests into chat; use `search` / `fetch` on demand (`<= 150` lines).

3. **Tools-as-Files (`mcp/tools_api/`)**
   - Keep `mcp/server.py` upfront `@app.tool()` count `<= 10`; discover and import stubs via `discover_mcp_tools(query)` inside `execute_code_sandbox()`.

4. **In-Code Data Filtering & Loops (`filter_and_loop_data` / `execute_code_sandbox`)**
   - Filter logs, large JSON/CSV datasets, and multi-file searches locally in Python, emitting only bounded final matches (`<= 25` rows).

5. **AST Skeleton Folding & Diff-Only Re-Reads**
   - Use `get_file_outline()` and `get_symbol()` before reading whole files.
   - Use `diff_re_read()` on modified files and `code_graph_impact_probe()` before refactors.

6. **TOON Serialization & Content-Hash Caching**
   - Serialize uniform arrays via `to_toon()` (30–60% fewer tokens) and cache repeated deterministic results in `cache_lookup_or_store()`.
