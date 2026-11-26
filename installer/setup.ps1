# Antigravity IDE & VS Code FastMCP Installer
# Autonomous Engineering Intelligence for Google Antigravity & VS Code (Windows PowerShell)

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$NonInteractive,
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host @"
========================================================================
   Antigravity IDE & VS Code Setup Installer
========================================================================

Usage:
  .\installer\setup.ps1 [options]

Flags & Automation:
  -Uninstall           Cleanly unregisters FastMCP server and removes configurations
  -NonInteractive      Unattended execution (skips interactive prompts)
  -Force               Force overwrite existing configurations during install/uninstall
  -Help                Show this help screen
"@
    exit 0
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = Split-Path -Parent $scriptDir

# Delegate to uninstaller if selected
if ($Uninstall) {
    $uninstallScript = Join-Path $scriptDir "uninstall.ps1"
    if (-not (Test-Path $uninstallScript)) { $uninstallScript = Join-Path $repoRoot "installer\uninstall.ps1" }
    if (Test-Path $uninstallScript) {
        if ($Force -or $NonInteractive) {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uninstallScript -Force
        }
        else {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uninstallScript
        }
        exit $LASTEXITCODE
    }
    else {
        Write-Host "Error: uninstall.ps1 not found in $scriptDir" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host "   Installing Antigravity IDE & VS Code Suite                           " -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan

$geminiRoot = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini")
$geminiConfig = [System.IO.Path]::Combine($geminiRoot, "config")
$antigravityIdeMcp = [System.IO.Path]::Combine($geminiRoot, "antigravity-ide", "mcp", "god-mode")
$antigravityCliMcp = [System.IO.Path]::Combine($geminiRoot, "antigravity", "mcp", "god-mode")

# 1. Smart Check & Ensure Python Runtime
Write-Host "`n[1/6] Auto-checking Python runtime (>= 3.10)..." -ForegroundColor Yellow
$pyResolved = $null

if (Get-Command "python" -ErrorAction SilentlyContinue) {
    try {
        $pyVerStr = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
        $pyMajor = & python -c "import sys; print(sys.version_info.major)" 2>$null
        $pyMinor = & python -c "import sys; print(sys.version_info.minor)" 2>$null
        if ([int]$pyMajor -ge 3 -and [int]$pyMinor -ge 10) {
            $pyResolved = (Get-Command "python").Source
            Write-Host "  -> [SKIP] Python verified: $pyVerStr ($pyResolved)" -ForegroundColor Green
        }
    }
    catch {}
}

if (-not $pyResolved) {
    # Check uv managed Python
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        $uvPy = (uv python find 2>$null)
        if ($uvPy -and (Test-Path $uvPy.Trim())) {
            $pyResolved = $uvPy.Trim()
            Write-Host "  -> [SKIP] Found uv-managed Python: $pyResolved" -ForegroundColor Green
        }
    }
}

if (-not $pyResolved) {
    # Check default Windows Python installation paths
    $pyCandidate = [System.IO.Path]::Combine($env:LOCALAPPDATA, "Programs", "Python", "Python312", "python.exe")
    if (Test-Path $pyCandidate) {
        $pyResolved = $pyCandidate
        Write-Host "  -> [SKIP] Found Python at: $pyResolved" -ForegroundColor Green
    }
}

if (-not $pyResolved) {
    Write-Host "  -> Python >= 3.10 was not found." -ForegroundColor Yellow
    $doInstallPy = $true
    if (-not $NonInteractive) {
        $promptPy = Read-Host "Would you like to install Python 3.12 automatically? (Y/n)"
        if ($promptPy -eq 'n' -or $promptPy -eq 'N') {
            $doInstallPy = $false
        }
    }

    if ($doInstallPy) {
        Write-Host "  -> Attempting automatic Python installation..." -ForegroundColor Cyan
        if (Get-Command "uv" -ErrorAction SilentlyContinue) {
            try {
                uv python install 3.12 | Out-Null
                $pyResolved = (uv python find).Trim()
            }
            catch {}
        }
        if (-not $pyResolved -and (Get-Command "scoop" -ErrorAction SilentlyContinue)) {
            try {
                scoop install python | Out-Null
                if (Get-Command "python" -ErrorAction SilentlyContinue) {
                    $pyResolved = (Get-Command "python").Source
                }
            }
            catch {}
        }
        if (-not $pyResolved -and (Get-Command "winget" -ErrorAction SilentlyContinue)) {
            try {
                winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
                $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
                if (Get-Command "python" -ErrorAction SilentlyContinue) {
                    $pyResolved = (Get-Command "python").Source
                }
            }
            catch {}
        }
    }

    if (-not $pyResolved) {
        Write-Host "  -> [ERROR] Python 3.10+ is required. Please install Python manually and re-run." -ForegroundColor Red
        Exit 1
    }
}

# 2. Smart Check & Install Core Python Packages
Write-Host "`n[2/6] Auto-checking God-Mode Python packages..." -ForegroundColor Yellow
$packages = @("mcp>=1.28.1,<2.0.0", "tiktoken", "ast-grep-cli", "ruff", "llmtrim", "mem0ai", "fastembed", "mcptoon")

$allPkgsPresent = $false
try {
    $verifyCheck = & $pyResolved -c "import mcp, tiktoken, ruff, mem0, fastembed; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $allPkgsPresent = $true
        Write-Host "  -> [SKIP] Core Python AI packages already installed and verified." -ForegroundColor Green
    }
}
catch {}

