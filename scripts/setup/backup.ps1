# God-Mode Universal Backup Engine for Antigravity IDE
# Captures live ecosystem: global configs, rules, skills, scripts, and schemas into root repository layout

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   God-Mode Antigravity IDE Backup Engine" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $repoRoot "skills"))) {
    $repoRoot = $PSScriptRoot
}

$geminiConfig = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config")
$antigravityIdeMcp = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "antigravity-ide", "mcp", "god-mode")

# 1. Backup Global Configs from ~/.gemini/config to repository
Write-Host "`n[1/4] Backing up global configurations from $geminiConfig..." -ForegroundColor Yellow
$coreAgents = Join-Path $geminiConfig "AGENTS.md"
if (Test-Path $coreAgents) {
    Copy-Item -Path $coreAgents -Destination $repoRoot -Force
    Write-Host "  -> Backed up AGENTS.md to root" -ForegroundColor Green
}
$mcpSrcDir = Join-Path $geminiConfig "mcp"
$mcpSrcLegacy = Join-Path $geminiConfig "server.py"
$mcpDir = Join-Path $repoRoot "mcp"
New-Item -ItemType Directory -Force -Path $mcpDir | Out-Null
if (Test-Path $mcpSrcDir) {
    Copy-Item -Path "$mcpSrcDir\*" -Destination $mcpDir -Recurse -Force -Exclude @("__pycache__", ".ruff_cache")
    Write-Host "  -> Backed up mcp\ engine directory" -ForegroundColor Green
} elseif (Test-Path $mcpSrcLegacy) {
    Copy-Item -Path $mcpSrcLegacy -Destination (Join-Path $mcpDir "server.py") -Force
    Write-Host "  -> Backed up server.py to mcp\" -ForegroundColor Green
}

$configDir = Join-Path $repoRoot "config"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
foreach ($item in @("runtime.json", "hooks.json", "repomix.json", "ruff.toml", "memory.json", "system_prompt.md")) {
    $src = Join-Path $geminiConfig $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $configDir -Force
        Write-Host "  -> Backed up $item to config\" -ForegroundColor Green
    }
}
$godModeSrc = Join-Path $geminiConfig "RUNTIME_GUIDE.md"
if (Test-Path $godModeSrc) {
    Copy-Item -Path $godModeSrc -Destination (Join-Path $repoRoot "docs\RUNTIME_GUIDE.md") -Force
    Write-Host "  -> Backed up RUNTIME_GUIDE.md to docs\" -ForegroundColor Green
}

# 2. Backup scripts
if (Test-Path (Join-Path $geminiConfig "scripts")) {
    $targetScripts = Join-Path $repoRoot "scripts"
    New-Item -ItemType Directory -Force -Path $targetScripts | Out-Null
    Copy-Item -Path (Join-Path $geminiConfig "scripts\*") -Destination $targetScripts -Recurse -Force -Exclude "__pycache__"
    Write-Host "  -> Backed up global scripts (Laya, Mem0, token audit)" -ForegroundColor Green
}

# 3. Backup skills, agents, rules, workflows
Write-Host "`n[2/4] Backing up skills, agents, rules, workflows..." -ForegroundColor Yellow
$subdirs = @("skills", "agents", "rules", "workflows")
foreach ($sd in $subdirs) {
    $srcDir = Join-Path $geminiConfig $sd
    $targetDir = Join-Path $repoRoot $sd
    if (Test-Path $srcDir) {
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Copy-Item -Path "$srcDir\*" -Destination $targetDir -Recurse -Force
        Write-Host "  -> Backed up $sd" -ForegroundColor Green
    }
}

# Export clean base seed memory
$memSource = Join-Path $geminiConfig "memory.json"
$memDest = Join-Path $configDir "memory.json"
if (Test-Path $memSource) {
    try {
        $memData = Get-Content $memSource -Raw -Encoding UTF8 | ConvertFrom-Json
        $cleanMemories = @()
        foreach ($m in $memData.memories) {
            $m.user_id = "default"
            $cleanMemories += $m
        }
        $cleanObj = @{ memories = $cleanMemories }
        $jsonStr = $cleanObj | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($memDest, $jsonStr, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  -> Backed up sanitized seed memories (memory.json)" -ForegroundColor Green
    } catch {
        Copy-Item -Path $memSource -Destination $memDest -Force
    }
}

# 4. Backup Active Antigravity IDE MCP Tool Schemas
Write-Host "`n[3/4] Backing up active MCP tool schemas from $antigravityIdeMcp..." -ForegroundColor Yellow
$targetSchemas = Join-Path $repoRoot "mcp\schemas"
New-Item -ItemType Directory -Force -Path $targetSchemas | Out-Null
if (Test-Path $antigravityIdeMcp) {
    Get-ChildItem -Path $antigravityIdeMcp -Filter "*.json" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $targetSchemas -Force
        Write-Host "  -> Backed up schema: $($_.Name)" -ForegroundColor Green
    }
}

# 5. Create Standalone Distribution Archive
Write-Host "`n[4/4] Generating standalone god-mode-dist.zip..." -ForegroundColor Yellow
$distDir = Join-Path $repoRoot "dist"
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$zipOutput = Join-Path $distDir "god-mode-dist.zip"
if (Test-Path $zipOutput) { Remove-Item -Path $zipOutput -Force }

$tempDist = Join-Path ([System.IO.Path]::GetTempPath()) "god_mode_dist_$(Get-Random)"
New-Item -ItemType Directory -Force -Path $tempDist | Out-Null
try {
    foreach ($sd in @("skills", "agents", "rules", "workflows", "scripts", "schemas", "docs", "installer", "mcp", "config")) {
        $dirPath = Join-Path $repoRoot $sd
        if (Test-Path $dirPath) {
            Copy-Item -Path $dirPath -Destination (Join-Path $tempDist $sd) -Recurse -Force -Exclude @("__pycache__", ".ruff_cache")
        }
    }
    foreach ($fn in @("AGENTS.md", "README.md", "LICENSE", ".gitignore")) {
        $filePath = Join-Path $repoRoot $fn
        if (Test-Path $filePath) {
            Copy-Item -Path $filePath -Destination (Join-Path $tempDist $fn) -Force
        }
    }

    if (Get-Command "7z" -ErrorAction SilentlyContinue) {
        & 7z a -tzip -y $zipOutput "$tempDist\*" | Out-Null
    } else {
        Compress-Archive -Path (Join-Path $tempDist "*") -DestinationPath $zipOutput -Force
    }
    Write-Host "  -> Built distribution archive: god-mode-dist.zip" -ForegroundColor Green
} finally {
    if (Test-Path $tempDist) {
        Remove-Item -Path $tempDist -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "   God-Mode Backup Complete! Ready for Universal Deploy   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
