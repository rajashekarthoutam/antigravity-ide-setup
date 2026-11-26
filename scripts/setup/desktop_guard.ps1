# Antigravity Secure Desktop Automation Guardrail (NeMo / Model Armor Enforcement)
# Intercepts all agent-desktop invocations to prevent unauthorized access, credential theft, and prompt hijacking.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
$auditLog = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "agent_desktop_audit.log")

# 1. Protected Application Blacklist (Browsers, Password Managers, Auth Dialogs, Messaging)
$blockedApps = @(
    'chrome', 'google chrome', 'msedge', 'microsoft edge', 'firefox', 'brave', 'opera', 'vivaldi', 'tor',
    'bitwarden', '1password', 'keepass', 'lastpass', 'dashlane', 'enpass',
    'credentialuibroker', 'consent', 'windows security', 'secpol', 'regedit',
    'whatsapp', 'telegram', 'signal', 'outlook', 'thunderbird', 'slack', 'discord'
)

# 2. Blocked Keystroke & Input Patterns
$blockedKeyPatterns = @(
    'win\+r', 'win\+x', 'ctrl\+alt\+del', 'win\+l', 'alt\+f4'
)

$rawArgs = $Arguments -join ' '
$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

# Check Target App / Window against Blacklist
foreach ($blocked in $blockedApps) {
    if ($rawArgs -match "(?i)(?:--app|-a|--window)\s*[`"']?.*$blocked.*[`"']?") {
        $logEntry = "[$timestamp] [BLOCKED] Target app matches security blacklist: $blocked | Args: $rawArgs"
        Add-Content -Path $auditLog -Value $logEntry -Encoding utf8
        Write-Host "`n[SECURITY GUARD]: Desktop automation targeting '$blocked' is strictly BLOCKED by Antigravity Security Policy." -ForegroundColor Red
        Write-Host "Reason: Web browsers, password managers, and authentication dialogs are protected from agent inspection to prevent data leakage.`n" -ForegroundColor Yellow
        exit 1
    }
}

# Check Keystrokes & Values against High-Risk Patterns
foreach ($pat in $blockedKeyPatterns) {
    if ($rawArgs -match "(?i)$pat") {
        $logEntry = "[$timestamp] [BLOCKED] Dangerous keystroke sequence: $pat | Args: $rawArgs"
        Add-Content -Path $auditLog -Value $logEntry -Encoding utf8
        Write-Host "`n[SECURITY GUARD]: Keystroke combination '$pat' is strictly BLOCKED by Antigravity Security Policy." -ForegroundColor Red
        Write-Host "Reason: High-risk system shortcuts cannot be triggered by automated agents.`n" -ForegroundColor Yellow
        exit 1
    }
}

# Check for Credential / Token Leaks in set-value or type
if ($rawArgs -match "(?i)(?:ghp_[A-Za-z0-9]{36}|AIzaSy[A-Za-z0-9_-]{33}|bearer\s+[A-Za-z0-9_\-\.]{20,})") {
    $logEntry = "[$timestamp] [BLOCKED] Potential credential injection detected in input value"
    Add-Content -Path $auditLog -Value $logEntry -Encoding utf8
    Write-Host "`n[SECURITY GUARD]: Credential injection blocked. Raw secrets cannot be typed or set into desktop fields.`n" -ForegroundColor Red
    exit 1
}

# 3. Locate Real Binary
$realBin = [System.IO.Path]::Combine($env:USERPROFILE, "scoop", "persist", "bun", "bin", "agent-desktop.exe")
if (-not (Test-Path $realBin)) {
    $cmdFound = Get-Command agent-desktop.exe -ErrorAction SilentlyContinue
    if ($cmdFound) { $realBin = $cmdFound.Source }
}

if (-not (Test-Path $realBin)) {
    Write-Host "[ERROR] Could not locate underlying agent-desktop.exe binary." -ForegroundColor Red
    exit 1
}

# 4. Log Approved Action and Execute
$logEntry = "[$timestamp] [ALLOWED] Args: $rawArgs"
Add-Content -Path $auditLog -Value $logEntry -Encoding utf8

& $realBin @Arguments
exit $LASTEXITCODE
