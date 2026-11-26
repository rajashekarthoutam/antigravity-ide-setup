# Antigravity IDE & VS Code FastMCP Suite Uninstaller
# Cleanly removes FastMCP registrations, editor configs, and deployed components.

param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Red
Write-Host "   Antigravity IDE & VS Code Suite Uninstaller            " -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red

if (-not $Force) {
    Write-Host "`nThis will remove:" -ForegroundColor Yellow
    Write-Host "  - Global FastMCP server registration in Antigravity IDE & CLI"
    Write-Host "  - Global MCP configs in VS Code (Roo/Cline), Cursor, Windsurf, Claude"
    Write-Host "  - Deployed skills, agents, rules, and workflows in ~/.gemini/config"
    Write-Host "  - Your personal workspace repositories and code will NOT be touched.`n"

    $confirm = Read-Host "Are you sure you want to proceed with uninstallation? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Uninstallation canceled." -ForegroundColor Cyan
        exit 0
    }
}

Write-Host "`n[1/4] Removing FastMCP schemas & configurations..." -ForegroundColor Yellow
$geminiRoot = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini")
$antigravityIdeMcp = Join-Path $geminiRoot "antigravity-ide\mcp\god-mode"
$antigravityCliMcp = Join-Path $geminiRoot "antigravity\mcp\god-mode"
$geminiMcpJson = Join-Path $geminiRoot "config\mcp_config.json"

if (Test-Path $antigravityIdeMcp) { Remove-Item -Path $antigravityIdeMcp -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $antigravityCliMcp) { Remove-Item -Path $antigravityCliMcp -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $geminiMcpJson) { Remove-Item -Path $geminiMcpJson -Force -ErrorAction SilentlyContinue }
Write-Host "  [OK] Cleaned Antigravity IDE & CLI registrations" -ForegroundColor Green

Write-Host "`n[2/4] Cleaning Global Editor MCP Configurations..." -ForegroundColor Yellow
function Remove-McpServerEntry {
    param([string]$Path, [string]$ServerName = "god-mode")
    if (Test-Path $Path) {
        try {
            $raw = Get-Content $Path -Raw -Encoding UTF8
            $obj = $raw | ConvertFrom-Json -AsHashtable
            if ($obj -and $obj.ContainsKey("mcpServers") -and $obj["mcpServers"].ContainsKey($ServerName)) {
                $obj["mcpServers"].Remove($ServerName)
                $outJson = $obj | ConvertTo-Json -Depth 6
                [System.IO.File]::WriteAllText($Path, $outJson, [System.Text.UTF8Encoding]::new($false))
                Write-Host "  [OK] Unregistered '$ServerName' from $Path" -ForegroundColor Green
            }
        } catch {}
    }
}

# VS Code Roo & Cline
Remove-McpServerEntry ([System.IO.Path]::Combine($env:APPDATA, "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings", "cline_mcp_settings.json"))
Remove-McpServerEntry ([System.IO.Path]::Combine($env:APPDATA, "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json"))
# Cursor & Windsurf & Claude
Remove-McpServerEntry ([System.IO.Path]::Combine($env:USERPROFILE, ".cursor", "mcp.json"))
Remove-McpServerEntry ([System.IO.Path]::Combine($env:USERPROFILE, ".codeium", "windsurf", "mcp_config.json"))
Remove-McpServerEntry ([System.IO.Path]::Combine($env:APPDATA, "Claude", "claude_desktop_config.json"))

Write-Host "`n[3/4] Removing Global Editor Rules & Prompts..." -ForegroundColor Yellow
$cursorRulesFile = [System.IO.Path]::Combine($env:USERPROFILE, ".cursor", "rules", "antigravity.mdc")
$claudeMdFile = [System.IO.Path]::Combine($env:USERPROFILE, ".claude", "CLAUDE.md")
if (Test-Path $cursorRulesFile) { Remove-Item -Path $cursorRulesFile -Force -ErrorAction SilentlyContinue }
if (Test-Path $claudeMdFile) { Remove-Item -Path $claudeMdFile -Force -ErrorAction SilentlyContinue }
Write-Host "  [OK] Cleaned global editor rule files" -ForegroundColor Green

Write-Host "`n[4/4] Cleaning Deployed Customizations in ~/.gemini/config..." -ForegroundColor Yellow
$geminiConfig = Join-Path $geminiRoot "config"
if (Test-Path $geminiConfig) {
    foreach ($item in @("server.py", "repomix.json", "ruff.toml", "context_vault.db", "context_vault.db-wal", "context_vault.db-shm")) {
        $p = Join-Path $geminiConfig $item
        if (Test-Path $p) { Remove-Item -Path $p -Force -ErrorAction SilentlyContinue }
    }
    foreach ($dir in @("mcp", "skills_vault")) {
        $dp = Join-Path $geminiConfig $dir
        if (Test-Path $dp) { Remove-Item -Path $dp -Recurse -Force -ErrorAction SilentlyContinue }
    }
    Write-Host "  [OK] Cleaned deployed configuration files & MCP modules" -ForegroundColor Green
}

# Clean any lingering CLI shims
$shimsDir = [System.IO.Path]::Combine($env:USERPROFILE, "scoop", "shims")
$shimsToRemove = @("agy.cmd", "dsh.cmd", "agy-doctor.cmd", "agy-doctor.ps1", "agy-verify-skill.cmd", "agy-verify-skill.ps1")
foreach ($shim in $shimsToRemove) {
    $targetShim = Join-Path $shimsDir $shim
    if (Test-Path $targetShim) {
        Remove-Item -Path $targetShim -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   Uninstallation Complete! System Restored Cleanly.     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