if (-not $allPkgsPresent) {
    Write-Host "  -> Installing / Updating God-Mode Python packages..." -ForegroundColor Cyan
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        try {
            uv pip install --system --break-system-packages --python $pyResolved $packages | Out-Null
        }
        catch {
            & $pyResolved -m pip install --quiet --upgrade pip
            & $pyResolved -m pip install --quiet $packages
        }
    }
    else {
        & $pyResolved -m pip install --quiet --upgrade pip
        & $pyResolved -m pip install --quiet $packages
    }
    Write-Host "  -> Installed/Verified: $($packages -join ', ')" -ForegroundColor Green
}

# 3.5 Configure Windows Defender exclusions (safe best effort)
$userProfile = $env:USERPROFILE
$devPaths = [System.Collections.Generic.List[string]]@("$userProfile\scoop", "$userProfile\.gemini")
if ($repoRoot -and (Test-Path $repoRoot) -and -not $devPaths.Contains($repoRoot)) {
    $devPaths.Add($repoRoot)
}
try {
    Add-MpPreference -ExclusionPath $devPaths -ErrorAction SilentlyContinue
    Add-MpPreference -AttackSurfaceReductionOnlyExclusions $devPaths -ErrorAction SilentlyContinue
    Write-Host "  -> Developer directory exclusions configured." -ForegroundColor Green
}
catch {}

# 4. Deploy Global Configurations (~/.gemini/config)
Write-Host "`n[3/6] Deploying Global Configurations to $geminiConfig..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $geminiConfig | Out-Null

$configDir = Join-Path $repoRoot "config"

# Copy root core files and config files
$coreAgents = Join-Path $repoRoot "AGENTS.md"
if (Test-Path $coreAgents) {
    Copy-Item -Path $coreAgents -Destination $geminiConfig -Force
    Write-Host "  -> Deployed AGENTS.md" -ForegroundColor Green
}
$mcpSrcDir = Join-Path $repoRoot "mcp"
$geminiMcpDir = Join-Path $geminiConfig "mcp"
$legacyServer = Join-Path $geminiConfig "server.py"
if (Test-Path $legacyServer) { Remove-Item -Path $legacyServer -Force -ErrorAction SilentlyContinue }
if (Test-Path $mcpSrcDir) {
    New-Item -ItemType Directory -Force -Path $geminiMcpDir | Out-Null
    Copy-Item -Path "$mcpSrcDir\*" -Destination $geminiMcpDir -Recurse -Force -Exclude @("__pycache__", ".ruff_cache")
    Write-Host "  -> Deployed full mcp/ engine (server.py, infinite_context.py, code_nav.py, security_eval.py, tools_api/, schemas/)" -ForegroundColor Green
}

