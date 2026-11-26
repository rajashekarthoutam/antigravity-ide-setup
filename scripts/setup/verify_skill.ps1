param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$SkillPath = "."
)

$ErrorActionPreference = 'Continue'

Write-Host "`n=== NVIDIA SkillSpector AI Skill Security Validator ===" -ForegroundColor Cyan
Write-Host "Target: $SkillPath`n" -ForegroundColor DarkGray

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

$verifyScript = @"
import sys, json, os
from pathlib import Path

candidates = [
    os.path.join(r'$repoRoot', 'mcp'),
    os.path.expanduser(r'~/.gemini/config/mcp'),
    os.path.expanduser(r'~/.gemini/config'),
]
for c in candidates:
    if os.path.exists(c) and c not in sys.path:
        sys.path.insert(0, c)

from server import verify_agent_skill

res = verify_agent_skill(r'$SkillPath')
print(json.dumps(res))
"@

$resultJson = python -c "$verifyScript" 2>&1

try {
    $res = $resultJson | ConvertFrom-Json
} catch {
    Write-Host "[FAIL] Error invoking SkillSpector: $resultJson" -ForegroundColor Red
    exit 1
}

if ($res.verdict -eq 'VERIFIED_SAFE') {
    Write-Host "  Verdict:     " -NoNewline
    Write-Host "[VERIFIED SAFE]" -ForegroundColor Green -NoNewline
    Write-Host " (Trust Score: $($res.trust_score)/100)" -ForegroundColor White
} elseif ($res.verdict -eq 'WARNING_FLAGGED') {
    Write-Host "  Verdict:     " -NoNewline
    Write-Host "[WARNING FLAGGED]" -ForegroundColor Yellow -NoNewline
    Write-Host " (Trust Score: $($res.trust_score)/100)" -ForegroundColor White
} else {
    Write-Host "  Verdict:     " -NoNewline
    Write-Host "[MALICIOUS REJECTED]" -ForegroundColor Red -NoNewline
    Write-Host " (Trust Score: $($res.trust_score)/100)" -ForegroundColor White
}

Write-Host "  Summary:     $($res.summary)" -ForegroundColor DarkGray
Write-Host "  Scanned:     $($res.files_scanned) file(s)" -ForegroundColor DarkGray
Write-Host "  Findings:    $($res.critical_count) critical, $($res.high_count) high ($($res.total_findings) total)`n" -ForegroundColor DarkGray

if ($res.findings.Count -gt 0) {
    Write-Host "Security Findings:" -ForegroundColor Yellow
    foreach ($f in $res.findings) {
        $color = if ($f.severity -eq 'CRITICAL') { 'Red' } else { 'Yellow' }
        Write-Host "  - [$($f.severity)] " -ForegroundColor $color -NoNewline
        Write-Host "$($f.file):$($f.line) " -ForegroundColor White -NoNewline
        Write-Host "- $($f.issue)" -ForegroundColor DarkGray
        Write-Host "    Code: $($f.snippet)" -ForegroundColor DarkGray
    }
    Write-Host ""
}

if ($res.verdict -eq 'MALICIOUS_REJECTED') {
    Write-Host "BLOCKED: Skill installation prohibited by NVIDIA SkillSpector policy.`n" -ForegroundColor Red
    exit 1
} else {
    Write-Host "PASS: Skill eligible for installation in .skills_vault/.`n" -ForegroundColor Green
    exit 0
}
