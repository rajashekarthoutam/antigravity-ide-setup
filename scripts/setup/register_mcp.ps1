# Universal Global MCP Registrar for All Editors & AI Assistants
# Registers God-Mode FastMCP server globally across:
# 1. Google Antigravity IDE & Antigravity CLI
# 2. DeepSeek Harness (dsh)
# 3. VS Code (Cline, Roo-Code, Native MCP)
# 4. Cursor IDE
# 5. Windsurf (Codeium)
# 6. Claude Desktop

$ErrorActionPreference = 'Continue'

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$deployedPy = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "mcp", "server.py")
$godModePy = if (Test-Path $deployedPy) { $deployedPy } else { Join-Path $repoRoot "mcp\server.py" }

$pyCmd = "python"

Write-Host "`n=== Universal Global MCP Registrar ===" -ForegroundColor Cyan
Write-Host "Server: $godModePy`n" -ForegroundColor DarkGray

$mcpDir = Split-Path -Parent $godModePy
$mcpServerDefinition = @{
    "command" = $pyCmd
    "args" = @($godModePy)
    "env" = @{
        "PYTHONPATH" = "$mcpDir;$repoRoot;$env:USERPROFILE\.gemini\config"
    }
}

function Register-McpTarget {
    param([string]$Name, [string]$Path, [string]$Key = "mcpServers")
    try {
        $parent = Split-Path -Parent $Path
        if (!(Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        $existing = @{}
        if (Test-Path $Path) {
            try {
                $raw = Get-Content $Path -Raw -Encoding UTF8
                $existing = $raw | ConvertFrom-Json -AsHashtable
            } catch { $existing = @{} }
        }
        if (-not $existing) { $existing = @{} }
        if (-not $existing.ContainsKey($Key)) { $existing[$Key] = @{} }
        $existing[$Key]["god-mode"] = $mcpServerDefinition

        $jsonOut = $existing | ConvertTo-Json -Depth 6
        [System.IO.File]::WriteAllText($Path, $jsonOut, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  [OK]   $Name -> $Path" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Failed to configure $Name : $_" -ForegroundColor Yellow
    }
}

# 1. Antigravity IDE & CLI
$antigravityConfig = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "mcp_config.json")
Register-McpTarget "Google Antigravity Global" $antigravityConfig "mcpServers"

# 2. DeepSeek Harness (dsh) God-Mode Profile
$dshProfile = [System.IO.Path]::Combine($env:USERPROFILE, ".dsh", "profiles", "god-mode", "runtime.json")
Register-McpTarget "DeepSeek Harness Profile" $dshProfile "mcpServers"

# 3. VS Code Native Copilot MCP + Cline & Roo-Code Global Storage
$vsCodeNativeMcp = [System.IO.Path]::Combine($env:APPDATA, "Code", "User", "mcp.json")
Register-McpTarget "VS Code Native (Copilot Agent)" $vsCodeNativeMcp "servers"

$rooClineMcp = [System.IO.Path]::Combine($env:APPDATA, "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings", "cline_mcp_settings.json")
Register-McpTarget "VS Code (Roo-Code)" $rooClineMcp "mcpServers"

$claudeDevMcp = [System.IO.Path]::Combine($env:APPDATA, "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")
Register-McpTarget "VS Code (Cline)" $claudeDevMcp "mcpServers"

# 4. Cursor IDE
$cursorMcp = [System.IO.Path]::Combine($env:USERPROFILE, ".cursor", "mcp.json")
Register-McpTarget "Cursor IDE" $cursorMcp "mcpServers"

# 5. Windsurf (Codeium)
$windsurfMcp = [System.IO.Path]::Combine($env:USERPROFILE, ".codeium", "windsurf", "mcp_config.json")
Register-McpTarget "Windsurf IDE" $windsurfMcp "mcpServers"

# 6. Claude Desktop
$claudeDesktop = [System.IO.Path]::Combine($env:APPDATA, "Claude", "claude_desktop_config.json")
Register-McpTarget "Claude Desktop" $claudeDesktop "mcpServers"

# 7. Deploy Universal Antigravity System Prompts & Agent Rules Globally
Write-Host "`nDeploying Universal Antigravity Rules & Identity..." -ForegroundColor Yellow
$masterPrompt = Join-Path $repoRoot "AGENTS.md"
if (-not (Test-Path $masterPrompt)) {
    $masterPrompt = Join-Path $repoRoot "config\system_prompt.md"
}
if (Test-Path $masterPrompt) {
    # VS Code Copilot Global Instructions
    $vsCodePromptsDir = [System.IO.Path]::Combine($env:APPDATA, "Code", "User", "prompts")
    New-Item -ItemType Directory -Path $vsCodePromptsDir -Force | Out-Null
    Copy-Item -Path $masterPrompt -Destination (Join-Path $vsCodePromptsDir "god-mode.instructions.md") -Force
    Write-Host "  [OK]   VS Code Global Instructions -> $vsCodePromptsDir\god-mode.instructions.md" -ForegroundColor Green

    # DeepSeek Harness Profile System Prompt
    $dshPrompt = [System.IO.Path]::Combine($env:USERPROFILE, ".dsh", "profiles", "god-mode", "system_prompt.md")
    New-Item -ItemType Directory -Path (Split-Path -Parent $dshPrompt) -Force | Out-Null
    Copy-Item -Path $masterPrompt -Destination $dshPrompt -Force
    Write-Host "  [OK]   DeepSeek Harness System Prompt -> $dshPrompt" -ForegroundColor Green

    # Global Cursor Rules
    $cursorRulesDir = [System.IO.Path]::Combine($env:USERPROFILE, ".cursor", "rules")
    New-Item -ItemType Directory -Path $cursorRulesDir -Force | Out-Null
    Copy-Item -Path $masterPrompt -Destination (Join-Path $cursorRulesDir "antigravity.mdc") -Force
    Write-Host "  [OK]   Global Cursor Rules -> $cursorRulesDir\antigravity.mdc" -ForegroundColor Green

    # Claude Code Global CLAUDE.md
    $claudeGlobalDir = [System.IO.Path]::Combine($env:USERPROFILE, ".claude")
    New-Item -ItemType Directory -Path $claudeGlobalDir -Force | Out-Null
    Copy-Item -Path $masterPrompt -Destination (Join-Path $claudeGlobalDir "CLAUDE.md") -Force
    Write-Host "  [OK]   Claude Code Global Memory -> $claudeGlobalDir\CLAUDE.md" -ForegroundColor Green
}

Write-Host "`nGod-Mode FastMCP & Antigravity Rules are now globally active for Antigravity, DeepSeek Harness, and all AI editors!`n" -ForegroundColor Cyan
