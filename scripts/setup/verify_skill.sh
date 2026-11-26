#!/usr/bin/env bash
# SkillSpector AI Skill Security & Quality Validator (Linux / macOS / WSL)
set -e

SKILL_DIR="${1:-.}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export PYTHONPATH="$REPO_ROOT/mcp:$HOME/.gemini/config/mcp:${PYTHONPATH:-}"

python3 -c '
import json, sys
from server import evaluate_skill, verify_agent_skill

target = sys.argv[1]
sec = verify_agent_skill(target)
ev = evaluate_skill(target)
print(json.dumps({"security": sec, "quality": ev}, indent=2))
if sec.get("verdict") == "MALICIOUS_REJECTED":
    sys.exit(1)
' "$SKILL_DIR"
