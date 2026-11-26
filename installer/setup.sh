#!/usr/bin/env bash
# Antigravity IDE & VS Code FastMCP Installer (Linux & macOS)
# Autonomous Engineering Intelligence for Google Antigravity & VS Code
set -e

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
DIM="\033[2m"
RESET="\033[0m"

NON_INTERACTIVE=false
FORCE=false
UNINSTALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        -y|--yes|--non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo -e "${CYAN}${BOLD}Antigravity IDE & VS Code FastMCP Installer${RESET}"
            echo -e "Usage: ./install.sh [options]\n"
            echo -e "Flags:"
            echo -e "  --uninstall   Clean uninstallation and system restoration"
            echo -e "  -y, --yes     Non-interactive unattended execution (CI/CD, Docker)"
            echo -e "  -f, --force   Force overwrite existing configurations"
            echo -e "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$REPO_DIR/.." && pwd)"

# Delegate to uninstaller if selected
if [ "$UNINSTALL" = true ]; then
    UNINSTALL_BIN="$REPO_DIR/uninstall.sh"
    [ ! -f "$UNINSTALL_BIN" ] && UNINSTALL_BIN="$REPO_ROOT/installer/uninstall.sh"
    if [ -f "$UNINSTALL_BIN" ]; then
        if [ "$NON_INTERACTIVE" = true ] || [ "$FORCE" = true ]; then
            bash "$UNINSTALL_BIN" --force
        else
            bash "$UNINSTALL_BIN"
        fi
        exit 0
    else
        echo -e "${RED}[Error] uninstall.sh not found in $REPO_DIR${RESET}"
        exit 1
    fi
fi

echo -e "\n${CYAN}${BOLD}╔════════════════════════════════════════════════════════════════════════╗"
echo -e "║   Antigravity IDE & VS Code FastMCP Suite Installer                    ║"
echo -e "╚════════════════════════════════════════════════════════════════════════╝${RESET}\n"

# 1. Check OS and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"
echo -e "${DIM}Platform: $OS ($ARCH)${RESET}"

# 2. Smart Check & Ensure Python Runtime (>= 3.10)
echo -e "\n${YELLOW}[1/5] Auto-checking Python runtime (>= 3.10)...${RESET}"
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null || true)
    PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null || true)
    PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null || true)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        echo -e "  ${GREEN}[SKIP]${RESET} Python verified: $PY_VER (already installed)"
    else
        echo -e "${RED}[Error] Python 3.10+ required. Current version: $PY_VER${RESET}"
        exit 1
    fi
else
    echo -e "${RED}[Error] Python 3 executable not found in PATH.${RESET}"
    exit 1
fi

# 3. Check & Install Python Core Dependencies
echo -e "\n${YELLOW}[2/5] Auto-checking Python core packages...${RESET}"
if python3 -c "import tiktoken, mcp, ruff; print('OK')" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[SKIP]${RESET} Core Python packages (tiktoken, mcp, ruff) already installed"
else
    echo -e "  ${CYAN}Installing missing Python packages...${RESET}"
    python3 -m pip install --quiet --upgrade tiktoken mcp ruff || {
        echo -e "${YELLOW}[Warning] pip install had warnings; continuing with runtime check.${RESET}"
    }
fi

# 4. Determine installation paths & deploy config
echo -e "\n${YELLOW}[3/5] Deploying Global Configurations to ~/.gemini/config...${RESET}"
mkdir -p "$HOME/.gemini/config"
for dir in rules workflows scripts; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        cp -r "$REPO_ROOT/$dir" "$HOME/.gemini/config/" 2>/dev/null || true
    fi
done
rm -rf "$HOME/.gemini/config/skills"
mkdir -p "$HOME/.gemini/config/skills_vault" "$HOME/.gemini/config/skills" "$HOME/.gemini/config/agents"
if [ -d "$REPO_ROOT/skills" ]; then
    find "$REPO_ROOT/skills" -type f -name "SKILL.md" | while read -r smd; do
        sdir="$(dirname "$smd")"
        sname="$(basename "$sdir")"
        cp -r "$sdir" "$HOME/.gemini/config/skills_vault/" 2>/dev/null || true
        if [ "$sname" = "elephant-goldfish-model" ] || [ "$sname" = "code-execution-mcp" ] || [ "$sname" = "skill-evaluator" ] || [ "$sname" = "infinite-context-loop" ]; then
            cp -r "$sdir" "$HOME/.gemini/config/skills/" 2>/dev/null || true
        fi
    done
