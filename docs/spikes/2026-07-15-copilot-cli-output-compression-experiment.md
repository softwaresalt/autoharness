---
title: "Copilot CLI Tool-Output Compression — Experiment Design & Feasibility Spike"
date: "2026-07-15"
description: "Feasibility findings and experiment design for agent tool-output compression with GitHub Copilot CLI as the PRIMARY host, challenging 086-F's MCP-only assumption."
topic: "Does GitHub Copilot CLI expose a pre-transcript output-rewrite surface that makes transparent tool-output compression feasible, and how should the experiment be designed?"
depth: "spike"
decision_status: "proceed-to-bounded-experiment"
doc_type: spike
source: docs/spikes/2026-07-15-copilot-cli-output-compression-experiment.md
stash_source: "AF767A44"
backlog_items:
  - "088-F"
relates_to:
  - "086-F"
builds_on:
  - "docs/spikes/2026-07-13-brainspace-compression-feasibility.md"
linked_artifacts:
  - "docs/spikes/2026-07-13-brainspace-compression-feasibility.md"
  - ".backlogit/archive/086-F.md"
  - "docs/decisions/2026-07-13-tokenmasterx-integration-spike.md"
  - ".github/instructions/constitution.instructions.md"
  - ".github/instructions/harness-architecture.instructions.md"
external_sources:
  - "https://docs.github.com/en/copilot/reference/hooks-reference"
  - "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks"
  - "https://docs.github.com/en/copilot/concepts/agents/hooks"
  - "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli"
tags:
  - "brainspace"
  - "ccr"
  - "copilot-cli"
  - "hooks"
  - "posttooluse"
  - "host-parity"
  - "primitive-1"
  - "primitive-5"
  - "primitive-7"
  - "operator-decision"
---

<!-- markdownlint-disable MD013 -->

<!-- markdownlint-disable-next-line MD025 -->
# Copilot CLI Tool-Output Compression — Experiment Design & Feasibility Spike

## Status

**INVESTIGATION COMPLETE — interception-surface feasibility CONFIRMED for
GitHub Copilot CLI; recommendation: PROCEED to a bounded, opt-in experiment /
benchmark, still DEFER any default or production install.** This spike is
Stage-side research for stash entry `AF767A44` and builds on `086-F`
(`docs/spikes/2026-07-13-brainspace-compression-feasibility.md`). No templates,
source, config, shipment, PR, or merge state were changed during the research.

The single most important finding: **the 086-F assumption that "Copilot CLI is
MCP-only with no pre-send output rewrite" is refuted by current GitHub
documentation.** Copilot CLI exposes a first-class `postToolUse` hook that can
replace a tool result **before it enters the model transcript**. This closes
086-F open question #1 for the Copilot CLI host specifically and turns the
central architectural blocker (host parity for compression-on-write) from
"unknown" into "confirmed on the primary host, with known caveats."

### Confidence labeling

Every claim below is tagged:

* **[CONFIRMED]** — verified from authoritative GitHub Docs (hooks reference /
  Copilot CLI docs) or from the locally installed Copilot CLI (`/env`, `/help`,
  version `1.0.71`).
* **[HYPOTHESIS]** — a design proposition or projection that the experiment must
  validate; not yet proven.

### Evidence provenance

* GitHub Copilot hooks reference — <https://docs.github.com/en/copilot/reference/hooks-reference>
  (event table, `postToolUse` input/output contract, hook locations, command/HTTP/prompt hook types, fail semantics). Fetched 2026-07-15.
* Using hooks with Copilot CLI — <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>.
* Locally installed Copilot CLI `1.0.71` `/env` line: "Show loaded environment
  details (instructions, MCP servers, skills, agents, **hooks**, plugins, LSPs,
  extensions)" and `/mcp`, `/plugin`, `/compact` slash commands — confirms hooks,
  plugins, and MCP are shipped, discoverable surfaces in the running CLI.
* Prior spike `086-F` for CCR store, retention, storage-location, and
  benchmark-safety findings (reused rather than re-derived).

This spike did **not** build or run a working hook; feasibility is established
from the documented contract plus the prior spike's safety analysis. Actual
token-savings numbers and evidence-preservation guarantees remain
**[HYPOTHESIS]** until the experiment (harvested below) runs.

## Problem / Context

