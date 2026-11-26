---
name: subagent-orchestrator
description: Dynamic DAG execution of child subagents with strict token budgets, bounded contexts, and structured result synthesis.
---

# Subagent Orchestrator & DAG Execution Protocol

Enables Antigravity and VS Code assistants to decompose massive, complex goals into discrete subagent execution graphs with zero token leakage.

---

## Orchestration Architecture

```mermaid
graph TD
    User["User Request / Epic"] --> Coordinator["Main Agent (Coordinator)"]
    
    subgraph DAG Decomposition
        Coordinator --> P1["Phase 1: Recon & Search"]
        Coordinator --> P2["Phase 2: Targeted Implementation"]
        Coordinator --> P3["Phase 3: Adversarial Review"]
    end
    
    subgraph Isolated Child Contexts
        P1 --> Sub1["research / explorer subagent"]
        P2 --> Sub2["coder / resolver subagent"]
        P3 --> Sub3["verifier / reviewer subagent"]
    end
    
    subgraph Synthesis
        Sub1 --> Synthesis["Bounded Summary & Artifact"]
        Sub2 --> Synthesis
        Sub3 --> Synthesis
        Synthesis --> Coordinator
    end
```

---

## Core Execution Invariants

1. **Strict Context Isolation**:
   Child subagents run in isolated conversation branches. Tool outputs, large diffs, and exploratory tracebacks do NOT spill into the coordinator's primary context window.

2. **Single-Responsibility Delegation**:
   Each subagent receives an unambiguous objective, strict read/write scope boundaries, and a deterministic completion criterion.

3. **Envelope Handoff Validation**:
   Coordinator verifies handoffs using `validate_a2a_handoff`:
   - `task_type`: Research, Code Modification, Review, or Verification.
   - `input_context`: Distilled facts, specific file paths, line ranges.
   - `success_criteria`: Exit code 0, test command, or schema match.

4. **Structured Synthesis**:
   Subagent returns a concise result (<= 3 lines) + structured markdown artifact path. Coordinator cites the artifact rather than echoing verbose child outputs.
