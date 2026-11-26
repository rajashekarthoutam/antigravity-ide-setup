#!/usr/bin/env bash
# Export God-Mode FastMCP configuration to VS Code, Cursor, and Claude Desktop (Linux / macOS)
set -e

TARGET_DIR="${1:-$(pwd)}"
GLOBAL="${2:-false}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GOD_MODE_PY="$REPO_ROOT/mcp/server.py"
[ ! -f "$GOD_MODE_PY" ] && GOD_MODE_PY="$HOME/.gemini/config/mcp/server.py"

echo -e "\033[36m=== Antigravity MCP Bridge Generator ===\033[0m"
echo -e "\033[2mTarget Directory: $TARGET_DIR\033[0m"

# Generate JSON payload
MCP_JSON=$(cat <<EOF
{
  "mcpServers": {
    "god-mode": {
      "command": "python3",
      "args": ["$GOD_MODE_PY"],
      "env": {
        "PYTHONPATH": "$REPO_ROOT:$REPO_ROOT/mcp"
      }
    }
  }
}
EOF
)

# 1. Project-level .vscode/mcp.json
mkdir -p "$TARGET_DIR/.vscode"
echo "$MCP_JSON" > "$TARGET_DIR/.vscode/mcp.json"
echo -e " \033[32m[OK]\033[0m Created Project MCP config: $TARGET_DIR/.vscode/mcp.json"

# 2. Global Claude Desktop config if requested
if [ "$GLOBAL" = "--global" ] || [ "$GLOBAL" = "-g" ]; then
    CLAUDE_DIR="$HOME/.config/Claude"
    if [ "$(uname)" = "Darwin" ]; then
        CLAUDE_DIR="$HOME/Library/Application Support/Claude"
    fi
    mkdir -p "$CLAUDE_DIR"
    echo "$MCP_JSON" > "$CLAUDE_DIR/claude_desktop_config.json"
    echo -e " \033[32m[OK]\033[0m Created Claude Desktop MCP config: $CLAUDE_DIR/claude_desktop_config.json"
fi

echo -e "\n\033[36mGod-Mode FastMCP tools are now active in your editor!\033[0m"