Token costs are rising as providers trim model-usage subsidies. Bulky tool
outputs (test logs, JSON, directory listings, CI logs, verbose MCP responses)
remain in the transcript and are re-sent on every later turn, so compressing
them yields area-under-the-curve (AUC) savings across a session. 086-F evaluated
this (Brainspace / CCR from TokenMasterX) and recommended DEFER, with host
parity as the top blocker: it assumed only Claude Code could rewrite tool output
pre-transcript and treated Copilot CLI as MCP-only.

`AF767A44` challenges that assumption and asks, with **Copilot CLI as the
PRIMARY host**, for (1) an enumeration of every interception surface Copilot CLI
actually exposes today, and (2) an experiment design plus feasibility findings
covering measurable AUC savings, explicit decline cases, lossless byte-equivalent
retrieval, a security-safe store, and graceful cross-environment degradation.

## 1. Copilot CLI interception surfaces (refutes the 086-F MCP-only assumption)

Copilot CLI exposes a documented **hooks** system in addition to MCP, skills,
agents, plugins, LSPs, and extensions. The relevant interception points for
tool-output rewriting:

| Surface | Can rewrite tool result before transcript? | Evidence | Finding |
| --- | --- | --- | --- |
| **`postToolUse` hook** | **Yes.** Returns `modifiedResult.textResultForLlm` that **replaces** the tool result the model sees. Fires on the CLI surface for every successful tool call; optional `matcher` regex on `toolName`. | [CONFIRMED] hooks reference `postToolUse` output section. | **This is the compression-on-write surface.** It is exactly the PostToolUse-equivalent 086-F assumed Copilot CLI lacked. |
| `preToolUse` hook | Rewrites tool **args** (`modifiedArgs`) and can allow/deny; does not see the result. | [CONFIRMED] `preToolUse` decision control. | Useful for pre-screening (e.g., forcing quiet flags), not for output compression. |
| `postToolUseFailure` hook | Fires on tool **invocation failure**; can only append `additionalContext` recovery guidance — **cannot** replace the result. | [CONFIRMED] event table + payload (`error: string`). | Failed tool *invocations* are out of reach of compression — a partial safety win. This does **not** cover a shell/CI command that fails *inside* a successful tool result, which still arrives via `postToolUse.textResultForLlm` and is rewritable; a failure-content detector is required (see §3). |
| `preCompact` hook | Notification before context compaction (manual/auto). | [CONFIRMED] event table. | Relevant to Primitive 1 (state/context) but not to per-tool compression. |
| MCP tool result | A retrieval MCP server can return byte-equivalent originals on demand. | [CONFIRMED] `/mcp`; autoharness already ships `.mcp.json`. | This is the **retrieval half** (expand a placeholder), not the compression-on-write half. |
| Plugins | A plugin may contribute `hooks.json` (including `postToolUse`) plus MCP servers and skills. | [CONFIRMED] hooks reference "Hooks contributed by installed plugins". | **The clean packaging/distribution path**: ship the compression hook + retrieval MCP + decline policy as one optional plugin. |

**Conclusion:** compression-on-write is **feasible on Copilot CLI today**
through a `postToolUse` command or HTTP hook returning `modifiedResult`, with a
companion retrieval MCP tool for reversibility. This is a documented, shipped
capability — not a TokenMasterX assumption.

## 2. The `postToolUse` contract and what it means for compression

**[CONFIRMED] Input the hook receives (camelCase form):**

```typescript
{ sessionId, timestamp, cwd, toolName, toolArgs,
  toolResult: { resultType: "success"; textResultForLlm: string } }
```

**[CONFIRMED] Output the hook may return:**

```typescript
{ modifiedResult?: { resultType: "success"; textResultForLlm: string };
  additionalContext?: string }
```

* `modifiedResult` **replaces** the result text the model sees. Must keep
  `resultType: "success"` (a `"failure"` reroutes to `postToolUseFailure`).
* `additionalContext` is **appended after** `textResultForLlm`, joined across
  hooks with a double newline, and **capped at 10 KB**.
* Honored by both SDK programmatic hooks and command/HTTP config-file hooks.
* Return `{}` / empty to keep the original result unchanged (natural decline).
* Hook config load order (all combined): policy → repo `.github/hooks/*.json` →
  user `~/.copilot/hooks/` → inline settings → plugins.

**Design implications:**

