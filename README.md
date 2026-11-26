# Antigravity IDE & VS Code God-Mode Suite

[![Ecosystem CI & Token Audit](https://github.com/rajashekarthoutam/antigravity-ide-setup/actions/workflows/verify.yml/badge.svg)](https://github.com/rajashekarthoutam/antigravity-ide-setup/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A production-grade, cross-platform AI engineering runtime for **Google Antigravity IDE, VS Code, Cursor, Windsurf, and Claude Code** featuring an **Infinite-Horizon 90%+ Token Engine**, Code-Mode FastMCP server, Gravitas verification hooks, and on-demand skills & agent orchestration.

---

## Core Architecture

```text
antigravity-ide-setup/
├── AGENTS.md                 # Static <1,000-token master contract (KV-cache locked)
├── pyproject.toml            # Python project metadata & dependency tiers
├── mcp/
│   ├── server.py             # FastMCP entrypoint (9 upfront @app.tool() schemas)
│   ├── infinite_context.py   # FTS5 ContextVirtualizer, cli_compress, epoch compactor
│   ├── code_nav.py           # PageRank AST map, outlines, symbol slice, impact probe
│   ├── security_eval.py      # SkillSpector, Model Armor, A2A cards, skill grader
│   ├── tools_api/            # On-demand Code-Mode stubs (6 domain modules)
│   └── schemas/              # 26 tool JSON schemas
├── scripts/
│   ├── hooks/                # Gravitas Pre/Post/Stop hooks, Laya triage, token audit
│   └── setup/                # Backup, health doctor, MCP registrar, skill verifier
├── installer/                # Cross-platform setup & uninstall (.ps1 / .sh)
├── agents/                   # 65 specialized agent definitions (4 categories)
├── skills/                   # 231 progressive-disclosure skills (6 categories)
├── rules/                    # 11 layered rule sets (common + 10 languages)
├── workflows/                # 4 native multi-agent & token workflows
├── config/                   # Clean seed templates (memory.json, hooks.json, ruff.toml)
├── docs/                     # Architecture, Runtime Guide, and Token Economy specs
└── tests/                    # Automated unit, security, and 100-turn benchmark tests
```

---

## Infinite-Horizon 90%+ Token Engine (`mcp/infinite_context.py`)

Even across continuous, bloated, 100-turn agent loops, per-turn and cumulative token growth is compressed by **>=90%** through five orthogonal zero-LLM layers:

1. **Epoch-Aligned Prefix Locking**: `AGENTS.md` (`< 1,000` tokens) and compacted epoch prefixes stay byte-identical between epoch boundaries (`epoch_size=12`), preserving GPU KV-cache reuse without mid-stream cache invalidation.
2. **Preventative SQLite FTS5 Virtualization (`ContextVirtualizer` + `--exec` CLI)**: Oversized tool/command outputs (`> 1,200` chars or `35` lines) or shell commands run via `python mcp/infinite_context.py --exec "<cmd>"` / `--pipe` are redacted via Model Armor rules and indexed in local WAL SQLite FTS5 (`ctx://<hash12>`), inserting only a concise structural digest into chat while supporting bounded BM25 search & slice fetches (`<= 150` lines).
3. **Deterministic CLI Noise Compression (`cli_compress`)**: Strips ANSI sequences, `\r` spinner rewrites, package download chatter, and passing dot noise on CPU while unconditionally preserving stack traces, test failure counts, assertions, and unified diffs.
4. **DCP Cleanup + JetBrains Observation Masking**: Deduplicates repeated read/search calls, supersedes stale file reads/writes, purges oversized arguments from old errored calls (keeping root cause), and masks pre-window tool observations outside `window=4`.
5. **Anchored State Capsule**: Folds pre-window prose into a bounded `<= 450`-token capsule (`intent`, `files`, `decisions`, `errors`, `handles`, `next`), reporting raw reduction and advisory KV-cache metrics cleanly without conflation.

---

## Quick Start Installation

### Windows (PowerShell)
```powershell
.\installer\setup.ps1 -NonInteractive
```

### Linux & macOS (Bash)
```bash
chmod +x installer/setup.sh
./installer/setup.sh --yes
```

Deployments copy the full `mcp/` engine into `~/.gemini/config/mcp/`, deploy skills to `~/.gemini/config/skills_vault/` (loading 4 core skills upfront), and register `god-mode` across Antigravity, VS Code, Cursor, Windsurf, and Claude Desktop.

---

## Verification & Diagnostics

```bash
# Run full unit, security, hook, and 100-turn infinite-loop benchmark suite
python -m unittest discover -s tests -v

# Lint and check formatting
ruff check mcp tests scripts workflows --config config/ruff.toml
ruff format --check mcp tests scripts workflows --config config/ruff.toml

# Validate a skill package
bash scripts/setup/verify_skill.sh skills/ai-agentic/infinite-context-loop

# Run system health doctor
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup/doctor.ps1
```

To uninstall cleanly: `.\installer\uninstall.ps1` (Windows) or `./installer/uninstall.sh` (POSIX).