fi
if [ -d "$REPO_ROOT/agents" ]; then
    find "$REPO_ROOT/agents" -type f -name "*.md" -exec cp {} "$HOME/.gemini/config/agents/" \; 2>/dev/null || true
fi
for file in AGENTS.md; do
    if [ -f "$REPO_ROOT/$file" ]; then
        cp "$REPO_ROOT/$file" "$HOME/.gemini/config/" 2>/dev/null || true
    fi
done
rm -f "$HOME/.gemini/config/server.py" "$HOME/.gemini/config/god_mode_mcp.py" "$HOME/.gemini/config/ANTIGRAVITY_SYSTEM_PROMPT.md" "$HOME/.gemini/config/GOD_MODE.md" "$HOME/.gemini/config/repomix.config.json" 2>/dev/null || true
if [ ! -f "$HOME/.gemini/config/memory.json" ] && [ -f "$HOME/.gemini/config/god_mode_mem0.json" ]; then
    mv "$HOME/.gemini/config/god_mode_mem0.json" "$HOME/.gemini/config/memory.json" 2>/dev/null || true
fi
if [ -d "$REPO_ROOT/mcp" ]; then
    mkdir -p "$HOME/.gemini/config/mcp"
    cp -r "$REPO_ROOT/mcp/"* "$HOME/.gemini/config/mcp/" 2>/dev/null || true
    find "$HOME/.gemini/config/mcp" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi
if [ -d "$REPO_ROOT/mcp/schemas" ]; then
    mkdir -p "$HOME/.gemini/antigravity/mcp/god-mode" "$HOME/.gemini/antigravity-ide/mcp/god-mode"
    cp "$REPO_ROOT/mcp/schemas/"*.json "$HOME/.gemini/antigravity/mcp/god-mode/" 2>/dev/null || true
    cp "$REPO_ROOT/mcp/schemas/"*.json "$HOME/.gemini/antigravity-ide/mcp/god-mode/" 2>/dev/null || true
fi
if [ -d "$REPO_ROOT/config" ]; then
    cp -r "$REPO_ROOT/config/"* "$HOME/.gemini/config/" 2>/dev/null || true
fi
echo -e "  ${GREEN}[OK]${RESET} Deployed unified payload (mcp engine, skills_vault, agents, rules, scripts, workflows, config)"

# 5. Register Global FastMCP across Antigravity and VS Code / Cursor
echo -e "\n${YELLOW}[4/5] Registering FastMCP Globally & Deploying Master Rules...${RESET}"
if [ -f "$REPO_ROOT/scripts/setup/register_mcp.sh" ]; then
    bash "$REPO_ROOT/scripts/setup/register_mcp.sh" || true
fi
if [ -f "$REPO_ROOT/scripts/setup/export_mcp.sh" ]; then
    bash "$REPO_ROOT/scripts/setup/export_mcp.sh" || true
fi

# 6. Run Environment Health Doctor
echo -e "\n${YELLOW}[5/5] Running Antigravity Health Doctor...${RESET}"
if [ -f "$REPO_ROOT/scripts/setup/doctor.sh" ]; then
    bash "$REPO_ROOT/scripts/setup/doctor.sh" || true
fi

echo -e "\n${GREEN}${BOLD}════════════════════════════════════════════════════════════════════════"
echo -e "✓ Antigravity IDE & VS Code Suite successfully installed!"
echo -e "════════════════════════════════════════════════════════════════════════${RESET}"
SKILL_COUNT=$(find "$HOME/.gemini/config/skills_vault" -maxdepth 2 -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
echo -e "Ready to use in:"
echo -e "  1. ${BOLD}Google Antigravity IDE${RESET} - FastMCP server (9 upfront / 26 schema tools) and ${SKILL_COUNT} skills active"
echo -e "  2. ${BOLD}VS Code / Cursor${RESET}       - FastMCP server & Infinite-Horizon Context Engine active"
echo -e "\nTo cleanly uninstall: ./installer/uninstall.sh\n"
exit 0