* The compressor sees exactly **one text field** (`textResultForLlm`) — the same
  string the model would otherwise see. There are **no sibling `stderr` /
  `exit_code` fields** in the payload to accidentally drop, because the CLI has
  already flattened the tool result into that single string. So the "lose
  sibling failure fields" defect from the Claude hook in 086-§1 does **not**
  apply structurally here — but any failure evidence embedded *inside* that
  success string can still be elided by a careless compressor (see §3). [CONFIRMED contract; HYPOTHESIS on residual elision risk]
* Placeholders must be deterministic (no timestamps/mutable counters) to avoid
  breaking prompt caching (086 risk carried forward). [HYPOTHESIS to validate]
* The 10 KB `additionalContext` cap means the retrieval **handle/footer** must be
  compact; the bulk savings come from shrinking `modifiedResult.textResultForLlm`,
  not from `additionalContext`. [CONFIRMED cap]

## 3. Decline cases (Copilot-CLI-specific, extends 086-§Compression-decline)

Compression MUST be declined (return `{}`, pass original through) for:

* **Failure-bearing successes** — any success payload whose text embeds a
  non-zero exit, `stderr`, stack trace, gate verdict, or first actionable error
  the agent needs next. Because the hook cannot see structured exit status, a
  conservative detector must keep such outputs verbatim. [CONFIRMED single-field payload; HYPOTHESIS on detector]
* **Small outputs** where placeholder + retrieval-footer overhead loses the
  token-level never-expand check. [carried from 086]
* **Security-sensitive outputs** — tokens, `.env` content, auth output,
  environment dumps, private keys, or any secret-detector hit — declined
  **before** any durable stash. [carried from 086; hard requirement]
* **Gate/readiness artifacts** — local review readiness blocks, CI aggregation
  verdicts, `autoharness gate ...` output, P0/P1 findings, merge-authorization
  summaries — the verdict itself is the artifact. [carried from 086]
* **Operator / approval text** that must stay legible without tool-assisted
  expansion. [carried from 086]
* **Unwritable / failed CCR** — if the store cannot durably hold the original,
  pass the output through byte-identically; never emit placeholder-free elision. [carried from 086]

Tool-*invocation* failures (`postToolUseFailure`) are inherently excluded: the
hook cannot rewrite them. This does **not** cover a shell/CI command that fails
*inside* a successful tool result — that failure text arrives through
`postToolUse.textResultForLlm` and is rewritable, so the failure-bearing-success
decline above (a mandatory failure-content detector) is what keeps it verbatim.
[CONFIRMED invocation-failure exclusion; detector required for in-result failures]

## 4. Lossless byte-equivalent retrieval

* **Compression-on-write** (`postToolUse.modifiedResult`) shows a compressed view
  plus a compact, deterministic handle. [design]
* **Retrieval** is a companion **MCP tool** (e.g. `output_retrieve`) returning the
  byte-equivalent original from the store. Copilot CLI MCP support is
  [CONFIRMED]; autoharness already registers `.mcp.json`.
* **Byte fidelity requirement** (carried from 086-§2): the store must use a
  bytes-level / lossless codec, not UTF-8 `errors="replace"`, so tool JSON with
  surrogate or non-round-trippable text recovers exactly. The retrieval tool must
  return the **full** original or provide tested pagination/chunking — no silent
  truncation (086 flagged `MAX_RETRIEVE_CHARS` truncation). [HYPOTHESIS to prove in experiment]
* **Decide-then-stash** (086-§Stash-before-reject): screen for secrets and run
  the never-expand decision **before** any durable write, or roll back stashes
  from rejected attempts. No orphaned raw originals. [hard requirement]

## 5. Security-safe, containment-safe cache

Reuse 086-§3 wholesale — nothing about Copilot CLI changes the storage
conclusion:

* **Location:** repo-local, narrowly gitignored `.autoharness/cache/brainspace/`
  (or `.autoharness/ccr/`). Never user-home/global (`~/.copilot/`), never OS
  temp, never `.git/`.
* **Containment (Constitution IV):** resolver must anchor to workspace root/cwd,
  reject `..`, symlink escape, arbitrary absolute env paths, and upward parent
  search. No arbitrary `BRAINSPACE_CCR`.
* **Git hygiene:** ignore SQLite + `-wal`/`-shm` sidecars; add a staged-file guard
  / doctor check that fails if store files are staged.
* **Retention:** short, session/window-bounded TTL + size cap + purge command +
  session-end cleanup + SQLite checkpoint/compaction guidance. Never extend
  retention silently on dedup/access.
