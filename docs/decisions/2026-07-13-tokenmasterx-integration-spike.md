---
title: "TokenMasterX Token-Economics Integration Evaluation"
date: "2026-07-13"
description: "Spike evaluation of the gitignored TokenMasterX reference workspace and candidate autoharness integration ideas for graph-routed structural queries, token-economics measurement, and Brainspace-style output compression."
topic: "Which TokenMasterX ideas, if any, should autoharness integrate, given existing agent-engram code-graph coverage and the need for operator product direction?"
depth: "spike"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-13-tokenmasterx-integration-spike.md
source_stash_ids:
  - "CE8771AF"
backlog_items:
  - "078-F"
linked_artifacts:
  - "references/tokenmasterx/README.md"
  - "references/tokenmasterx/token-master-plugin/skills/token-master/SKILL.md"
  - "references/tokenmasterx/token-master-plugin/skills/token-master/agent.template.copilot.md"
  - "references/tokenmasterx/token-master-plugin/skills/token-master/brainspace/router.py"
  - ".github/instructions/agent-engram.instructions.md"
tags:
  - "token-economics"
  - "agent-engram"
  - "code-graph"
  - "brainspace"
  - "primitive-1"
  - "primitive-7"
  - "operator-decision"
---

# TokenMasterX Token-Economics Integration Evaluation

## Status

**PROPOSED — operator product decision required before implementation.** This
spike evaluated the local, gitignored `references/tokenmasterx/` workspace for
ideas that could inform autoharness. The reference contents are intentionally not
committable here; this document records the evaluation and links to the local
paths used as evidence. No TokenMasterX code, templates, schemas, config, hooks,
or source files were copied or modified.

## Problem (stash CE8771AF)

The stash asks whether TokenMasterX contains ideas or features worth integrating
into autoharness. TokenMasterX describes itself as a harness-layer token-economics
project: instead of letting the model repeatedly re-derive code structure through
grep and file reads, it routes structural questions to a prebuilt code graph and
adds a Brainspace compression layer for bulky tool outputs that persist in the
transcript. The decision is not whether the ideas are interesting — they are —
but which ones belong in autoharness without duplicating the already-enabled
`agent-engram` code-graph capability pack.

## Evaluation inputs

* `references/tokenmasterx/README.md` — measurement thesis, graph-routing design,
  Brainspace compression layer, install model, limitations, and repository layout.
* `references/tokenmasterx/token-master-plugin/skills/token-master/SKILL.md` —
  `/token-master` command behavior: build `.token-master/graph.json`, install a
  routing agent, prefer graphify, escalate to codegraph only for precision cases.
* `references/tokenmasterx/token-master-plugin/skills/token-master/agent.template.copilot.md`
  — routing instructions for graphify-nav vs codegraph and native Copilot session
  recall.
* `references/tokenmasterx/token-master-plugin/skills/token-master/brainspace/router.py`
  — type detection and never-expand guard for JSON, logs, code, and prose output.
* Directory skim: `.claude-plugin/`, `token-master-plugin/`, and `assets/` confirm
  this is packaged as a plugin/skill with host-agent templates, graph MCP server,
  Brainspace MCP/hook implementation, benchmark harnesses, tests, and generated
  SVG assets.

## Core ideas mapped to autoharness primitives

| TokenMasterX idea | Summary | Autoharness primitive mapping | Evaluation note |
|---|---|---|---|
| Enforced structural-query routing | Make graph lookup the default for callers/callees/impact/inheritors instead of optional grep. | Primitive 1 (State, Context & Knowledge Retrieval), Primitive 6 (Injection Points), Primitive 9 (Repository Knowledge). | Strong conceptual fit, but autoharness already has `agent-engram` with `map_code`, `impact_analysis`, `list_symbols`, and freshness rules. Integration should likely strengthen Engram routing, not add a second graph stack by default. |
| Token economics as cumulative area under context | Measure cumulative input processed across turns, not just one-shot token counts. | Primitive 7 (Observability & Evaluation), Primitive 10 (Operational Closure & Feedback). | High value for autoharness evaluation because it turns token efficiency into a measurable outcome rather than an anecdotal claim. This overlaps with 079-F's telemetry contract work. |
| Cheap graph default plus precision escalation | Use `graphify` for cheap inferred edges and `codegraph` only when exact call sites or sparse graphs justify cost. | Primitive 1 (State, Context & Knowledge Retrieval) and Primitive 5 (Guardrails). | Useful policy pattern: graph-source selection should be explicit, cost-aware, and evidence-backed. This is retrieval-source escalation, not Primitive 3 model-tier escalation; reserve Primitive 3 for actual model routing decisions. Engram could expose a similar cheap/default vs precise/escalated contract if multiple graph suppliers exist. |
| Brainspace compression with CCR | Compress repetitive tool outputs, store exact originals in a content-addressed reversible store, and never expand in token terms. | Primitive 1, Primitive 6, Primitive 7. | Promising but higher-risk than graph routing. Host support differs: Claude Code can rewrite tool output; Copilot CLI is MCP-only. autoharness should not commit to this without a product decision on host behavior and data retention. |
| Self-serve benchmarks | A/B/C benchmark runs report token savings and honest negatives. | Primitive 7. | Strong fit for evals. The method is more important than the implementation: autoharness should be able to prove token-efficiency improvements and report neutral/negative cases. |
| Native session recall as temporal layer | Use host CLI session history/resume rather than a custom memory server. | Primitive 1. | Useful caution: full transcript resume is re-billed and is not semantic memory. autoharness should keep memory guidance honest and cost-aware. |

