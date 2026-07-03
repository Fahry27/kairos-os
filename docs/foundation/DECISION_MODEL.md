# The Kairos Decision Model

## Mission
Kairos is transitioning from a traditional AI Operating System into a **Decision Operating System**. Its core purpose is to facilitate, track, and learn from the decisions made by the human operator.

## The DecisionPlan
The `DecisionPlan` is the canonical object of the Kairos ecosystem. It replaces transient AI outputs with a durable, structured record of human intent and machine reasoning. 

Every capability in Kairos—Workspace, Provider Router, Approval, Workflow, Audit, Reflection, and Memory—revolves around the `DecisionPlan`. It ensures that the exact context evaluated by the AI is the exact context reviewed by the human, executed by the workflow, and evaluated by the reflection engine.

## Decision Lifecycle
The journey of a decision in Kairos follows a strict lifecycle:
1. **Goal**: The operator provides an intent and context.
2. **Planner**: The Planner Engine uses the Provider Router to generate a proposal.
3. **DecisionPlan**: The output is structured into the canonical `DecisionPlan` object.
4. **Approval**: The operator reviews the `DecisionPlan` and explicitly authorizes it.
5. **Execution**: The approved plan triggers external workflows (e.g., n8n).
6. **Outcome**: The results of the execution are captured.
7. **Reflection**: The system evaluates the outcome against the plan's success definition.
8. **Memory**: Lessons learned are stored for future context.
9. **Future Planning**: New goals draw upon refined memory for better proposals.

## Decision Graph
A single goal rarely has only one solution. The `DecisionPlan` incorporates a **Decision Graph**, ensuring that exactly one primary plan is returned, while alternative viable approaches are nested as structured options. This gives the operator the agency to choose the best path without being overwhelmed by multiple disjointed plans.

## Outcome, Reflection, and Memory
A decision does not end at execution. Kairos treats the post-execution phases as critical to its value:
- **Outcome**: Capturing the raw results (success, failure, metrics) of an executed workflow.
- **Reflection**: Comparing the Outcome to the `success_definition` defined in the `DecisionPlan` to understand *why* a plan succeeded or failed.
- **Memory & Learning**: Extracting structured lessons from the Reflection phase. With the operator's permission, these lessons are embedded into long-term Memory, allowing Kairos to automatically inject past successes into future `DecisionPlan` proposals, compounding its intelligence over time.
