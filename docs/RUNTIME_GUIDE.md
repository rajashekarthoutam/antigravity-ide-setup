# God-Mode Antigravity Runtime Guide

Master operational manual for `antigravity-ide-setup`.

---

## 1. Repository Layout & Global Install Targets

Running `.\installer\setup.ps1` (Windows) or `./installer/setup.sh` (Linux/macOS) deploys to `~/.gemini/config/`:

| Component | Source in Repo | Deployed Location | Purpose |
|---|---|---|---|
| Master Contract | `AGENTS.md` | `~/.gemini/config/AGENTS.md` | Static `<1,000`-token rule prefix |
| FastMCP Engine | `mcp/` (`server.py`, `infinite_context.py`, `code_nav.py`, `security_eval.py`, `tools_api/`, `schemas/`) | `~/.gemini/config/mcp/` | 9 upfront tools + 26 schemas + Infinite-Horizon Engine |
| Tool Schemas | `mcp/schemas/*.json` | `~/.gemini/antigravity*/mcp/god-mode/` | Antigravity IDE & CLI schema discovery |
| Config Templates | `config/` (`hooks.json`, `memory.json`, `ruff.toml`, `runtime.json`, `system_prompt.md`, `repomix.json`) | `~/.gemini/config/` | Clean runtime defaults |
| Runtime Hooks | `scripts/hooks/*.py` | `~/.gemini/config/scripts/hooks/` | Gravitas enforcement, Laya triage, token audit |
| Setup CLI | `scripts/setup/` (`doctor`, `verify_skill`, `register_mcp`, `export_mcp`, `backup`, `clear_chat`) | `~/.gemini/config/scripts/setup/` | Maintenance & multi-editor MCP sync |
| Skills Library | `skills/` (231 skills, 6 categories) | `~/.gemini/config/skills_vault/` (+4 core in `skills/`) | Zero-bloat on-demand expertise |
| Agents & Rules | `agents/` (65), `rules/` (11), `workflows/` (4) | `~/.gemini/config/{agents,rules,workflows}/` | Specialized subagents, language rules & workflows |

---

## 2. FastMCP Upfront Tools (9 Active Schemas)

| # | Tool | Role |
|---|---|---|
| 1 | `execute_code_sandbox` | Run Python scripts in isolated subprocess with `tools_api/` on `PYTHONPATH` |
| 2 | `pagerank_repo_map` | Rank codebase architecture with PageRank within token budget |
| 3 | `system1_triage` | Sub-40ms local CPU log/diff triage via Convai Laya rules |
| 4 | `search_memories` | Query persistent `memory.json` strictly bounded by `max_tokens` |
| 5 | `search_skills` | Discover skills across `skills/` and `skills_vault/` on demand |
| 6 | `discover_mcp_tools` | Locate `mcp/tools_api/*.py` & `mcp/schemas/*.json` stubs on demand |
| 7 | `filter_and_loop_data` | Filter large JSON/JSONL/CSV/log files in Python before prompt entry |
| 8 | `evaluate_skill` | Grade any skill (0–100 / A–F) across frontmatter, tokens, actions, security |
| 9 | `infinite_context_compact` | Unified entry (`compact`, `virtualize`, `search`, `fetch`, `cli_compress`) |

Additional helpers (`code_graph_impact_probe`, `get_symbol`, `safe_read_file`, `diff_re_read`, `verify_agent_skill`, `model_armor_sanitize`, `add_memory`, `record_failure_reflexion`, `to_toon`, `cache_lookup_or_store`, `create_checkpoint`, `restore_checkpoint`) are exposed via `mcp/tools_api/`.

---

## 3. Daily Commands & Maintenance

```bash
# Verify entire ecosystem, security scanners, hooks, and 100-turn 90%+ benchmark
python -m unittest discover -s tests -v

# Check Ruff lint + formatting
ruff check mcp tests scripts workflows --config config/ruff.toml
ruff format --check mcp tests scripts workflows --config config/ruff.toml

# Validate external skill security before use
powershell -File scripts/setup/verify_skill.ps1 skills/ai-agentic/infinite-context-loop

# Run system health check
powershell -File scripts/setup/doctor.ps1
# or POSIX:
bash scripts/setup/doctor.sh

# Run verbose test/build commands cleanly without bloating chat context
python mcp/infinite_context.py --exec "python -m unittest discover -s tests -v"

# Clean old chat transcripts while keeping latest session
powershell -File scripts/setup/clear_chat.ps1
```
