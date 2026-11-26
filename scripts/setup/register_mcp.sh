#!/usr/bin/env bash
# Universal Global MCP Registrar for All Editors & AI Assistants (Linux / macOS)
# Registers God-Mode FastMCP globally across:
# 1. Google Antigravity IDE & Antigravity CLI
# 2. DeepSeek Harness (dsh)
# 3. VS Code / Cline / Roo-Code
# 4. Cursor IDE
# 5. Windsurf
# 6. Claude Desktop

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GOD_MODE_PY="$HOME/.gemini/config/mcp/server.py"

if [ ! -f "$GOD_MODE_PY" ]; then
    GOD_MODE_PY="$REPO_ROOT/mcp/server.py"
fi

echo -e "\033[36m=== Universal Global MCP Registrar (POSIX) ===\033[0m"
echo -e "\033[2mServer: $GOD_MODE_PY\033[0m\n"

register_target() {
    local name="$1"
    local target_file="$2"
    local dir_path
    dir_path="$(dirname "$target_file")"
    mkdir -p "$dir_path"

    python3 -c "
import json, os, sys

target = r'$target_file'
server_def = {
    'command': 'python3',
    'args': [r'$GOD_MODE_PY'],
    'env': {
        'PYTHONPATH': '$REPO_ROOT:$REPO_ROOT/mcp:$HOME/.gemini/config:$HOME/.gemini/config/mcp'
    }
}

data = {}
if os.path.exists(target):
    try:
        with open(target, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}

if 'mcpServers' not in data:
    data['mcpServers'] = {}

data['mcpServers']['god-mode'] = server_def

with open(target, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
"
    echo -e "  \033[32m[OK]\033[0m   $name -> $target_file"
}

# 1. Google Antigravity Global
register_target "Google Antigravity Global" "$HOME/.gemini/config/mcp_config.json"

# 2. DeepSeek Harness (dsh) God-Mode Profile
register_target "DeepSeek Harness Profile" "$HOME/.dsh/profiles/god-mode/runtime.json"

# 3. VS Code Global Settings
register_target "VS Code (Roo-Code)" "$HOME/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json"
register_target "VS Code (Cline)" "$HOME/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"

# 4. Cursor IDE
register_target "Cursor IDE" "$HOME/.cursor/mcp.json"

# 5. Windsurf
register_target "Windsurf IDE" "$HOME/.codeium/windsurf/mcp_config.json"

# 6. Claude Desktop
if [ "$(uname)" = "Darwin" ]; then
    register_target "Claude Desktop" "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
else
    register_target "Claude Desktop" "$HOME/.config/Claude/claude_desktop_config.json"
fi

# 7. Deploy Universal Antigravity System Prompts & Agent Rules Globally
echo -e "\n\033[33mDeploying Universal Antigravity Rules & Identity...\033[0m"
MASTER_PROMPT="$REPO_ROOT/AGENTS.md"
[ ! -f "$MASTER_PROMPT" ] && MASTER_PROMPT="$REPO_ROOT/config/system_prompt.md"
if [ -f "$MASTER_PROMPT" ]; then
    # DeepSeek Harness Profile System Prompt
    mkdir -p "$HOME/.dsh/profiles/god-mode"
    cp "$MASTER_PROMPT" "$HOME/.dsh/profiles/god-mode/system_prompt.md"
    echo -e "  \033[32m[OK]\033[0m   DeepSeek Harness System Prompt -> $HOME/.dsh/profiles/god-mode/system_prompt.md"

    # Global Cursor Rules
    mkdir -p "$HOME/.cursor/rules"
    cp "$MASTER_PROMPT" "$HOME/.cursor/rules/antigravity.mdc"
    echo -e "  \033[32m[OK]\033[0m   Global Cursor Rules -> $HOME/.cursor/rules/antigravity.mdc"

    # Claude Code Global CLAUDE.md
    mkdir -p "$HOME/.claude"
    cp "$MASTER_PROMPT" "$HOME/.claude/CLAUDE.md"
    echo -e "  \033[32m[OK]\033[0m   Claude Code Global Memory -> $HOME/.claude/CLAUDE.md"
fi

echo -e "\n\033[36mGod-Mode FastMCP & Antigravity Rules are now globally active for Antigravity, DeepSeek Harness, and all AI editors!\033[0m\n"