# Copy template configurations from config/
if (Test-Path $configDir) {
    Get-ChildItem -Path $configDir -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $geminiConfig -Force
        Write-Host "  -> Deployed $($_.Name)" -ForegroundColor Green
    }
}

$godModeCandidate = Join-Path $repoRoot "docs\RUNTIME_GUIDE.md"
if (Test-Path $godModeCandidate) {
    Copy-Item -Path $godModeCandidate -Destination $geminiConfig -Force
    Write-Host "  -> Deployed RUNTIME_GUIDE.md" -ForegroundColor Green
}

$targetScripts = Join-Path $geminiConfig "scripts"
New-Item -ItemType Directory -Force -Path $targetScripts | Out-Null
# Clean deprecated v1 loose scripts so hooks/ and setup/ are canonical
foreach ($oldScript in @(
    "agy-doctor.cmd", "agy-doctor.ps1", "agy-doctor.sh",
    "agy-verify-skill.cmd", "agy-verify-skill.ps1", "agy-verify-skill.sh",
    "clear_chat_history.bat", "clear_chat_history.ps1",
    "export-vscode-mcp.ps1", "export-vscode-mcp.sh",
    "register-global-mcp.ps1", "register-global-mcp.sh",
    "evidence_chain.py", "gravitas_action.py", "gravitas_context.py",
    "gravitas_evidence.py", "gravitas_policy.py", "gravitas_repo.py",
    "gravitas_verify.py", "impact_graph.py", "init_session.py",
    "laya_gate.py", "ledger_add.py", "memory_sync.py",
    "post_invocation.py", "post_tool.py", "pre_tool.py",
    "repro_runner.py", "resume_session.py", "scan_skills.py",
    "session_context.py", "session_status.py", "stop_gate.py",
    "token_audit.py", "validator_runner.py"
)) {
    $oldPath = Join-Path $targetScripts $oldScript
    if (Test-Path $oldPath) { Remove-Item -Path $oldPath -Force -ErrorAction SilentlyContinue }
}
$srcScripts = Join-Path $repoRoot "scripts"
if (Test-Path $srcScripts) {
    Copy-Item -Path "$srcScripts\*" -Destination $targetScripts -Recurse -Force
    Write-Host "  -> Deployed runtime scripts (hooks/ & setup/)" -ForegroundColor Green
}

# Remove superseded legacy root config artifacts safely
foreach ($legacyFile in @("god_mode_mcp.py", "ANTIGRAVITY_SYSTEM_PROMPT.md", "GOD_MODE.md", "repomix.config.json", "cloudflare_mcp.py", "config.json")) {
    $legacyPath = Join-Path $geminiConfig $legacyFile
    if (Test-Path $legacyPath) { Remove-Item -Path $legacyPath -Force -ErrorAction SilentlyContinue }
}

$targetVault = Join-Path $geminiConfig "skills_vault"
$targetSkills = Join-Path $geminiConfig "skills"
if (Test-Path $targetSkills) { Remove-Item -Path $targetSkills -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force -Path $targetVault | Out-Null
New-Item -ItemType Directory -Force -Path $targetSkills | Out-Null
$srcSkills = Join-Path $repoRoot "skills"
$deployedSkillCount = 0
if (Test-Path $srcSkills) {
    $coreActive = @("elephant-goldfish-model", "code-execution-mcp", "skill-evaluator", "infinite-context-loop")
    $skillManifests = Get-ChildItem -Path $srcSkills -Filter "SKILL.md" -Recurse -File
    $deployedSkillCount = $skillManifests.Count
    $skillManifests | ForEach-Object {
        $skillDir = $_.Directory
        Copy-Item -Path $skillDir.FullName -Destination $targetVault -Recurse -Force
        if ($coreActive -contains $skillDir.Name) {
            Copy-Item -Path $skillDir.FullName -Destination $targetSkills -Recurse -Force
        }
    }
    Write-Host "  -> Deployed $deployedSkillCount skills to server-side skills_vault/ ($($coreActive.Count) core active)" -ForegroundColor Green
}

$targetAgents = Join-Path $geminiConfig "agents"
New-Item -ItemType Directory -Force -Path $targetAgents | Out-Null
$srcAgents = Join-Path $repoRoot "agents"
if (Test-Path $srcAgents) {
    Get-ChildItem -Path $srcAgents -Filter "*.md" -Recurse -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $targetAgents -Force
    }
    Write-Host "  -> Deployed categorized agents (flattened for native discovery)" -ForegroundColor Green
}