* **Secrets:** treat the store as sensitive-by-default; decline before storage on
  secret-detector hits.

Note: Copilot CLI hooks **run locally in the same shell as the CLI** [CONFIRMED],
which fits the local, containment-first model. The Copilot **cloud agent** runs hooks
inside an ephemeral Linux sandbox that is **provisioned per job and destroyed when the
job ends** [CONFIRMED, hooks reference]. Because a session maps to a job (`sessionEnd`
fires once per job), the sandbox filesystem **persists across turns within a job**, so a
**job-scoped** reversible store is viable there — files a hook writes stay available to
later turns in the same job. Only cross-**job** durability is unavailable, and the
compressed transcript does not resume across jobs either, so cross-job durability is not
required. The store design is therefore in scope for the cloud agent as a job-scoped
store, not excluded.

## 6. Graceful cross-environment degradation

* **Copilot CLI (primary):** transparent compression-on-write via `postToolUse` +
  MCP retrieval. [CONFIRMED feasible]
* **Copilot cloud agent:** the sandbox is provisioned per job and destroyed at job end,
  but its filesystem **persists across turns within a job**, so a **job-scoped** reversible
  store works — there is no cross-job durability, which the transcript does not need since
  it also does not resume across jobs. The genuine caveats are the reduced hook surface
  (only a **subset of events** fires and only **bash/`command`** hook entries are honored)
  and constrained network, so treat as **supported within a job, non-durable across jobs**
  rather than degraded on persistence grounds. [CONFIRMED, hooks reference]
* **VS Code + Copilot:** hooks support a "VS Code compatible" PascalCase payload
  format [CONFIRMED in reference], suggesting parity potential, but this spike
  did not verify the VS Code Copilot host end-to-end — treat as
  **unknown/verify-before-claim**.
* **Codex / Cursor / Claude Code and other hosts:** fall back to **MCP/manual**
  compression, explicitly labeled degraded; base agent behavior stays coherent
  and correct when the pack is disabled or unavailable. [carried from 086 overlay
  contract]

Overlay contract (unchanged from 086): compression changes token **economics**,
not task **correctness**. Agents must preserve evidence and complete work with the
pack disabled, unavailable, MCP-only, or declined for a specific output. This
keeps autoharness environment-agnostic — the transparent mode is an optional
overlay enabled only on hosts with verified pre-transcript rewrite support
(now: **Copilot CLI confirmed**).

## 7. Experiment design (the deliverable AF767A44 asked for)

**Goal:** prove or disprove, on real autoharness work, that Copilot-CLI
`postToolUse` compression yields honest AUC token savings without hiding required
evidence, with lossless retrieval and a safe store.

### 7.1 Prototype (throwaway, behind a flag; NOT a production install)

1. A `postToolUse` command hook (matcher scoped to noisy tools:
   `bash|view|task` and MCP result tools) that: reads the payload, runs a
   secret/PII screen, runs a type router (JSON / log / diff / prose), applies a
   never-expand token+char guard, **decides before stashing**, writes the
   original to a byte-lossless local store, and returns `modifiedResult` with a
   compressed view + compact deterministic handle — else returns `{}`.
2. A retrieval **MCP tool** returning the byte-equivalent original (full or
   paginated).
3. A containment-safe store under `.autoharness/cache/brainspace/` with TTL, size
   cap, purge, and staged-file guard.

### 7.2 Measurement — AUC token savings

For each benchmark task, record: raw tokens, compressed tokens, and projected
**AUC savings over 1 / 3 / 5 / 10 turns** (the output is re-sent each turn), under
the model tokenizer plus a cheap fallback estimator. Report net savings after
placeholder/footer overhead.

### 7.3 Benchmark corpus (reuse 086-§4 candidates on real autoharness commands)

Compression-positive: `pytest -vv` (passing runs); `backlogit doctor` (~62-finding baseline);
large `git --no-pager diff`; verbose MCP JSON
(backlogit queue/list, GitHub check-runs); Engram/graphtor large search results;
workspace file inventories.

Decline / negative controls: tiny outputs; forced unwritable-CCR passthrough;
secret-bearing output; gate-verdict/readiness blocks; failure-bearing successes
(e.g. failed `gh run view --log-failed`, non-zero-exit command output embedded in
a successful tool result); active stack traces; operator/approval text.

### 7.4 Proof method — a result counts as a **safe win** only when

