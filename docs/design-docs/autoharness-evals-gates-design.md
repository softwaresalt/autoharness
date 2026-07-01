# **Design Document: Deterministic Gates, Telemetry, & Evaluation Engine**

**Date:** 2026-06-30

**Status:** Proposed / Active

**Target Repositories:** autoharness, backlogit, agent-engram / docline

## **1\. Overview & Objectives**

To achieve true long-horizon autonomy, an agentic system cannot rely on non-deterministic LLM loops for state validation, nor can it self-improve without high-fidelity operational metrics. The objective of this design is to transition autoharness from a purely prompt-driven orchestrator into a **deterministic, closed-loop execution and observability engine**.

This will be achieved by:

1. **Deterministic Gating:** Enforcing strict CLI-based validation hooks (via git diff) before allowing tasks to transition to a completed state.  
2. **High-Fidelity Telemetry:** Capturing precise economic (token, duration) and outcome (quality, verification success) metrics per execution run.  
3. **Compound Learning:** Piping execution telemetry into agent-engram's CozoDB to allow agents to retrieve their own historical performance data for dynamic self-correction.  
4. **Headless Evaluation:** Providing an isolated benchmark mode for testing model combinations across standard task sizes.

## **2\. Architectural Philosophy: Strict Separation of Concerns**

To avoid monolithic anti-patterns, responsibilities are strictly partitioned across the tooling ecosystem:

* **autoharness (The Orchestrator & Observer):** Wraps the execution environment. It triggers hooks, emits telemetry (Execution Epochs), runs benchmarks, and dispatches validation commands. *It does not parse documents or manage task schemas.*  
* **backlogit (The Work State Authority):** Owns the .backlogit/ queue. Validates state machine transitions. *It does not validate code or architecture documents.*  
* **agent-engram / docline (The Structural Authority):** Owns document integrity. Provides the AST parser and schema validation logic to verify that files are fully conformant for graph database ingestion.

## **3\. Phase 1: Deterministic Gates & State Synchronization**

This phase guarantees that no file enters the repository or graph without passing a strict, binary validation check, effectively eliminating LLM "hallucinated completion."

### **autoharness Tasks**

* **Implement Lifecycle Hooks:** Refactor the execution loop to read validation\_gates from .autoharness/config.yaml.  
* **Git-Diff Discovery Engine:** Implement a utility to run git diff \--name-only (against the active task branch's base) to determine exactly which files the agent modified.  
* **Subprocess Interceptor:** Hijack the mark\_task\_complete agent tool call. Iterate through modified files, match them to config.yaml glob patterns, and execute mapped commands (e.g., engram verify).  
* **Forced Correction Loop:** If a validation subprocess exits \> 0, block the task completion and inject stderr directly into the agent's context window.

### **backlogit Tasks**

* **Restrict Doctor Scope:** Ensure backlogit doctor only validates .backlogit/ artifacts against header-def.yaml.  
* **State Locking:** Implement a lock (e.g., a .lock file) to prevent concurrent modifications to a task while it is undergoing validation.

### **agent-engram / docline Tasks**

* **Provide verify CLI:** Implement engram verify \<path\> (or docline verify). This acts as the structural AST / YAML frontmatter linter.  
* **Reactive Sync Daemon:** Implement the file-watcher that automatically syncs valid, mutated markdown files directly into CozoDB nodes.

## **4\. Phase 2: Telemetry, Estimations, & Compound Learning**

This phase enables the system to measure its own efficiency ("Best Outcome at the Best Price") and adjust strategies dynamically.

### **autoharness Tasks**

* **Pre-Execution Sizing Gate:** Before a task starts, pass the task node to a lightweight model (e.g., Haiku) to estimate complexity. Execute backlogit update \<task\_id\> \--size \<result\> to write it back to the repository.  
* **Execution Epoch Emitter:** Wrap the execution loop to log: Route Configuration (Models used), Economic Payload (Tokens, COGS, Duration), Operational Reality (CLI tools used), and Absolute Outcome (Gate exit codes).  
* **SQLite Aggregator:** Write Execution Epochs to a local SQLite database (.autoharness/metrics/execution\_epochs.db) for quantitative metric analysis.  
* **Reviewer Matrix:** Run a headless, deterministic grading prompt on the final git diff (scoring Maintainability, Security, etc., requiring line-number citations for penalties).  
* **Headless Eval Runner:** Build an autoharness eval mode that runs frozen git states against multiple model configurations to build baseline benchmarks.

### **backlogit Tasks**

* **Schema Update:** Update header-def.yaml to require/allow a size: attribute in task frontmatter.  
* **Mutation CLI:** Expose a command (e.g., backlogit update \<task\_id\> \--size \<value\>) allowing autoharness to inject the T-shirt size back into the .backlogit markdown without destroying the AST.

### **agent-engram Tasks**

* **Telemetry Schema:** Define the CozoDB relational schema for ExecutionEpoch events.  
* **Ingestion Path:** Consume the JSONL telemetry emitted by autoharness and link it relationally to active Task and Code nodes, enabling the agent to query its own past failures/costs.

## **5\. Configuration Schema Contract**

The following configuration block dictates the contract between autoharness and the external authorities. It must be added to .autoharness/config.yaml.

lifecycle\_hooks:  
  pre\_execution:  
    \- name: "estimate\_complexity"  
      condition: "task.size \== null"  
      action: "internal:estimate\_tshirt\_size"  
      write\_back: "backlogit update {task\_id} \--size {result}"

  pre\_task\_completion:  
    validation\_gates:  
      \- pattern: "docs/\*\*/\*.md"  
        command: "engram verify {file\_path}"  
        timeout\_seconds: 15  
        
      \- pattern: ".backlogit/queue/\*.md"  
        command: "backlogit doctor \--target {file\_path}"  
        timeout\_seconds: 5  
        
      \- pattern: "src/\*\*/\*.py"  
        command: "pytest tests/ \--lf"  
        timeout\_seconds: 60

telemetry:  
  mode: "sqlite"  
  database\_path: ".autoharness/metrics/execution\_epochs.db"  
  emit\_jsonl: true

## **6\. Open Questions & Resolution Paths**

1. **Infinite Correction Loops:** If an agent consistently fails the validation gate (e.g., 3+ failures), should autoharness force a state change to blocked and return it to the queue, or attempt an automatic model escalation (e.g., routing to a heavier model)?  
2. **Cross-Platform Paths:** Ensure the autoharness glob matching and subprocess execution handles path normalization gracefully across Windows/Linux runners.  
3. **Global vs. Local Telemetry:** Should the SQLite telemetry database live locally inside the target repository (.autoharness/metrics/), or globally to allow multi-repo performance aggregation? *(Recommendation: Keep local for Phase 1 to bind context directly to the repo's specific architecture).*