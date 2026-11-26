---
name: agent-desktop
description: Operates and inspects Windows desktop applications through native UI Automation (UIA) accessibility trees using Vercel Labs open-source agent-desktop. Inspects open windows, finds buttons/inputs, sets values, clicks, and sends keystrokes.
---

# Agent Desktop Skill (Vercel Labs)

This skill enables Antigravity to observe and interact with desktop GUI applications on Windows through the native operating system accessibility tree (UI Automation) via the `agent-desktop` CLI.

## Binary Location & PATH
- The executable is installed globally under `%USERPROFILE%\scoop\shims\agent-desktop.exe` (or `~/.local/bin/agent-desktop`).
- It is available directly in PATH as `agent-desktop`.
- Active security guardrail: `agent-desktop-guard.cmd` / `agent-desktop-guard.ps1`.

## Security Guardrails & Protected Applications (NeMo / Model Armor Enforced)
All `agent-desktop` executions are intercepted and validated by the security guardrail:
1. **Blacklisted Target Applications (STRICTLY BLOCKED)**:
   - **Web Browsers**: Chrome, Edge, Firefox, Brave, Opera, Vivaldi (protecting Google accounts, active sessions, and web logins).
   - **Password Managers**: Bitwarden, 1Password, KeePass, LastPass, Dashlane, Enpass.
   - **Authentication & System Dialogs**: CredentialUIBroker, Windows Security, Consent (UAC), Regedit.
   - **Private Messaging**: WhatsApp, Telegram, Signal, Outlook, Thunderbird, Slack, Discord.
2. **Blocked Keystroke & Input Patterns**:
   - High-risk system shortcuts (`Win+R`, `Win+X`, `Ctrl+Alt+Del`, `Win+L`, `Alt+F4`).
   - Credential injections: Typing raw API keys, bearer tokens, or secrets is automatically blocked.
3. **Immutable Audit Logging**:
   - Every invocation attempt is timestamped and recorded in `~/.gemini/config/agent_desktop_audit.log`.

## Key Advantages
- **No Vision Token Cost**: Reads structured JSON trees instead of sending multi-megabyte screenshots to the LLM.
- **Stable Element References (`@refs`)**: Uses deterministic IDs (e.g. `'@s8f3k2p9:e1'`) rather than fragile pixel coordinates.
- **Headless by Default**: Interacts with applications semantically in the background without stealing focus or moving the physical mouse.

## Windows PowerShell Guidelines
- **Always quote refs in PowerShell**: Because `@` is the PowerShell splatting operator, always quote refs (e.g., `'@s8f3k2p9:e5'`).
- **Use `--headed` only when physical input is required**: By default, commands are headless. Use `--headed` when you need physical keyboard typing (`type`), double clicks, or drag actions.

## Common Workflows

### 1. Check System Status & Permissions
```powershell
agent-desktop status
```

### 2. Snapshot an Application UI Tree
```powershell
# Snapshot a specific application (e.g. Word, Notepad, File Explorer)
agent-desktop snapshot --app "Word" -i --compact

# Snapshot with a skeleton view for large apps
agent-desktop snapshot --app "Notepad" --skeleton -i --compact
```

### 3. Drill Down into a Subtree
```powershell
agent-desktop snapshot --root '@s8f3k2p9:e3' -i --compact
```

### 4. Click an Element or Set Text
```powershell
# Click a button using its qualified ref
agent-desktop click '@s8f3k2p9:e5'

# Set value into a text field semantically
agent-desktop set-value '@s8f3k2p9:e8' "New text value"
```

### 5. Send Keyboard Shortcuts
```powershell
# Send standard key combinations
agent-desktop press ctrl+s
agent-desktop press enter
agent-desktop press esc
```

### 6. Window Management
```powershell
# List open GUI applications and windows
agent-desktop list-apps
agent-desktop list-windows

# Manage window state
agent-desktop focus-window --app "Word"
agent-desktop restore --app "Word"
```

