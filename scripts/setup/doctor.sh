#!/usr/bin/env bash
# Antigravity Universal Agent Suite Doctor (Linux / macOS / WSL)
# Deterministic health check across Python, FastMCP, Ollama, and Git.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

TOTAL_CHECKS=0
PASSED_CHECKS=0
WARN_CHECKS=0
FAIL_CHECKS=0

report_check() {
    local name="$1"
    local status="$2"
    local details="$3"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ "$status" = "OK" ]; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        echo -e "  \033[32m[OK]\033[0m   \033[1m$name\033[0m - \033[2m$details\033[0m"
    elif [ "$status" = "WARN" ]; then
        WARN_CHECKS=$((WARN_CHECKS + 1))
        echo -e "  \033[33m[WARN]\033[0m \033[1m$name\033[0m - \033[33m$details\033[0m"
    else
        FAIL_CHECKS=$((FAIL_CHECKS + 1))
        echo -e "  \033[31m[FAIL]\033[0m \033[1m$name\033[0m - \033[31m$details\033[0m"
    fi
}

echo -e "\n\033[36m\033[1m=== Antigravity Universal Runtime Doctor (POSIX) ===\033[0m"
echo -e "\033[2mVerifying execution runtime, FastMCP tools, memory, and environment...\033[0m\n"

# 1. Python Check
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 --version)
    report_check "Python 3 Runtime" "OK" "$PY_VER"
else
    report_check "Python 3 Runtime" "FAIL" "python3 executable not found"
fi

# 2. AI Core Packages
if python3 -c "import tiktoken, mcp; print('OK')" >/dev/null 2>&1; then
    report_check "AI Agent Core Packages" "OK" "tiktoken, mcp present"
else
    report_check "AI Agent Core Packages" "WARN" "Some python packages missing (run pip install tiktoken mcp)"
fi

# 3. FastMCP Syntax & Module Verification
GOD_MODE_PY="$REPO_ROOT/mcp/server.py"
[ ! -f "$GOD_MODE_PY" ] && GOD_MODE_PY="$HOME/.gemini/config/mcp/server.py"
if [ -f "$GOD_MODE_PY" ]; then
    MCP_DIR="$(dirname "$GOD_MODE_PY")"
    if python3 -c "import sys; sys.path.insert(0, r'$MCP_DIR'); import server, infinite_context, context_vault, text_filters, code_nav, security_eval, ops_helpers; print('OK')" >/dev/null 2>&1; then
        report_check "FastMCP Server & Infinite Engine" "OK" "server + infinite_context + context_vault + text_filters + code_nav + security_eval + ops_helpers verified"
    else
        report_check "FastMCP Server & Infinite Engine" "FAIL" "Import/compile error in $MCP_DIR"
    fi
fi

# 4. Ollama Local Daemon
if command -v ollama >/dev/null 2>&1; then
    report_check "Local Inference (Ollama)" "OK" "Ollama CLI installed"
else
    report_check "Local Inference (Ollama)" "WARN" "Ollama not in PATH (optional for local models)"
fi

# 5. Git CLI
if command -v git >/dev/null 2>&1; then
    GIT_VER=$(git --version)
    report_check "Version Control (Git)" "OK" "$GIT_VER"
else
    report_check "Version Control (Git)" "WARN" "git not found"
fi

echo -e "\n\033[1mDoctor Summary:\033[0m $PASSED_CHECKS Passed, $WARN_CHECKS Warnings, $FAIL_CHECKS Failed (Total $TOTAL_CHECKS checks)"
if [ "$FAIL_CHECKS" -eq 0 ]; then
    echo -e "\033[32mAntigravity Universal Runtime is 100% HEALTHY.\033[0m\n"
    exit 0
else
    echo -e "\033[31mHealth checks reported failures. Resolve before launching.\033[0m\n"
    exit 1
fi
