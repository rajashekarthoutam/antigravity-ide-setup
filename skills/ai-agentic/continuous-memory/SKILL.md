---
name: continuous-memory
description: Manages persistent cross-session memory, records architectural decisions, anti-patterns, and project facts, decoupling state from conversational context.
---

# Continuous Memory & Self-Learning Skill

Use this skill to decouple conversation history from project knowledge. It ensures the assistant retains memory across sessions with zero context bloat.

## Workflow

### 1. After Solving a Complex Bug or Architecture Problem
Instead of letting the solution get lost when the chat closes, persist it:
1. Append the gotcha and solution to `.agents/memory/anti_patterns.md`.
2. Recommend the user trigger `/learn` in chat to automatically persist key takeaways into Antigravity Knowledge Items (`<appDataDir>\knowledge`).

### 2. Session Initialization (Zero Bloat)
When starting a new session:
1. Read only `.agents/memory/project_brief.md` (under 30 lines) to ground context.
2. Query the memory MCP server (`search_nodes` or `search_entities`) if specific historical facts or past decisions are needed.
3. Do NOT load old chat transcripts or massive historical logs.

### 3. File Structure
Every workspace should have:
- `.agents/memory/project_brief.md`: One-page architectural blueprint, key modules, and tech stack.
- `.agents/memory/anti_patterns.md`: Solved traps, bugs, library quirks, and forbidden patterns.
- `.agents/memory/decisions.md`: Architecture Decision Records (ADRs) with rationale.
