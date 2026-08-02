# **AutoHarness Framework: Multi-Tier Routing, Escalation, and State Management Specification**

## **1\. Core Architectural Components**

The autoharness framework must implement the following distinct roles and capabilities:

> * **The Orchestrator (Workflow Manager):** Captures user intent, manages system state, determines the sequence of actions, and executes routing decisions using the Action/Observation loop.  
> * **The Stage Agent (Architect / Planner):** Retrieves architectural context via tools like graphtor-docs and agent-engram, designs solutions that respect existing constraints, and decomposes high-level goals into granular implementation tasks.  
> * **The Ship Agent (Implementation Worker):** Executes granular, decomposed tasks provided by the Stage Agent, engaging in fast generation and rapid compile/test/fix iterations.  
> * **The Verification & Compaction Layer:** Analyzes test results, parses compiler logs, summarizes conversational history, and prunes redundant state data in the background.

## **2\. Dynamic Model Routing Logic**

The harness must implement a dynamic routing layer to assign the optimal model to each component based on the required cognitive profile.

| Component | Recommended Model | Rationale for Routing   |
| :---- | :---- | :---- |
| Orchestrator | GPT-5.6 Sol | Optimal for CLI tool execution, sequential pipelining, and strict JSON schema adherence. |
| Stage Agent | Claude Opus 4.8 | Superior for long-context codebase evaluation and designing architecture within complex existing constraints without price penalties. |
| Ship Agent | GPT-5.6 Terra | Fast, cost-efficient baseline worker for implementing decomposed tasks. |
| Verification & Compaction | Anthropic Haiku / GPT-5.6 Luna | Lowest latency and cost for background tasks like log parsing, state summarization, and initial intent routing. |

## **3\. CLI & MCP Tool Integration Requirements**

The autoharness framework must seamlessly integrate with custom tools (backlogit, agent-engram, graphtor-docs) across identical CLI and MCP tool surfaces.

> * **Tool Execution Abstraction:** Provide a unified interface for tool execution, treating CLI commands and MCP server requests as equivalent actions within the Action/Observation loop.  
> * **MCP Schema Adherence:** The Orchestrator must strictly validate tool calls against JSON schemas provided by the respective MCP servers.  
> * **Sequential Pipelining:** Support piping the output of one CLI tool directly into the input of another.  
> * **Error Handling & Recovery:** Parse stderr or MCP error responses and route them back to the active model for correction.

## **4\. Dynamic Escalation Routing (Fallback Capability)**

The framework must implement a multi-tiered escalation routing system to dynamically scale model capability based on task difficulty.

> * **Telemetry Monitoring:** Actively track the iteration count, token consumption, and execution time of the active Ship Agent.  
> * **Escalation Triggers:** Define configurable thresholds (e.g.,  
>   `MAX_ITERATIONS = 5`) that immediately halt the current execution when breached.  
> * **Adversarial Verification Pass:** Support a low-latency verification step using GPT-5.6 Luna or Anthropic Haiku. A low confidence score triggers an escalation.  
> * **Contextual Handoff Generation:** Compile an "Escalation Payload" containing the original specification, current codebase state, and a summary of failure modes.  
> * **Model Re-Routing:** Dynamically assign the Escalation Payload to Claude Sonnet 5 for implementation.  
> * **Terminal Handoff:** If Claude Sonnet 5 fails, pause execution, save state to agent-engram, and surface a prompt for human intervention.

## **5\. Checkpointing and State Recovery**

To ensure resilience in long-running agent workflows, the framework must implement persistent, granular state checkpointing to recover from crashes, token limits, or API failures without restarting tasks from the beginning.

> * **Granular State Preservation:** The harness must save the complete context state—including the current prompt history, working variables, generated plans, and recent tool outputs—after every successful step or completed Action/Observation loop.  
> * **Durable Storage Integration:** Checkpoints should be serialized and written to a durable storage backend (e.g., SurrealDB via agent-engram) using unique run identifiers.  
> * **Crash Resumption Logic:** On startup or recovery, the harness must check for incomplete runs. If a run crashed, the Orchestrator retrieves the last successful checkpoint and re-initializes the context window exactly as it was prior to the failure.  
> * **Context Pruning on Restore:** During resumption, the Verification/Compaction layer should automatically summarize the pre-checkpoint conversation history to optimize the restored context window and save tokens.

## **6\. Implementation Plan**

> 1. **Phase 1 \- Routing Engine Implementation:** Develop dynamic routing logic to select models based on task type (Sol, Opus 4.8, Terra, Haiku/Luna).  
> 2. **Phase 2 \- Component Architecture:** Refactor existing code to separate Orchestrator, Stage Agent, and Ship Agent paths. Implement background Verification/Compaction.  
> 3. **Phase 3 \- Tool Surface Unification & Checkpointing:** Standardize the Action/Observation loop for CLI/MCP. Implement durable state checkpointing to agent-engram after each loop.  
> 4. **Phase 4 \- Escalation Loops:** Implement telemetry tracking, the adversarial verification pass, and the payload handoff to Claude Sonnet 5\.  
> 5. **Phase 5 \- Testing & Validation:** Execute the Contextual Integration Test to validate architectural planning and implementation safety across the multi-tier system.