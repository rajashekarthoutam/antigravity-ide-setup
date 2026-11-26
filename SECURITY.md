# Security Policy

## Security Boundaries & Supply-Chain Guardrails

- **SkillSpector (`verify_agent_skill`)**: Scans skill manifests and scripts (`.md`, `.py`, `.js`, `.ts`, `.mjs`, `.cjs`, `.rb`, `.sh`, `.ps1`, `.json`, `.yaml`) for prompt injections, remote shell pipes, method-free `eval`/`exec`, credential exposure, memory poisoning, and hidden zero-width steganography.
- **Model Armor (`redact_secrets` / `model_armor_sanitize`)**: Redacts API keys, tokens, and private keys before persisting data into `ContextVirtualizer` (`context_vault.db`) or diagnostic logs.
- **Gravitas PreToolUse / Policy Gate**: Enforces quote-aware shell classification (preserving command substitution detection inside double quotes and failing closed on unclosed quotes), workspace-contained path scoping, read-before-write enforcement, and duplicate-failure prevention.

## Reporting a Vulnerability

Do not open public issues for undisclosed credentials or security bypasses. Sanitize test artifacts and report reproducible details privately to the repository maintainer with steps to verify and mitigate.
