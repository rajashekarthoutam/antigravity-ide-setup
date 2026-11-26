---
name: skillspector
description: "Audits AI agent skills, prompts, and MCP configurations using NVIDIA SkillSpector. Detects prompt injections, tool poisoning, privilege escalation, data leaks, and supply chain risks."
---

# NVIDIA SkillSpector Security Scanner

Audits agent skills, prompt instructions, and Model Context Protocol (MCP) tool configurations before installation or activation.

## When to Use
- Before activating new third-party skills or tools in Antigravity or Claude Code.
- Auditing local skills for prompt injection, sensitive data leakage, or unsafe subprocess calls.
- Validating MCP tool schemas for tool poisoning or privilege escalation.

## CLI Usage
- **Fast Static Scan (Local):**
  ```bash
  skillspector scan <path-to-skill> --no-llm
  ```
- **Recursive Scan Across Skills Directory:**
  ```bash
  skillspector scan ~/.gemini/config/skills --recursive --no-llm
  ```
- **JSON / SARIF Report Generation:**
  ```bash
  skillspector scan <path-to-skill> --format json --output audit_report.json
  ```
- **MCP Registry Audit:**
  ```bash
  skillspector scan <path-to-mcp-schema> --mcp-registry
  ```
