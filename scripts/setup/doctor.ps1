# Antigravity IDE Setup - Comprehensive Environment Doctor & Health Auditor
# Sub-second deterministic verification across Python, FastMCP, Scoop, Mem0, and Git.

$ErrorActionPreference = 'Continue'
$totalChecks = 0
$passedChecks = 0
$warnChecks = 0
$failChecks = 0

function Report-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Details
    )
    $script:totalChecks++
    if ($Status -eq 'OK') {
        $script:passedChecks++
        Write-Host "  [OK]   " -ForegroundColor Green -NoNewline
    } elseif ($Status -eq 'WARN') {
        $script:warnChecks++
        Write-Host "  [WARN] " -ForegroundColor Yellow -NoNewline
    } else {
        $script:failChecks++
        Write-Host "  [FAIL] " -ForegroundColor Red -NoNewline
    }
    Write-Host "$Name" -ForegroundColor White -NoNewline
    if ($Details) {
        Write-Host " - $Details" -ForegroundColor DarkGray
    } else {
        Write-Host ""
    }
}

Write-Host "`n=== Antigravity IDE Suite Doctor ===" -ForegroundColor Cyan
Write-Host "Verifying execution runtime, FastMCP tools, memory, and environment...`n" -ForegroundColor DarkGray

# 1. Python Runtime
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Report-Check "Python Runtime" "OK" "$pyVersion"
} else {
    Report-Check "Python Runtime" "FAIL" "Python not found in PATH"
}

# 2. Python Core Packages
$pkgs = python -c "import tiktoken, mcp, ruff; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Report-Check "Core AI Agent Libraries" "OK" "tiktoken, mcp, ruff installed"
} else {
    Report-Check "Core AI Agent Libraries" "WARN" "Some packages missing: $pkgs"
}

# 3. FastMCP Syntax & Module Verification
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$godModePyCandidates = @(
    (Join-Path $repoRoot "mcp\server.py"),
    ([System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "mcp", "server.py"))
)
$godModePy = $null
foreach ($cand in $godModePyCandidates) {
    if (Test-Path $cand) {
        $godModePy = $cand
        break
    }
}
if ($godModePy) {
    $mcpParent = Split-Path -Parent $godModePy
    $compileRes = python -c "import sys; sys.path.insert(0, r'$mcpParent'); import server, infinite_context, context_vault, text_filters, code_nav, security_eval, ops_helpers; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Report-Check "FastMCP Server & Infinite Engine" "OK" "server + infinite_context + context_vault + text_filters + code_nav + security_eval + ops_helpers verified"
    } else {
        Report-Check "FastMCP Server & Infinite Engine" "FAIL" "Import/compile error: $compileRes"
    }
} else {
    Report-Check "FastMCP Server & Infinite Engine" "WARN" "mcp/server.py not found"
}

# 4. Mem0 Continuous Memory
$mem0File = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "memory.json")
if (Test-Path $mem0File) {
    try {
        $memData = Get-Content $mem0File -Raw | ConvertFrom-Json
        $count = $memData.memories.Count
        Report-Check "Persistent Episodic Memory (Mem0)" "OK" "$count persistent memories indexed"
    } catch {
        Report-Check "Persistent Episodic Memory (Mem0)" "WARN" "Memory JSON format invalid"
    }
} else {
    Report-Check "Persistent Episodic Memory (Mem0)" "WARN" "memory.json not found"
}

# 5. Start Menu Clutter-Free Organization
$scoopAppsDir = [System.IO.Path]::Combine($env:APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Scoop Apps")
if (Test-Path $scoopAppsDir) {
    $looseFiles = Get-ChildItem $scoopAppsDir -File
    $subDirs = Get-ChildItem $scoopAppsDir -Directory
    if ($looseFiles.Count -eq 0) {
        Report-Check "Start Menu Folder Hierarchy" "OK" "$($subDirs.Count) clean software folders, 0 loose shortcuts"
    } else {
        Report-Check "Start Menu Folder Hierarchy" "WARN" "$($looseFiles.Count) loose shortcuts found in root folder"
    }
} else {
    Report-Check "Start Menu Folder Hierarchy" "OK" "Directory not initialized yet"
}

# 6. KV-Cache Static Prefix Token Budget
$agentsMd = Join-Path $repoRoot "AGENTS.md"
if (Test-Path $agentsMd) {
    $tokenCheck = python -c "import tiktoken; enc = tiktoken.get_encoding('cl100k_base'); text = open(r'$agentsMd', encoding='utf-8').read(); tokens = len(enc.encode(text)); print(tokens)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $tokInt = [int]$tokenCheck
        if ($tokInt -lt 1000) {
            Report-Check "KV-Cache Static Prefix Invariant" "OK" "$tokInt tokens (< 1000 budget limit)"
        } else {
            Report-Check "KV-Cache Static Prefix Invariant" "FAIL" "$tokInt tokens exceeds 1000 budget limit!"
        }
    }
}

# 7. Workspace Git Repository Health
if (Test-Path (Join-Path $repoRoot ".git")) {
    $st = git -C $repoRoot status --porcelain 2>$null
    if (-not $st) {
        Report-Check "Workspace Git Repository" "OK" "Repository working tree is clean"
    } else {
        Report-Check "Workspace Git Repository" "WARN" "Uncommitted local modifications present"
    }
} else {
    Report-Check "Workspace Git Repository" "OK" "Deployed non-git runtime layout"
}

Write-Host "`n----------------------------------------" -ForegroundColor DarkGray
if ($failChecks -eq 0) {
    Write-Host "Summary: All systems operational ($passedChecks/$totalChecks passed, $warnChecks warnings)`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Summary: $failChecks check(s) failed ($passedChecks passed, $warnChecks warnings)`n" -ForegroundColor Red
    exit 1
}
