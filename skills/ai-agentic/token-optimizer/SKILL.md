---
name: token-optimizer
description: Analyzes repository token distribution, packs codebases with Tree-sitter compression, and audits context usage to achieve maximum token efficiency.
---

# Token Optimizer Skill

This skill provides procedures and commands to measure, compress, and budget token consumption for any codebase.

## Core Capabilities

### 1. Codebase Token Usage Audit
Identify token-heavy files, bloated assets, and dependencies:
```powershell
npx -y repomix --token-count-tree
```
Use the output to immediately add bloated directories (build artifacts, static assets, vendor files) to `.gitignore` or `.repomixignore`.

### 2. Compressed Codebase Snapshot (Tree-sitter AST)
Generate an ultra-compact codebase representation that strips function bodies and keeps only type signatures, classes, and exported interfaces:
```powershell
npx -y repomix --compress --style xml
```
This typically reduces repository token size by 75% to 90% compared to raw file ingestion.

### 3. Budgeted Context Packing
Pack only up to a strict token limit (e.g. 5,000 tokens):
```powershell
npx -y repomix --compress --token-budget 5000
```

### 4. Interactive MCP Mode
Run Repomix as a Model Context Protocol server so agents can query compressed file trees on demand:
```powershell
npx -y repomix --mcp
```
