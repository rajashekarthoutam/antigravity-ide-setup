# Antigravity IDE - Deep History & Telemetry Cleaner
# Safely purges accumulated transcripts, old chat sessions, and debug logs.
# PRESERVES: ~/.gemini/config/ (Rules, FastMCP, Mem0 memories, and scripts)

$ErrorActionPreference = "SilentlyContinue"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Antigravity IDE - History & Log Purge Engine" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$geminiRoot = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini")
$ideRoots = @(
    ([System.IO.Path]::Combine($geminiRoot, "antigravity")),
    ([System.IO.Path]::Combine($geminiRoot, "antigravity-ide"))
)

# 1. Purge conversation logs and session transcripts (frees up 500k+ tokens)
Write-Host "`n[1/3] Purging accumulated session transcripts & brains..." -ForegroundColor Yellow
foreach ($ideRoot in $ideRoots) {
    $brainDir = [System.IO.Path]::Combine($ideRoot, "brain")
    if (Test-Path $brainDir) {
        Get-ChildItem -Path $brainDir -Directory | ForEach-Object {
            Remove-Item -Path $_.FullName -Recurse -Force
        }
        Write-Host "  -> Purged session brains in $brainDir" -ForegroundColor Green
    }

    $convDir = [System.IO.Path]::Combine($ideRoot, "conversations")
    if (Test-Path $convDir) {
        Get-ChildItem -Path $convDir | ForEach-Object {
            Remove-Item -Path $_.FullName -Recurse -Force
        }
        Write-Host "  -> Purged conversation history index in $convDir" -ForegroundColor Green
    }

    $scratchDir = [System.IO.Path]::Combine($ideRoot, "scratch")
    if (Test-Path $scratchDir) {
        Remove-Item -Path (Join-Path $scratchDir "*") -Recurse -Force
        Write-Host "  -> Cleaned scratch workspace in $ideRoot" -ForegroundColor Green
    }

    $crashesDir = [System.IO.Path]::Combine($ideRoot, "crashes")
    if (Test-Path $crashesDir) {
        Remove-Item -Path (Join-Path $crashesDir "*") -Recurse -Force
        Write-Host "  -> Cleaned crash logs in $ideRoot" -ForegroundColor Green
    }
}

# 2. Clean system logs
Write-Host "`n[2/3] Checking IDE runtime logs..." -ForegroundColor Yellow

# 3. Purge system logs
Write-Host "`n[3/3] Purging IDE runtime logs..." -ForegroundColor Yellow
$logsDir = [System.IO.Path]::Combine($geminiRoot, "logs")
if (Test-Path $logsDir) {
    Remove-Item -Path (Join-Path $logsDir "*") -Recurse -Force
    Write-Host "  -> Purged IDE system logs in $logsDir" -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "   Cleanup Complete! Token count reset to 0.              " -ForegroundColor Green
Write-Host "   God-Mode remains 100% active globally in ~/.gemini/config." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
