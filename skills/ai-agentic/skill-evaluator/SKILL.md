---
name: skill-evaluator
description: "Deterministic Skill Evaluator for auditing, grading (0-100 / A-F), and improving Antigravity skills across frontmatter triggers, token economy, actionability, and supply-chain security. Use when creating, reviewing, or auditing any SKILL.md package."
---

# Skill Evaluator

Deterministically grade and harden any skill before accepting it into the repository or `~/.gemini/config/skills/`.

## Evaluation Rubric (100 Points)

1. **YAML Frontmatter & Trigger Clarity (25 pts)**: Valid `name` and `description` with explicit `Use when...` activation triggers.
2. **Token Economy & Progressive Disclosure (25 pts)**: `SKILL.md` under 1,500 tokens via `tiktoken`, offloading bulky docs/scripts to `references/` and `scripts/`.
3. **Actionability & Verification Steps (20 pts)**: Concrete numbered steps, executable commands, and deterministic verification criteria.
4. **Security & Supply-Chain Safety (20 pts)**: Zero prompt injections, tool poisoning, or unsafe shell patterns via `verify_agent_skill`.
5. **Structure & Organization (10 pts)**: Clean Markdown headings and zero redundant boilerplate.

## Procedure

1. Run `evaluate_skill("<skill_name_or_path>")` via the `god-mode` FastMCP server.
2. Inspect `breakdown` and `recommendations` in the JSON report.
3. Fix any security findings (`status != PASS`) immediately; refactor skills scoring `< 80` (Grade `< B`).
4. Re-run `evaluate_skill()` and verify score >= 85 before committing.
