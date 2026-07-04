# ADR 013: Decision Operating System

## Status
Proposed

## Context
Kairos OS is evolving from a simple command-execution utility into a fully autonomous agent framework. Executing scripts deterministically is straightforward, but allowing an AI to synthesize plans, parse context, and independently decide on actions introduces significant safety and alignment risks. We need a fundamental paradigm shift in how the system processes intent.

## Decision
We will architecture Kairos as a **Decision Operating System (DOS)**. 

Instead of executing actions immediately, the system will decompose all high-level goals into a structured `DecisionPlan`.

1. **Planner Engine**: An AI-driven engine that receives a user goal, surveys the available system capabilities (commands, connectors, plugins), and formulates a step-by-step plan without executing it.
2. **Approval Bridge (User-in-the-loop)**: Any plan that mutates state, executes dangerous commands, or sends data externally must halt at the Approval Bridge. The `DecisionPlan` is presented to the user for explicit authorization.
3. **Safety Flags**: The DOS will embed safety flags at the core of the `DecisionPlan` schema (e.g., `execution_enabled`, `data_mutation_performed`). These are strictly enforced by the backend validation layer and cannot be bypassed by the AI.

## Consequences
- **Positive**: Maximum safety. The AI can reason and plan freely without the risk of accidental destruction.
- **Positive**: High observability. Users can inspect the exact thought process and intended execution path of the AI before it happens.
- **Negative**: Adds friction to the user experience, as fully autonomous execution is intentionally bottlenecked by the Approval Bridge.