$targetRules = Join-Path $geminiConfig "rules"
New-Item -ItemType Directory -Force -Path $targetRules | Out-Null
$srcRules = Join-Path $repoRoot "rules"
if (Test-Path $srcRules) {
    Copy-Item -Path "$srcRules\*" -Destination $targetRules -Recurse -Force
    Write-Host "  -> Deployed unified rules" -ForegroundColor Green
}

$targetWorkflows = Join-Path $geminiConfig "workflows"
New-Item -ItemType Directory -Force -Path $targetWorkflows | Out-Null
$srcWorkflows = Join-Path $repoRoot "workflows"
if (Test-Path $srcWorkflows) {
    Copy-Item -Path "$srcWorkflows\*" -Destination $targetWorkflows -Recurse -Force
    Write-Host "  -> Deployed native workflows" -ForegroundColor Green
}

# Seed memory initialization (migrate legacy god_mode_mem0.json if present)
$seedMem = Join-Path $configDir "memory.json"
$legacyMem = Join-Path $geminiConfig "god_mode_mem0.json"
$targetMem = Join-Path $geminiConfig "memory.json"
if (-not (Test-Path $targetMem)) {
    if (Test-Path $legacyMem) {
        Move-Item -Path $legacyMem -Destination $targetMem -Force
        Write-Host "  -> Migrated god_mode_mem0.json -> memory.json" -ForegroundColor Green
    } elseif (Test-Path $seedMem) {
        Copy-Item -Path $seedMem -Destination $targetMem -Force
        Write-Host "  -> Initialized seed memory (memory.json)" -ForegroundColor Green
    }
} elseif (Test-Path $legacyMem) {
    Remove-Item -Path $legacyMem -Force -ErrorAction SilentlyContinue
}

# 5. Dynamically Generate & Deploy mcp_config.json (register only installed MCP servers)
Write-Host "`n[4/6] Registering God-Mode FastMCP Server..." -ForegroundColor Yellow
$mcpConfigPath = Join-Path $geminiConfig "mcp_config.json"
$mcpServers = [ordered]@{}
if (Test-Path $mcpConfigPath) {
    try {
        $prevCfg = [System.IO.File]::ReadAllText($mcpConfigPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json -AsHashtable
        if ($prevCfg -and $prevCfg.ContainsKey("mcpServers") -and $prevCfg["mcpServers"]) {
            foreach ($k in $prevCfg["mcpServers"].Keys) { $mcpServers[$k] = $prevCfg["mcpServers"][$k] }
        }
    } catch {}
}
$mcpServers["god-mode"] = [ordered]@{
    "command" = $pyResolved
    "args" = @((Join-Path $geminiMcpDir "server.py"))
}
$xerjCandidate = [System.IO.Path]::Combine($env:USERPROFILE, "scoop", "apps", "xerj", "current", "xerj.exe")
$xerjCmd = $null
if (Test-Path $xerjCandidate) { $xerjCmd = $xerjCandidate }
elseif (Get-Command "xerj" -ErrorAction SilentlyContinue) { $xerjCmd = (Get-Command "xerj").Source }
if ($xerjCmd) {
    $mcpServers["xerj"] = [ordered]@{ "command" = $xerjCmd; "args" = @("mcp") }
}
try {
    & $pyResolved -c "import mcptoon" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $mcpServers["mcptoon"] = [ordered]@{ "command" = $pyResolved; "args" = @("-m", "mcptoon", "serve", "--smart") }
    }
} catch {}

