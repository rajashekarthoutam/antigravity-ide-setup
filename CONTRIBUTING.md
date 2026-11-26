# Contributing to Antigravity God-Mode Suite

Thanks for contributing! Keep every change minimal, well-tested, and compliant with our token-economy and security invariants.

## Development Workflow

1. **Architecture First (EGM Gate)**: For non-trivial changes, draft goals/interfaces cleanly and check blast radius with `code_graph_impact_probe`.
2. **Code Quality & Style**:
   - Keep `mcp/` Python modules focused (`<= 800` lines soft ceiling) and free of circular imports.
   - Never create `mcp/__init__.py` (avoids colliding with PyPI's `mcp` package).
   - Add `encoding="utf-8"` to all file I/O.
   - Keep `AGENTS.md` strictly `< 1,000` tokens with zero volatile timestamps/nonces.
   - Keep upfront `@app.tool()` registrations in `mcp/server.py` `<= 10`.
3. **Zero PII & Security**: Never commit machine-specific paths, emails, API keys, or personal project data into `config/memory.json`, scripts, or skills.
4. **Required Checks Before Submitting**:

```bash
python -m unittest discover -s tests -v
ruff check mcp tests scripts workflows --config config/ruff.toml
ruff format --check mcp tests scripts workflows --config config/ruff.toml
bash -n installer/setup.sh installer/uninstall.sh scripts/setup/*.sh
```
