# Export God-Mode FastMCP configuration to VS Code, Cursor, and Claude Desktop
param(
    [string]$TargetDir = (Get-Location).Path,
    [switch]$Global
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$godModePy = Join-Path $repoRoot "mcp\server.py"
if (-not (Test-Path $godModePy)) {
    $godModePy = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "mcp", "server.py")
}

Write-Host "=== Antigravity MCP Bridge Generator ===" -ForegroundColor Cyan
Write-Host "Target: $TargetDir" -ForegroundColor DarkGray

$mcpConfig = @{
    "mcpServers" = @{
        "god-mode" = @{
            "command" = "python"
            "args" = @($godModePy)
            "env" = @{
                "PYTHONPATH" = "$repoRoot;$repoRoot\mcp"
            }
        }
    }
}

$jsonOutput = $mcpConfig | ConvertTo-Json -Depth 5

# 1. Project-level .vscode/mcp.json
$vscodeDir = Join-Path $TargetDir ".vscode"
if (!(Test-Path $vscodeDir)) {
    New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
}
$projectMcpJson = Join-Path $vscodeDir "mcp.json"
Set-Content -Path $projectMcpJson -Value $jsonOutput -Encoding UTF8
Write-Host " [OK] Created Project MCP config: $projectMcpJson" -ForegroundColor Green

# 2. Global Claude Desktop config if requested
if ($Global) {
    $claudeConfigDir = "$env:APPDATA\Claude"
    if (!(Test-Path $claudeConfigDir)) {
        New-Item -ItemType Directory -Path $claudeConfigDir -Force | Out-Null
    }
    $claudeJson = Join-Path $claudeConfigDir "claude_desktop_config.json"
    Set-Content -Path $claudeJson -Value $jsonOutput -Encoding UTF8
    Write-Host " [OK] Created Claude Desktop MCP config: $claudeJson" -ForegroundColor Green
}

Write-Host "`nGod-Mode FastMCP tools are now active in your editor!" -ForegroundColor Cyan
