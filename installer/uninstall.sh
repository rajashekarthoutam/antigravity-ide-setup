#!/usr/bin/env bash
# Antigravity IDE & VS Code FastMCP Suite Uninstaller (Linux & macOS)
set -e

FORCE=false
for arg in "$@"; do
    case "$arg" in
        -y|--yes|-f|--force)
            FORCE=true
            ;;
        -h|--help)
            echo "Usage: ./uninstall.sh [-y|--force]"
            exit 0
            ;;
    esac
done

if [ "$FORCE" = false ]; then
    echo -e "\033[31m╔══════════════════════════════════════════════════════════════════════╗"
    echo -e "║   Antigravity IDE & VS Code FastMCP Suite Uninstaller (POSIX)        ║"
    echo -e "╚══════════════════════════════════════════════════════════════════════╝\033[0m\n"
    echo -e "This will cleanly remove:"
    echo -e "  - FastMCP registration in Antigravity IDE & CLI (~/.gemini/config/mcp_config.json)"
    echo -e "  - MCP server configurations in VS Code, Cursor, Windsurf, Claude"
    echo -e "  - Global editor rules (~/.cursor/rules/antigravity.mdc, ~/.claude/CLAUDE.md)"
    echo -e "  - Your personal repositories and code will NOT be touched.\n"

    read -p "Are you sure you want to proceed with uninstallation? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "\033[36mUninstallation canceled.\033[0m"
        exit 0
    fi
fi

remove_mcp_entry() {
    local target_file="$1"
    local server_name="${2:-god-mode}"
    if [ -f "$target_file" ]; then
        python3 -c "
import json, os
path = r'$target_file'
server = '$server_name'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if 'mcpServers' in data and server in data['mcpServers']:
        del data['mcpServers'][server]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print('  [OK] Unregistered ' + server + ' from ' + path)
except Exception:
    pass
" 2>/dev/null || true
    fi
}

echo -e "\n\033[33m[1/4] Removing FastMCP configurations...\033[0m"
rm -f "$HOME/.gemini/config/mcp_config.json" 2>/dev/null || true
rm -rf "$HOME/.gemini/antigravity/mcp/god-mode" 2>/dev/null || true
rm -rf "$HOME/.gemini/antigravity-ide/mcp/god-mode" 2>/dev/null || true
echo -e "  \033[32m[OK]\033[0m Cleaned Antigravity IDE & CLI registrations"

echo -e "\n\033[33m[2/4] Cleaning Global Editor MCP Configurations...\033[0m"
remove_mcp_entry "$HOME/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json"
remove_mcp_entry "$HOME/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
remove_mcp_entry "$HOME/.cursor/mcp.json"
remove_mcp_entry "$HOME/.codeium/windsurf/mcp_config.json"
remove_mcp_entry "$HOME/.config/Claude/claude_desktop_config.json"
remove_mcp_entry "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo -e "\n\033[33m[3/4] Removing Global Editor Rules & Prompts...\033[0m"
rm -f "$HOME/.cursor/rules/antigravity.mdc" 2>/dev/null || true
rm -f "$HOME/.claude/CLAUDE.md" 2>/dev/null || true
echo -e "  \033[32m[OK]\033[0m Cleaned global editor rule files"

echo -e "\n\033[33m[4/4] Removing Deployed Config Modules & Symlinks...\033[0m"
rm -rf "$HOME/.gemini/config/mcp" "$HOME/.gemini/config/skills_vault" 2>/dev/null || true
rm -f "$HOME/.gemini/config/server.py" "$HOME/.gemini/config/context_vault.db"* 2>/dev/null || true
BIN_DIR="$HOME/.local/bin"
for bin_name in agy dsh agy-doctor agy-verify-skill; do
    if [ -L "$BIN_DIR/$bin_name" ] || [ -f "$BIN_DIR/$bin_name" ]; then
        rm -f "$BIN_DIR/$bin_name"
    fi
done

echo -e "\n\033[32m════════════════════════════════════════════════════════════════════════"
echo -e "✓ Antigravity Uninstallation Complete! System restored cleanly."
echo -e "════════════════════════════════════════════════════════════════════════\033[0m\n"