$mcpJsonContent = ([ordered]@{ "mcpServers" = $mcpServers }) | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($mcpConfigPath, $mcpJsonContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "  -> Registered mcp_config.json at $geminiConfig (god-mode + available tools only)" -ForegroundColor Green

# Deploy MCP Tool Schemas & IDE Settings
$schemasPayload = Join-Path $repoRoot "mcp\schemas"
if (Test-Path $schemasPayload) {
    New-Item -ItemType Directory -Force -Path $antigravityIdeMcp | Out-Null
    Copy-Item -Path (Join-Path $schemasPayload "*.json") -Destination $antigravityIdeMcp -Force
    New-Item -ItemType Directory -Force -Path $antigravityCliMcp | Out-Null
    Copy-Item -Path (Join-Path $schemasPayload "*.json") -Destination $antigravityCliMcp -Force
    Write-Host "  -> Deployed MCP tool schemas to Antigravity IDE & CLI" -ForegroundColor Green
}

# Configure Global IDE User Settings
$ideDirs = @(
    [System.IO.Path]::Combine($env:APPDATA, "Antigravity IDE", "User"),
    [System.IO.Path]::Combine($env:APPDATA, "Code", "User")
)
foreach ($ideSettingsDir in $ideDirs) {
    if (Test-Path (Split-Path -Parent $ideSettingsDir)) {
        try {
            New-Item -ItemType Directory -Force -Path $ideSettingsDir | Out-Null
            $ideSettingsPath = Join-Path $ideSettingsDir "settings.json"
            $cfgObj = @{}
            if (Test-Path $ideSettingsPath) {
                try {
                    $raw = [System.IO.File]::ReadAllText($ideSettingsPath, [System.Text.Encoding]::UTF8)
                    $cfgObj = $raw | ConvertFrom-Json -AsHashtable
                }
                catch { $cfgObj = @{} }
            }
            if (-not $cfgObj) { $cfgObj = @{} }
            if (-not $cfgObj.ContainsKey("files.exclude")) { $cfgObj["files.exclude"] = @{} }
            $cfgObj["python.defaultInterpreterPath"] = $pyResolved
            $cfgObj["python.languageServer"] = "Default"
            $cfgObj["files.exclude"]["**/.git"] = $true
            $cfgObj["files.exclude"]["**/.ruff_cache"] = $true
            $cfgObj["files.exclude"]["**/__pycache__"] = $true
            $cfgObj["files.exclude"]["**/*.pyc"] = $true

            $outJson = $cfgObj | ConvertTo-Json -Depth 10
            [System.IO.File]::WriteAllText($ideSettingsPath, $outJson, [System.Text.UTF8Encoding]::new($false))
            Write-Host "  -> Configured global IDE user settings at $ideSettingsPath" -ForegroundColor Green
        }
        catch {}
    }
}

# 5. Register Global FastMCP across Antigravity, VS Code, Cursor, Windsurf, Claude
Write-Host "`n[5/6] Registering Global MCP and Deploying Master Rules..." -ForegroundColor Yellow
$scriptsDir = Join-Path $repoRoot "scripts\setup"
$registerMcp = Join-Path $scriptsDir "register_mcp.ps1"
if (Test-Path $registerMcp) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $registerMcp
}

# 6. Verification & Health Doctor
Write-Host "`n[6/6] Verifying System Health..." -ForegroundColor Yellow
$doctorScript = Join-Path $scriptsDir "doctor.ps1"
if (Test-Path $doctorScript) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $doctorScript
}

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host "   Antigravity IDE & VS Code Setup Complete!                            " -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Ready to use in:" -ForegroundColor White
Write-Host "  1. Google Antigravity IDE - FastMCP server (9 upfront / 26 schema tools) & $deployedSkillCount skills active" -ForegroundColor Green
Write-Host "  2. VS Code / Cursor       - FastMCP server & Infinite-Horizon Context Engine active" -ForegroundColor Green
Write-Host "`nTo cleanly uninstall: .\installer\uninstall.ps1`n" -ForegroundColor DarkGray
