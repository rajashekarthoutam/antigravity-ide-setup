# Antigravity Ecosystem Architecture

```mermaid
flowchart TD
    IDE["Google Antigravity IDE / VS Code / Cursor / Claude"] --> Prefix["Static Prefix (AGENTS.md < 1,000 tokens)"]
    IDE --> MCP["FastMCP Server (mcp/server.py — 9 Upfront Schemas)"]
    IDE --> Hooks["Gravitas Runtime Hooks (scripts/hooks/)"]

    MCP --> Infinite["Infinite-Horizon Engine (mcp/infinite_context.py)"]
    Infinite --> Vault["WAL SQLite FTS5 Vault (ctx:// Handles + Secret Redaction)"]
    Infinite --> Capsule["Epoch Compactor + Observation Masking + Anchored Capsule"]

    MCP --> CodeMode["Tools-as-Files (mcp/tools_api/ & 26 mcp/schemas/)"]
    MCP --> Nav["Code Nav Engine (mcp/code_nav.py: PageRank AST, Symbols, Impact)"]
    MCP --> Sec["Security & Skill Grader (mcp/security_eval.py: SkillSpector, Model Armor)"]
    MCP --> Mem["Persistent Memory (memory.json) & Tool Cache (TOON + zlib)"]

    Hooks --> Policy["Quote-Aware Shell Scanner & Workspace Scope Guard"]
    Hooks --> Laya["Convai Laya System-1 Triage (< 40ms CPU)"]
    Hooks --> CI["Automated CI (tests/test_suite.py + ruff + bash -n)"]
```

## Components

- **Control Plane (`AGENTS.md` + `config/`)**: Static KV-cache-friendly contract (`< 1,000` tokens), `hooks.json`, clean seed `memory.json`, `repomix.json`, `ruff.toml`, `runtime.json`, `system_prompt.md`.
- **FastMCP Modular Runtime (`mcp/`)**:
  - `server.py`: Upfront `FastMCP("god-mode")` exposing `9` `@app.tool()` schemas (`<= 10` limit) and re-exporting all helper APIs.
  - `infinite_context.py`, `context_vault.py`, `text_filters.py`: Preventative FTS5 `ContextVirtualizer`, `cli_compress`, secret redaction, DCP transformations, Observation Masking, and Epoch Compaction.
  - `code_nav.py`: Pure-Python AST + `ast-grep` outline/symbol extraction, PageRank repo map, two-pass caller/importer impact analysis, diff-only re-reads.
  - `security_eval.py`: SkillSpector scanner (with method-free `eval`/`exec` and emoji-ZWJ precision), Model Armor secret redactor, A2A cards, and 100-point skill evaluator.
  - `ops_helpers.py`: Token audit, TOON serializer, compressed output cache, checkpoints, and doctor runners.
  - `tools_api/` & `schemas/`: 6 on-demand Python stub modules matching all 26 JSON tool schemas.
- **Customizations (`agents/`, `skills/`, `rules/`, `workflows/`)**: 65 agents, 231 skills, 11 rule directories, and 4 multi-agent/token workflows.
- **Setup & Installers (`installer/`, `scripts/`)**: Cross-platform setup/uninstaller, MCP registrar, chat cleaner, backup archiver, and health doctor.