## Overlap with `agent-engram`

The closest existing autoharness surface is the `agent-engram` capability pack.
Engram already provides indexed search, workspace binding/freshness checks,
code-graph lookup, `impact_analysis`, `map_code`, and fallback discipline. A
straight TokenMasterX import would risk:

1. **Duplicate graph authority** — agents could choose between Engram, graphify,
   codegraph, grep, and raw file reads without a clear precedence rule.
2. **Conflicting freshness models** — `.engram/` is tool-managed state, while
   TokenMasterX writes `.token-master/graph.json` and tells users to rerun
   `/token-master` when stale.
3. **Measurement mismatch** — TokenMasterX's key win is cumulative input-token
   reduction, while current autoharness telemetry captures route/economics per
   execution epoch but not yet graph-route savings or context-area deltas.

Therefore the likely integration path is to **use TokenMasterX as product/design
prior art**, not as an immediate dependency or copied implementation. Strengthen
Engram-first routing and add token-efficiency measurements before considering any
new graph supplier.

## Candidate integration ideas

| Candidate | Benefit | Cost | Risk | Requires operator decision? |
|---|---|---|---|---|
| Add explicit token-efficiency metrics to the autoharness telemetry contract: cumulative input tokens, context-area estimate, routed-vs-raw lookup counts, and avoided file-read evidence. | Makes Primitive 7 measurable and lets future graph/compression work prove value. | Medium: schema/docs/CLI/eval work after architecture approval. | Metrics can be misleading if the host cannot expose reliable token/context data. | **Yes** — data-contract scope belongs with 079-F and 082-F. |
| Tighten Engram routing guidance using TokenMasterX-style structural-query enforcement. | Lowers token waste without adding a new graph stack. | Low/medium: instruction and template updates plus verification checks. | Over-enforcement can slow work when Engram is unavailable or stale. | **Yes** — product decision on how strict retrieval enforcement should be. |
| Introduce a graph-supplier abstraction with Engram as the default and optional suppliers for graphify/codegraph-like backends. | Future-proofs graph routing and enables precision escalation. | High: schema/profile, installer, MCP registration, tuning, verification, and docs. | Duplicate tool state, stale indexes, and unclear support burden. | **Yes** — architecture/product decision. |
| Build a TokenMaster-style benchmark suite for structural navigation tasks. | Provides objective before/after evidence and honest negatives. | Medium/high: deterministic tasks, correctness oracles, replay support, telemetry integration. | Benchmark may overfit to structural tasks and ignore general workflow value. | **Yes** — evaluation investment decision. |
| Explore Brainspace-like output compression as an optional capability pack. | Could reduce transcript cost for large JSON/log/tool outputs and complement graph routing. | High: CCR persistence, host-specific hooks, MCP tools, privacy/security review, tuning/verification. | Loss or hiding of relevant evidence; host parity gap; durable storage of raw outputs. | **Yes** — explicit product and safety decision required. |
| Do not integrate yet; only record learnings. | Avoids duplicating Engram and keeps current roadmap focused. | Low. | Misses near-term token-efficiency wins if no follow-up is prioritized. | **Yes** — choosing not to integrate is still a product decision. |

## Recommendation

Sequence this behind the telemetry/data-contract work rather than importing a new
implementation now:

1. Treat **079-F** as the prerequisite: define a tool-telemetry contract that can
   measure graph routing, token efficiency, compression, and context-area savings.
2. Strengthen **Engram-first structural routing** if the operator wants a near-term
   low-cost win, because Engram is already installed and indexed in this repo.
3. Defer **Brainspace** and any extra graph supplier until the operator decides
   whether host-specific compression and multi-graph support belong in
   autoharness.

## Operator Decision Required

The operator must decide **which TokenMasterX ideas, if any, autoharness should
integrate**: measurement-only, Engram-routing tightening, benchmark/eval work,
Brainspace-style compression, graph-supplier abstraction, or no integration.
Implementation is blocked until that product direction is chosen.

## Open questions

1. Should autoharness measure cumulative token economics as a first-class success
   metric for every task, or only for eval/spike sessions?
2. Is Engram the single graph authority for autoharness, or should autoharness
   support interchangeable graph suppliers?
3. What host parity is required before output compression is acceptable, given
   Claude Code hooks and Copilot CLI MCP-only behavior differ?
4. Where should reversible raw-output storage live, and what retention/privacy
   rules apply?
5. What benchmark tasks would be representative of autoharness's real work rather
   than only structural navigation demos?