1. compressed tokens are lower under both tokenizers;
2. retrieval is byte-equivalent for every visible placeholder (full or tested
   pagination — no silent truncation);
3. rejected/declined attempts leave **no** durable store row (decide-then-stash);
4. the evidence oracle passes **without** retrieval for required inline facts
   (exit status, stderr, gate verdicts, IDs);
5. the model/evaluator answers the task correctly from the compressed view,
   using retrieval only when the task needs hidden detail;
6. decline cases and negative controls are reported, not hidden.

The benchmark must not "win" by hiding the one stack frame, gate verdict, stderr
line, exit status, or identifier needed to act.

## 8. Recommendation

**PROCEED to a bounded, opt-in experiment/benchmark; keep production/default
install DEFERRED until the experiment proves honest savings + evidence
preservation + safe reversible storage.**

Rationale:

* **Host parity for the primary host is now solved.** Copilot CLI `postToolUse`
  can rewrite tool output pre-transcript [CONFIRMED]. 086's central blocker no
  longer applies to Copilot CLI; the pilot need not wait on host uncertainty for
  the primary target.
* **The remaining risks are the measurement, evidence-preservation, and storage
  risks 086 already enumerated** — not an interception-surface gap. They are
  exactly what the experiment (§7) is designed to resolve.
* **The tool-invocation failure path is out of reach** — `postToolUse` fires only
  on success, so failed tool *invocations* cannot be rewritten [CONFIRMED].
  Failure text embedded in a *successful* tool result is still rewritable, so the
  experiment must include a failure-content detector (§3) rather than assume all
  failing-command evidence is safe by construction.
* **Clean packaging exists** — a plugin can bundle the hook + retrieval MCP +
  decline policy as one optional, disabled-by-default capability pack [CONFIRMED
  plugin hook contribution].
* **No second graph stack.** This is a tool-output compression overlay only;
  `agent-engram` remains the single graph authority.

Minimal acceptable scope for the follow-on experiment:

1. optional capability pack / plugin, disabled by default;
2. transparent mode enabled only on Copilot CLI (verified) — others degrade to
   MCP/manual, explicitly labeled;
3. repo-local gitignored store with containment-safe resolver, TTL/size cap,
   purge, checkpoint/compaction guidance, and staged-file guard;
4. decide-then-stash (or stash-rollback-on-reject);
5. full or paginated byte-equivalent retrieval;
6. secret/PII detection with conservative decline;
7. benchmark suite with positive and negative controls before any generated
   harness artifact depends on it.

### Relation to 086-F

This spike **closes 086 open question #1 for Copilot CLI** and **relates to**, not
duplicates, `086-F`. 086 remains the authoritative CCR store / retention /
storage-location / benchmark-safety analysis; this spike adds the confirmed
Copilot-CLI interception surface and the experiment design. Follow-on backlog is
harvested under a new feature that references `086-F` and this artifact.

## Risks

* **Evidence hiding inside success payloads** — a careless compressor can still
  elide a stack frame or exit line embedded in `textResultForLlm`. Conservative
  decline + evidence oracle mitigate. [HYPOTHESIS-level until experiment]
* **Sensitive-data persistence** — CCR stores exact originals; decide-then-stash
  and secret screening are mandatory.
* **Retrieval truncation** — must prove full/paginated byte-equivalent recovery.
* **Containment escape** — resolver must enforce Constitution IV.
* **Prompt-cache fragility** — placeholders must be deterministic.
* **Hooks feature maturity / version drift** — hooks are a recent, evolving
  Copilot surface; the contract (fields, caps, load order) must be re-verified
  against the target CLI version before the pilot ships. [product/version
  watch-item, not a hard blocker]
* **Benchmark overfitting** — repetitive logs/JSON may show large wins while
  prose, active debugging, and review-critical diffs should decline.

## Open questions / preconditions

1. Exact token-savings on real autoharness commands (§7.2) — unknown until run.
2. Which secret/PII detector + threshold forces decline before storage?
3. Byte-equivalent retrieval API shape: no-cap MCP retrieval, pagination, or
   chunking, plus direct-store recovery tests for large originals.
4. Retention TTL/size policy and purge ownership.
5. VS Code + Copilot host parity — verify the PascalCase hook path end-to-end
   before claiming transparent savings there.
6. Copilot CLI hooks version/GA guarantees for the pilot's target CLI version.
7. Doctor/pre-commit check proving store SQLite/WAL/SHM sidecars are never staged.
