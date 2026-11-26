---
name: code-execution-mcp
description: "Anthropic 98.7% token reduction pattern: store MCP tools as files, load instructions only when needed, filter huge datasets/logs in code before sending to the model, and use loops in sandboxed Python instead of repeated model calls. Use when tasks involve large JSON/CSV/log datasets, multi-step tool loops, or high MCP schema overhead."
---

# Code Execution with MCP (98.7% Token Reduction)

Based on Anthropic's *Code Execution with MCP* architecture, replace multi-hop LLM tool loops and upfront schema dumping with programmatic Python execution.

## Core Principles

1. **Store MCP Tools as Files (`mcp/tools_api/`)**
   - Never dump all 30+ MCP tool schemas into context upfront.
   - Call `discover_mcp_tools(query="<topic>")` to locate only the relevant module stub (`navigation.py`, `sandbox_filter.py`, `memory_graph.py`, `security_eval.py`).
   - Import only the needed functions inside `execute_code_sandbox()`.

2. **Load Instructions Only When Needed**
   - Use `search_skills(query="<topic>")` for on-demand skill discovery.
   - Read only the matched `SKILL.md` (and `references/` only when required).

3. **Filter Huge Databases & Logs Before Sending to the Model**
   - Never read multi-megabyte JSON, CSV, SQLite, or build logs directly into chat.
   - Call `filter_and_loop_data(data_source, keyword_or_regex, limit=25)` or run a Python filter script in `execute_code_sandbox()` so only matching summaries enter context.

4. **Use Code Loops Instead of Repeated Model Calls**
   - Batch repetitive file audits, AST checks, or multi-target queries inside a single Python loop in `execute_code_sandbox()`.
   - Emit only a compact JSON summary via `print()`.

## Verification

1. Confirm `discover_mcp_tools("sandbox")` resolves `mcp/tools_api/sandbox_filter.py`.
2. Confirm `filter_and_loop_data()` returns `returned_count <= limit` and concise matches instead of raw file dumps.
