---
title: "Shared execution architecture for the seven-entry contract-defect portfolio, and the precursor-first re-slicing that follows from it"
description: "Binding Stage architecture decision issued after the terminal attempt-08 plan-review block of all six defect plans. Decides the shared execution architecture the six units had been silently assuming and never building: Python-backed atomic operations in src/autoharness exposed through the CLI with a real MCP/sidecar parity surface; a PREPARE -> VERIFY -> ACTIVATE rollout invariant in which activation is one task and one commit across every authoritative template, installed mirror, registry, permission declaration and consumer; explicit versioned normalization of existing mutable manifests and checkpoints before strict canonical validation; a real installed Ship pre-task harness-generation lifecycle in place of the assumed harness-architect; and isolated network-denied Linux CI for external binary conformance. Re-slices the portfolio from a six-shipment false-star DAG into two bounded spikes, four foundational precursor release units, and five reduced defect units. Supersedes the 2026-09-17 seven-entry portfolio deliberation for EXECUTION ARCHITECTURE and SEQUENCE only; that decision's seven-source portfolio scope and per-entry ownership boundaries remain in force."
doc_type: decision
source: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
date: 2026-09-18
status: decided
revision: 7
revision_note: "REVISION 7 RECORDS THE ACTOR AS BOTH STRUCTURALLY PRESENT AND BEHAVIOURALLY CONFORMANT, AND RETIRES TWO EXECUTION GRAPHS THAT NEVER RAN. Revision 6 recorded structural installation by 07b4be79 but left the harness-architect actor behaviourally non-conformant with P-004: its installed Step 5.2 invoked pytest while P-004 and the manifest require the canonical command. Revision 6 attributed that to an install-time variable precedence defect and harvested a corrective release unit (191-S / 185-F / 185.001-T-185.006-T). BOTH THE DIAGNOSIS AND THE UNIT ARE WITHDRAWN. The real defects were a stale installed render plus a manifest variable that was never seeded; _derive_template_variables already treats manifest variables_used as authoritative because profile-derived defaults apply through setdefault. Ship review-remediation commits 1cb0dc81 and b8ac632a corrected both directly on this branch, and independent attempt-08 finding S26 separately held 191-S structurally unexecutable under ordinary P-002/P-004. 191-S, 185-F and 185.001-T-185.006-T are therefore ARCHIVED AS RETIRED, NEVER CLAIMED, NEVER EXECUTED AND NEVER SHIPPED; the 187-S -> 191-S edge is withdrawn and 187-S is restored as an explicit dag-root. This revision additionally retires 176-S, 168-F and the live 168 tasks: they encode the superseded P-004 design that independent attempt-01 finding O1 blocked, they were never claimed or executed, and the P-004 gate is re-harvested fresh after the foundations actually ship rather than restored. SM-1 is reconciled with P-004 plan revision 7. D1-D8, D10, D11 and every unrelated decision, state-machine table and DAG edge are UNCHANGED; D11 manifest parity is preserved verbatim."
depth: deep
deciders: operator, Stage
decision_status: decided
promoted_to: plan
parent_head: db2afc9a
supersedes_for_execution_architecture: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
superseded_decision_revision: 3
supersession_scope: "execution-architecture-and-sequence"
preserved_from_superseded_decision:
  - "D1 — 14F4D6F3 merged into 86498B64; both source IDs preserved"
  - "D2 — no other merge; five further single-entry groups held apart under width isolation"
  - "D4 — 76EBDE6D is disposition (c), an explicit harness-scoped selector"
  - "D5 — C9CD24F3 adopted with a hard scope ceiling"
  - "D6 — 71200CBB ships items (3) then (2) then (1)"
  - "D7 — 7F9CB5E9 retained as autoharness work with an explicit external boundary"
  - "D9 — two pre-existing blockers surfaced, not repaired"
withdrawn_from_superseded_decision:
  - "D8 — the six-shipment fan-out DAG rooted at 176-S. Withdrawn as a false star: 176-S is not a technical prerequisite of 177-S, 178-S, 179-S, 180-S or 181-S."
  - "D3 — the 3EF5AAF2 spike-first sequencing. The spike completed; its conclusion is carried forward, its sequencing edge is not."
stash_ids:
  - 3EF5AAF2
  - 14F4D6F3
  - 86498B64
  - 76EBDE6D
  - C9CD24F3
  - 7F9CB5E9
  - 71200CBB
degraded_capabilities:
  - capability: agent-engram
    state: circuit-open
    note: "Engram circuit open; not retried per operator instruction. All codebase discovery in this decision was performed by direct path reads, git plumbing, and backlogit SQL. Every finding below cites the exact file or query that produced it."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed. Operator selection was supplied in the session brief ahead of time, so no choice-presentation step was skipped."
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md
  - docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md
  - docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md
source_reviews:
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-08.md
  - docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-08.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-08.md
  - docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-08.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-08.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-08.md
tags:
  - architecture-decision
  - execution-architecture
  - operation-substrate
  - prepare-verify-activate
  - compatibility-normalization
  - portfolio-reslicing
---

# Shared execution architecture, and the precursor-first portfolio that follows from it

## Context

Eight independent plan-review attempts blocked six defect plans. Attempt 08 is
terminal across all six. The aggregate open finding count at content HEAD
`f142173c` is **4 P0, 34 P1, 11 P2**.

Seven prior remediation cycles treated each finding as a local defect and
patched it in place. The plans grew — the six now total **419 KB** — while the
block count did not fall. That is the signature of a wrong frame, not of
insufficient patching effort.

The frame error is this: **all six units assume a shared execution
architecture that does not exist in this workspace, and no unit builds it.**

* `178-S` assumes an executable argv boundary. The consuming surface is a
  Markdown document. (attempt-08 `A1`)
* `180-S` assumes a guarded MCP operation. No `autoharness` MCP server exists.
  (attempt-08 `B3`)
* `176-S` assumes an installed `harness-architect` and a Ship pre-task phase.
  Neither is installed. (attempt-08 `B1`)
* `179-S` assumes an atomic recorder. Every writer in the portfolio is
  multi-step and interruptible. (attempt-08 `B3`, `B5`)
* `177-S`, `179-S` assume template/mirror atomicity while decomposing the pair
  into separately-committable tasks. (attempt-08 `B7`)

Each plan then specifies the *consumer* of a producer that no plan creates.
This is precisely the failure mode
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
records: clauses that review clean in isolation, composing into a state no
legitimate execution can reach.

This decision stops the symptom patching and decides the architecture first.

### Session degradation declared

Engram's circuit is open and was not retried. Intercom is unavailable. All
research below was performed by direct read, `git` plumbing, and `backlogit`
SQL against the live index (1371 artifacts, synced at session start). Every
finding cites the exact artifact that produced it. No finding in this document
rests on semantic search.

### Recovery gate

`backlogit_list_checkpoints(consumer_id=stage)` returned 55 checkpoints, all
`status: resolved`, all `agent: stage`, zero validation or quarantine
anomalies. **ZERO-CANDIDATE NORMAL STARTUP**: no recovery candidate exists,
and this session began fresh. Single worktree confirmed
(`git worktree list` → one entry). No active shipments.

---

## Research findings

Each finding is empirical and reproducible from the cited surface.

### F1 — There is no `autoharness` executable operation surface at all

`src/autoharness/cli.py` dispatches on a hand-rolled `argv` table
(`cli.py:2913-2933`). The complete command vocabulary is:

```text
home | version | verify-workspace | gate | telemetry | eval
| setup-vscode | setup-copilot-cli | setup-claude | setup-codex
```

There is **no** operation namespace, no `git` surface, no `checkpoint`
surface, no `plan-review` surface. The internal convention is
`_parse_<name>_args(args: list[str]) -> dict` followed by
`_<name>_command(rest: list[str]) -> None`; `gate` is the established
multi-level example (`_gate_command` → `_gate_check_command`,
`_gate_pre_review_command`, `_gate_size_command`,
`_gate_pipeline_topology_command`, `_gate_dag_readiness_command`).

**Consequence.** Every plan that says "the agent calls the operation" is
naming a callable that does not exist. The substrate is the missing
prerequisite of four of the six units.

### F2 — There is no `autoharness` MCP server, and adding one is not a free action

`.mcp.json` registers six servers: `backlogit`, `engram`, `graphtor-docs`,
`context7`, `tavily`, `github`. **`autoharness` is not among them.**

`pyproject.toml` declares exactly two runtime dependencies:
`jsonschema>=4.23.0` and `PyYAML>=6.0.2`. There is **no MCP SDK**. autoharness
is a PyPI-distributed CLI (`[project.scripts] autoharness =
"autoharness.cli:main"`), so adding a dependency has real distribution blast
radius — a concern this repository has already paid for once
(`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`).

**Consequence.** `180-S`'s "guarded MCP create" and `176-S`'s "MCP parity
boundary" are not underspecified — they are *unresearched*. Choosing between a
hand-rolled JSON-RPC-over-stdio server and an SDK dependency is an
implementation-research question, and this decision refuses to pretend
otherwise. It becomes a **bounded spike** (`S1`), not a plan section.

### F3 — `harness-architect` is a template that was never installed

```text
templates/skills/harness-architect/SKILL.md.tmpl   EXISTS
.github/skills/harness-architect/                  ABSENT
```

`.github/skills/` contains 18 installed skills; `harness-architect` is not one
of them. Yet `.github/policies/workflow-policies.md` P-004 declares
`Applies To: ship (via harness-architect skill)`.

**The installed policy already names an actor that the installed workspace does
not contain.** `176-S`'s bootstrap did not invent a fictional dependency; it
faithfully inherited one from the policy. Fixing the plan without installing
the actor cannot succeed.

> **Current state (revision 6).** This finding is **closed by fact, not by a
> shipment.** `.github/skills/harness-architect/SKILL.md` was installed and
> manifest-registered by the elective harness-maintenance commit `07b4be79`, so
> the actor P-004 names now exists in this branch's publication baseline. The
> finding above is preserved as the truthful observation it was when taken.

### F4 — P-004 already requires compilation; the plan's gate dropped it

Verbatim from `.github/policies/workflow-policies.md`:

> **Precondition**: `python -m py_compile src/autoharness/cli.py` exits 0 AND
> `PYTHONPATH=src python -m unittest discover -s tests` exits non-zero with
> expected failure markers in the output for every test function.
>
> **Postcondition**: The harness manifest records `Compilation: PASS` and
> `Red Phase: CONFIRMED`.

The attempt-08 P0 (`A1`, "the atomic public P004 gate omits compilation") is
therefore a **regression against the live policy**, not a gap in it. The gate
must observe three independent channels — compilation, collection, outcomes —
because the policy's own postcondition has two of them.

### F5 — The live manifest corpus is two divergent families, not one closed shape

Seven live verdict manifests exist in `docs/reviews/`. Their top-level key sets
are **not** uniform:

| Family | Count | Distinguishing keys |
|---|---|---|
| A — attempt-roster | 6 | `plan_id`, `latest_attempt`, `review_terminal`, `awaiting_attempt`, `gate_result`, `verdict`, `remediation_authorization`, `latest_remediation_revision`, `latest_disposition`, `latest_artifact`, `attempts`, `carried_forward_context` (21 keys) |
| B — cycle-record | 1 | `source_decision`, `decision_revision`, `source_stash_id`, `deferred_scope_expansions`, `review_cycle`, `review_cycles_remaining`, `review_cycle_authorization`, `dispatch_mode`, `decision` (17 keys) |

Family B is `2026-09-17-closure-evidence-naming-contract-plan-review.md`, which
governs `175-S` — a shipment this session must not mutate.

`179-S`'s proposed **closed eight-key format** would reject *all seven*. The
attempt-08 findings `B1` (closed format rejects live manifests) and `B2`
(pre-review nulls) are two instances of one root cause: **a canonical format
was specified without a normalization layer beneath it.**

### F6 — The checkpoint corpus contains observed torn writes

134 checkpoint records exist (`.backlogit/checkpoints/` 60,
`.backlogit/archive/checkpoints/` 75, minus overlap). Two fail to parse:

```text
checkpoint-20260821-203531.json  4975 B  Unexpected end when deserializing object. Path 'context', position 4975
checkpoint-20260901-002917.json  5445 B  Unexpected end when deserializing object. Path 'progress', position 5445
```

Both truncate at **exactly the file length**, mid-object. These are not corrupt
bytes — they are **partial writes from a non-atomic writer**, captured in the
historical record.

This is decisive for two separate findings. It makes `180-S`'s `B4` (scanner
input hardening) an *observed* condition rather than a hypothetical, and it is
direct field evidence that the atomic-writer requirement (`179-S` `B3`/`B5`) is
load-bearing rather than theoretical.

`backlogit_create_checkpoint`'s current contract is also now known precisely:
at `schema_version: 1` the top level and `progress` are a **closed** namespace
(`schema_version`, `agent`, `session_id`, `phase`, `status`, `created_at`,
`updated_at`, `context`, `progress`, `resume_hint`; `progress` limited to
`tasks_completed`, `tasks_remaining`, `files_modified`, `decisions`), while
`context` is **open**. A record with no `schema_version` is written verbatim
with no validation — which is exactly how legacy records entered the corpus.

### F7 — The review-verdict consumer inventory is closed, enumerable, and small

Searching every tracked `.md`, `.tmpl` and `.py` under `.github/`,
`templates/`, `src/` and `scripts/` for `decision: PASS|FAIL|ADVISORY`,
`verdict_manifest`, `latest_attempt`, or `gate_result` returns exactly four
surfaces:

```text
templates/skills/harvest/SKILL.md.tmpl        (authoritative)
templates/skills/plan-review/SKILL.md.tmpl    (authoritative)
.github/skills/harvest/SKILL.md               (installed mirror)
.github/skills/plan-review/SKILL.md           (installed mirror)
```

`.autoharness/staging/` also contains copies, but `.gitignore:6` excludes
`.autoharness/staging/` — it is a **generated verify-workspace artifact, not a
mirror**, and must be excluded from every inventory by rule rather than by
oversight.

This retires attempt-08 `B4` on `179-S` ("the consumer graph is stale") and
`B5` on `180-S` ("the producer inventory is unsatisfiable"): an inventory
defined as *tracked files matching a marker set, minus generated paths* is
both complete and mechanically recomputable.

**And it confirms the P0.** `.github/skills/harvest/SKILL.md` Phase 1 step 4
reads:

> Locate the latest `## Plan Review` section and require literal
> machine-readable markers: `dispatch_mode:` and `decision:`.
> … `decision: PASS` — proceed.

Harvest reads an **inline marker inside the plan document**. It never opens the
verdict manifest. A stale inline `PASS` admits a plan to decomposition today.

### F8 — The Ship tool allowance is a wildcard, and narrowing it is already-proven syntax

`.github/agents/_ship.agent.md` frontmatter:

```yaml
tools: vscode, execute, read, agent, edit, search, web, 'microsoft-docs/*',
  'backlogit/*', ms-python.python/getPythonEnvironmentInfo, ... , todo
```

`'backlogit/*'` matches `backlogit_create_checkpoint`. Any guard on a wrapped
create is optional while the wildcard stands (attempt-08 `A1` on `180-S`).

Critically, **the same frontmatter already demonstrates per-tool enumeration**
(`ms-python.python/getPythonEnvironmentInfo` and three siblings). Narrowing
`backlogit/*` to an explicit allowlist is therefore a known-feasible edit in
proven syntax — it needs no spike. `.mcp.json`'s `"tools": ["*"]` for the
`backlogit` server is the second half of the same surface and must be narrowed
in the same activation.

### F9 — The current DAG is a false star

`item_deps` carries exactly five edges among the six defect shipments:

```text
177-S → 176-S      178-S → 176-S      179-S → 176-S
180-S → 176-S      181-S → 176-S
```

No other edges exist among them. `176-S` is a P-004 *policy* correction. It is
not a technical prerequisite of branch resolution, of the review-authority
contract, of the checkpoint contract, or of external binary conformance. The
star encoded an execution-ordering preference as a technical edge — the same
class of error revision 3 of the superseded decision corrected once already
when it withdrew the serial chain.

Two further pre-existing edges cross this scope and are **left untouched**:
`168-S → 176-S` and `167-S → 168-S`. They belong to the older SHIP-10 chain.

### F10 — The executable records carry three source IDs that do not exist

Scanning `.backlogit/stash.jsonl` (110 entries) and
`.backlogit/archive/stash.jsonl` (240 entries):

| ID | In stash files | Cited by |
|---|---|---|
| `3EF5AAF2` | 2 hits | plan frontmatter (correct) |
| `14F4D6F3` | 2 hits | plan frontmatter (correct) |
| `86498B64` | 3 hits | plan frontmatter (correct) |
| `76EBDE6D` | 5 hits | plan frontmatter (correct) |
| `C9CD24F3` | 6 hits | plan frontmatter (correct) |
| `7F9CB5E9` | 3 hits | plan frontmatter (correct) |
| `71200CBB` | 2 hits | plan frontmatter (correct) |
| `3EF5AAF9` | **0 hits** | `169-F`, `177-S`, eight `169.x` tasks |
| `2A7C48A8` | **0 hits** | `172-F`, `180-S`, `172.x` tasks |
| `4CE5D4D6` | **0 hits** | `173-F`, `181-S`, `173.x` tasks |

All three phantom IDs are single-character or wholesale corruptions of a real
neighbour. They are corrected under Stage's own backlog authority in this
session; the review cycle that recorded them was evidence-only and could not.

---

## Options evaluated

### Option 1 — Continue local remediation (ninth cycle)

Patch each attempt-08 finding where it was raised, in the existing six plans.

* **Cost**: lowest per-finding.
* **Evidence against**: seven cycles of this produced 419 KB of plan text and
  did not reduce the block count. Findings `A1` on `178-S` and `B3` on `180-S`
  cannot be patched locally at all — they name producers that do not exist, and
  no edit to a consumer creates its producer.
* **Verdict**: **rejected.** Mechanically incapable of closing 2 of the 4 P0s.

### Option 2 — Markdown-level hardening with documented discipline

Keep every surface in Markdown. Harden by prose contract: require agents to
validate before interpolating, require paired template/mirror edits by
convention, require manifest reads by instruction.

* **Cost**: low. No new Python, no new distribution surface, no spike.
* **Evidence against**: this *is* the current architecture, and it is what
  produced the defects. A Markdown agent cannot promise `shell=False` because
  it does not execute — the model composes a shell string. Attempt-08 `A1` on
  `178-S` states this exactly. Paired-edit "atomicity" by convention is
  defeated by any decomposition into two tasks (`B7` on `179-S`). Discipline is
  not a gate; it is a wish with a checklist.
* **Verdict**: **rejected.** It cannot produce an executable boundary, and
  every control it offers is advisory.

### Option 3 — Python-backed operation substrate with PREPARE/VERIFY/ACTIVATE rollout **(CHOSEN)**

Move every safety-critical boundary into typed, atomic Python operations in
`src/autoharness/`, exposed through the existing CLI dispatch and through a
real MCP/sidecar surface that calls the *same* functions. Markdown agents
invoke operations by name and never receive or interpolate the sensitive value.
Roll every contract out as inert PREPARE, evidential VERIFY, then a single
atomic ACTIVATE commit.

* **Cost**: highest. Requires a substrate that does not exist, a resolved MCP
  transport question, and a reordering of the entire portfolio.
* **Evidence for**: it is the only option under which `178-S`'s P0 has a
  fix (the branch name stops crossing the agent surface entirely), `180-S`'s
  `B3` has a server, `176-S`'s bootstrap has an installed actor, and
  `179-S`'s atomicity claim has a writer. The CLI dispatch convention it builds
  on is already proven by `gate`'s five subcommands.
* **Verdict**: **chosen**, per operator authorization.

### Option 4 — Adopt an external workflow engine

Delegate atomicity, state machines and rollout to a third-party orchestrator.

* **Evidence against**: the defects are in *this* repository's contracts, which
  an engine would still have to encode. It adds a dependency larger than the
  problem, and this workspace has a recorded lesson about layering protocols
  over a third party's state machine without validating the composition
  (`docs/compound/2026-09-06-...-state-machine-validation.md`).
* **Verdict**: **rejected.** Wrong blast radius; does not address the frame.

### Comparison

| Criterion | Opt 1 local patch | Opt 2 Markdown discipline | **Opt 3 operation substrate** | Opt 4 external engine |
|---|---|---|---|---|
| Closes `178-S` P0 (argv boundary) | No | No | **Yes** | Partial |
| Closes `180-S` P0 (raw create) | No | No | **Yes** | No |
| Closes `179-S` P0 (Harvest bypass) | Partial | Partial | **Yes** | No |
| Closes `176-S` P0 (compilation) | Yes | Yes | **Yes** | Yes |
| Provides a real atomic writer | No | No | **Yes** | Yes |
| Template/mirror atomicity enforceable | No | No | **Yes** | No |
| Agent/MCP parity possible | No | No | **Yes** | Yes |
| Compatible with 7 live manifests | No | n/a | **Yes** (normalization) | No |
| Compatible with 134 checkpoints incl. 2 torn | No | n/a | **Yes** (quarantine) | No |
| New distribution risk | None | None | **Bounded, spiked** | High |
| Honest about unknowns | No | No | **Yes** (2 spikes) | No |

---

## Decision

### D1 — The safe executable boundary is a Python operation, not an agent instruction

A **safe operation** is a pure Python function in `src/autoharness/ops/` that:

1. takes typed parameters and returns a typed result object — never a string
   to be re-parsed;
2. performs all filesystem writes through the atomic write primitive
   (`temp file in the destination directory → fsync → os.replace`);
3. performs all subprocess execution through the fixed-argv primitive
   (`subprocess.run(argv_list, shell=False, ...)`) with a per-operation
   allowlist of executables, and never through a shell;
4. resolves every path through the containment primitive, which rejects any
   resolved path outside the declared workspace root;
5. is registered exactly once in an operation registry, from which **both**
   transports are derived.

Two transports, one implementation:

* **CLI** — `autoharness op <namespace> <operation> [--flags]`, following the
  established `_parse_*_args` / `_*_command` convention that `gate` already
  demonstrates across five subcommands.
* **MCP/sidecar** — a real `autoharness` server registered in `.mcp.json`,
  whose tool handlers call **the identical registered functions**. Parity is
  asserted by a test that enumerates the registry and requires both transports
  to expose the same operation set with the same parameter names.

**Markdown agents invoke operations. They never promise `shell=False`, never
receive an untrusted value they must escape, and never interpolate one into
prose that a model will compose into a command.**

This is the load-bearing reframe for `178-S`. The plan tried to make
`selected_branch` safe *as it passes through* the Ship agent. The correct fix
is that `selected_branch` never passes through the Ship agent at all: the agent
calls `autoharness op git ensure-branch --shipment <ID>`, and the operation
resolves, validates and applies the branch entirely inside Python. A value the
agent never holds is a value the agent cannot mis-escape.

The transport half of this is **gated on spike `S1`** (F2): the choice between
a hand-rolled JSON-RPC stdio server and an MCP SDK dependency has real
distribution consequences and has not been researched. Deciding it inside a
plan would be exactly the pretence this decision exists to stop.

### D2 — The rollout invariant is PREPARE → VERIFY → ACTIVATE

Every contract in this portfolio rolls out in three phases.

**PREPARE** — author the implementation and its tests **inert**. Inert means:
no existing consumer calls the new code, no policy clause references it, no
registry entry resolves to it, no gate observes it. The workspace's live
behaviour is byte-identical before and after a PREPARE task. Tests go RED
first, then GREEN, entirely within the inert surface.

**VERIFY** — produce the complete evidence set before any activation:
RED evidence (each new assertion observed failing, against an implementation
that does not yet satisfy it), GREEN evidence (the same assertions observed
passing), and compatibility evidence (every pinned fixture from D3 processed
without error). VERIFY produces an evidence record; it changes no behaviour.

**ACTIVATE** — **one task, one commit**, flipping every surface simultaneously:

* every authoritative template under `templates/`
* every installed mirror under `.github/`
* the backlog registry `.autoharness/backlog-registry.yaml`
* every permission and tool declaration (agent frontmatter, `.mcp.json`)
* every consumer identified by the F7 inventory rule

> **Sequential task edges are not atomic.** A dependency edge from task *A* to
> task *B* permits a commit — and therefore a reachable repository state —
> between them. Any pair of surfaces that must never disagree belongs in **one
> task**, not in two tasks joined by an edge.

This retires attempt-08 `B7` on `179-S` and the `T1`/`T2` shape on `177-S` by
construction, and it is the direct application of the recorded lesson that a
template and its installed mirror must move "in the same commit"
(`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
Lesson 1).

### D3 — Compatibility is explicit versioned normalization, then strict canonical validation

No canonical schema in this portfolio validates a raw historical record.
Every reader is two stages:

```text
raw record ──▶ normalize(record) ──▶ canonical form ──▶ strict validation
                     │
                     └── unnormalizable ──▶ QUARANTINE (typed, not an exception)
```

`normalize()` is **versioned and total**. It accepts every shape in the pinned
corpus and emits either a canonical record or a quarantine record carrying the
reason. It never raises on malformed input, and it never silently drops a
field.

**Pinned compatibility fixtures** (frozen copies, committed, never regenerated
from live data):

* **Manifests** — all seven live verdict manifests: the six Family-A
  attempt-roster manifests and the one Family-B cycle-record manifest (F5).
  The decision says "six real manifests"; research found a seventh of a
  different shape, and it is pinned too, because a normalizer that has never
  seen Family B will meet it in production on `175-S`.
* **Pre-review state** — a synthetic Family-C manifest with `latest_attempt:
  null`, `latest_artifact: null`, `attempts: []`. This is the legitimate state
  of a plan authored but not yet reviewed, and a closed required-everything
  format makes it unrepresentable (attempt-08 `B2`).
* **Checkpoints** — the **full 134-record corpus**, including both torn
  records (F6) and every legacy record lacking `schema_version`.

Strict canonical validation applies only downstream of normalization, and only
to newly authored records.

**Immutable history is never rewritten.** No file under
`docs/reviews/review-history/` is modified by any task in this portfolio. The
2026-08-21 and 2026-09-01 torn checkpoints are quarantined and reported, never
repaired in place.

### D4 — P-004 bootstraps on a real installed lifecycle, never on an assumption

P-004's bootstrap is a **real, installed Ship pre-task harness-generation
lifecycle**. Concretely:

1. `templates/skills/harness-architect/SKILL.md.tmpl` is installed to
   `.github/skills/harness-architect/SKILL.md` — the actor P-004 already names
   (F3) is made to exist, and is registered in the harness manifest under
   `D11`. **At revision 6 that install is a completed fact**: it was performed
   by the elective harness-maintenance commit `07b4be79`, outside this
   portfolio's pipeline, and the retired precursor `188-S` never executed —
   see D9. `187-S` consumes the installed actor rather than producing it.
2. The Ship agent gains an explicit pre-task harness-generation phase that
   invokes it, in both `templates/agents/_ship.agent.md.tmpl` and
   `.github/agents/_ship.agent.md`, in one ACTIVATE commit.
3. The P-004 gate operation observes **three independent channels** —
   compilation, collection, and per-test outcomes — because the live policy's
   postcondition already records two of them (F4). Absence of an outcome token
   is the distinct result `NO_OBSERVATION`, which is a **failed precondition**,
   never a silent pass.

There is **no waiver, no `--force`, no assumed skill, and no operator policy
edit** anywhere on this path. If the lifecycle is not installed, P-004 fails
closed.

### D5 — External binary conformance moves to isolated Linux CI; `002-C` stays blocked

SAFE_CLOSE conformance against the external `backlogit-linux-amd64` binary runs
**only** in an isolated Linux CI container, under these non-negotiable
conditions: no credentials of any kind in the job environment; network denied
after asset acquisition completes; the repository absent or mounted read-only;
all mounts disposable.

This resolves attempt-08 `B3` (no OS sandbox, TOCTOU/hardlink exposure) and
`B4` (a Windows workstation cannot execute an ELF baseline) by moving the
execution to a platform that can run it under containment, rather than by
asserting the workstation is adequate.

Three hard boundaries:

* **`002-C` remains `blocked` and outside every shipment manifest**, directly
  and transitively. No dependency edge in either direction.
* **No administrative-close workaround ships** until a supported, tested
  transition *and* a tested rollback exist. Attempt-08 `B7` showed the proposed
  interim close was routed through the very operation the fixtures measure as
  refusing the transition, with a rollback that contradicted the plan's own
  no-direct-edits, no-approval and lock constraints. None of that is
  recoverable by rewording. **No such transition exists today, so the local
  shipment scope is evidence and documentation only.**
* The CI isolation mechanism itself (egress denial after acquisition, read-only
  checkout, disposable mounts on GitHub-hosted runners) is **not known** and
  becomes bounded spike `S2`.

### D6 — Composed state machines are reviewed before harvest, not after

No gate is harvested into executable tasks until its composed state machine is
written down and checked. Every gate declares, in one table:

| Field | Requirement |
|---|---|
| Pass state | Exactly one, and demonstrably **reachable** by a legitimate execution |
| Fail state | Exactly one, and distinct from "no observation" |
| Producer | A named, existing artifact that emits the observation |
| Consumer | A named, existing artifact that reads it |
| Activation commit | The single ACTIVATE task that makes producer and consumer agree |

A gate whose pass state no legitimate state can satisfy is the exact defect
recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`.
A gate whose consumer activates before its producer exists is attempt-08 `B2`
on `180-S` and `B3` on `176-S`. Both are now checked before harvest rather than
discovered at review.

### D7 — Two bounded spikes, because two blockers require implementation research

This decision refuses to write a plan over an unresearched mechanism.

* **`S1` — autoharness MCP/sidecar transport.** Decide hand-rolled JSON-RPC
  stdio versus an MCP SDK dependency; measure the wheel/distribution impact
  (F2); define the `.mcp.json` registration; define the CLI/MCP parity test.
  **Gates the transport half of the substrate.** Without it, every "MCP parity"
  claim in this portfolio is unfounded.
* **`S2` — network-denied Linux container conformance isolation.** Determine
  whether GitHub-hosted runners can deny egress after asset acquisition, mount
  the repository read-only or omit it, and provide disposable mounts; if not,
  determine the supported alternative. **Gates SAFE_CLOSE conformance
  execution.**

Both are time-boxed and produce a findings artifact, not code.

### D8 — Precursor-first DAG; the false star is withdrawn

The `176-S` star (F9) is withdrawn. The new graph's roots are the two spikes
and the two defect units that genuinely need no foundation.

At revision 2 the graph below was amended by D9 and D10: `188-S` (BOOTSTRAP-0)
became a declared root and every code-bearing implementation shipment depended
on it; `P1`/`184-S` and `181-S` are **withheld by archival** as conditional
future units; and the `P4 → P1` edge is removed.

At **revision 6** the `188-S` layer is **removed entirely**. The
`harness-architect` actor was installed directly by the bounded Auto-Tune
harness-maintenance commit `07b4be79`, so `188-S` is retired and archived (D9
below) and every edge that existed only to await that installation is deleted.
`187-S`, whose sole prerequisite was `188-S`, becomes a declared `dag-root`.
Current graph:

```text
P2(185-S) ─┬─▶ P3(186-S)
           ├─▶ 178-S
           ├─▶ 180-S
           └─▶ 176-S ◀─┐
P4(187-S) ─────────────┘   (root — dag-root)

P2(185-S) ─▶ [P1 / 184-S : WITHHELD, archived, pending TRANSPORT_DECIDED]
S1(182-S)  (root — dag-root)   ⇢ authorizes re-harvest of 184-S only
S2(183-S)  (root — dag-root)   ⇢ authorizes re-harvest of 181-S only
177-S      (root — dag-root)
175-S      (root — dag-root)
187-S      (root — dag-root)

[181-S : WITHHELD, archived, pending an authorizing isolation verdict]
[188-S : RETIRED, archived — externally satisfied by 07b4be79, never executed]
```

**Root status is a graph fact, never an execution authorization.** `187-S`
being a root means no shipment must ship before it. It does **not** mean its
tasks may be claimed: ordinary pre-claim, this unit's own P-002/P-004 harness
generation over its own implementation tasks, independent review, CI and
closure all remain in force and unmodified.


The `⇢` arrows are **not DAG edges**. They are Stage re-harvest authorizations
consumed by a human-run staging session, precisely because a `blocks` edge
cannot enforce a verdict token. The pre-revision-2 graph was:

```text
S1 ─▶ P1 ─┬─▶ P2 ─┬─▶ P3
          │       ├─▶ 178-S
          │       ├─▶ 180-S
          │       └─▶ 176-S ◀─┐
          └─▶ P4 ─────────────┘
S2 ─▶ 181-S
177-S   (root — no precursor)
```

Edges express **real prerequisites only**:

* `P2 → 178-S` — the ensure-branch operation needs the fixed-argv primitive.
* `P2 → 180-S` — the guarded checkpoint operation needs the atomic writer and
  the bounded reader.
* `P2 → P3` — the atomic review recorder needs the atomic writer.
* `P2, P4 → 176-S` — the P-004 gate needs the compile/collect observation
  primitives *and* the installed harness-architect lifecycle.
* `S2 → 181-S` — conformance cannot be specified before isolation is known.
* `177-S` and `181-S` have **no edge to each other and none to `176-S`.** They
  are independent successors and must not be serialized.

`168-S → 176-S` and `167-S → 168-S` are pre-existing edges from the older
SHIP-10 chain and are **left exactly as they are**. `169-S` and `175-S` are not
touched.

At revision 2, `177-S` "root — no precursor" is made **mechanically
effective**: `177-S`, `182-S` and `183-S` now carry the `dag-root` label, and
the stale `dag-root` on `176-S` — which declared itself *not* a root while
carrying explicit edges — is removed. The `pre_claim` gate derives root
provenance only from a recorded `dag-root` label or from `genesis`, and
`genesis` applies only when a workspace holds exactly one shipment record
(live and archived together). This workspace holds hundreds, so an undeclared
edge-less shipment blocks as `unsequenced` rather than passing as a root. A
root that is stated only in prose is therefore not a root. (PR #457 threads
`PRRT_kwDORzpWpM6kHrxD`, `PRRT_kwDORzpWpM6kHrxY`, `PRRT_kwDORzpWpM6kHrxc`.)

### D9 — The harness-architect actor is installed and behaviourally conformant; every bootstrap and corrective precursor is retired (revision 7)

D4 decided *that* the actor must really exist. It did not decide *how the first
one gets built*, and PR #457 review thread `PRRT_kwDORzpWpM6kHrw5` showed the
omission was fatal: `187-S`, the unit that installs the lifecycle, **could not
reach execution at all** — its tasks write Python under `src/`, so P-002/P-004
demand a harness-ready state whose only declared producer was the actor `187-S`
itself was to install.

#### Current state: the actor is structurally present **and** behaviourally conformant

The actor was never built by any shipment in this portfolio. It reached its
current, conformant state through **three commits on this branch, none of them
a shipment execution**:

| Commit | What it established |
|---|---|
| `07b4be79263252b1820701fd123d0aed85c1db2a` | **Structural installation.** *"chore(harness): install harness architect skill"* — an elective harness-maintenance action that created `.github/skills/harness-architect/SKILL.md` and registered it in `.autoharness/harness-manifest.yaml` in the same commit, satisfying `D11` at the installing commit rather than by later fixup. |
| `1cb0dc8140a809d63c3193d58431cd14408788b7` | **Behavioural correction.** Ship review remediation: replaced the installed Step 5.2 `pytest` invocation with the canonical command, mirrored the change into the authoritative template with placeholders preserved, strengthened the red-phase guardrail to require per-test expected-marker correlation, added the contract test, and refreshed the manifest checksum in the same commit. |
| `b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3` | **Behavioural completion.** Seeded the manifest variable the render requires, closing the last divergence between the rendered template and the installed mirror. |

**Structural installation and behavioural conformance are distinct properties
and this decision keeps them distinct.** `07b4be79` is recorded as structural
installation ONLY and never as evidence of P-004 conformance. Conformance rests
on `1cb0dc81` and `b8ac632a`, evidenced by the canonical suite running **2358
passed / 0 failed / 54 skipped** with manifest parity holding.

#### The revision-6 corrective unit is retired, and its diagnosis was wrong

Revision 6 recorded the actor as structurally installed but behaviourally
non-conformant, attributed that to an **install-time variable precedence
defect**, and harvested a corrective release unit — `191-S` / `185-F` /
`185.001-T`…`185.006-T` — to fix it.

**That diagnosis is withdrawn as false.** `_derive_template_variables` already
treats the manifest's `variables_used` as authoritative: profile-derived
defaults are applied through `setdefault`, which is a no-op once the manifest
key exists. There was no precedence defect to correct. The actual defects were
a **stale installed render** and a **manifest variable that was never seeded at
all** — both fixed directly by `1cb0dc81` and `b8ac632a`.

`191-S`, `185-F` and `185.001-T`…`185.006-T` are therefore **archived as
RETIRED**. They were **never claimed by Ship, never executed and never
shipped**; no task passed through any lifecycle phase and no ACTIVATE commit
was authored under them. Two independent grounds support the retirement, and
either alone would suffice:

* **Externally satisfied.** The deliverable exists, correctly, through the two
  Ship commits above.
* **Structurally unexecutable.** Independent plan-review attempt 08 finding
  `S26` (P0) held that `191-S` could never have cleared its own gates: it
  needed a conformant actor in order to generate the harness that would make it
  claimable, and its own purpose was to produce that conformant actor. Removing
  the `187-S → 191-S` edge dissolves a **circular** dependency, not merely a
  satisfied one.

**Nothing in this decision may be read as claiming `191-S` shipped.**

#### The superseded P-004 defect graph is retired pending fresh re-harvest

`176-S`, `168-F` and every live `168.00x-T` / `168.01x-T` task encoded the
**superseded** P-004 gate design — a caller-supplied declaration document with
an `expected_green_characterization` set, an `autoharness gate p004` entrypoint
that does not exist, and a skill contract keyed to both. Independent
plan-review attempt 01 finding `O1` (P0) held that leaving those records live
while deferring them in prose is insufficient, because **a queued shipment
manifest is an executable instruction set, not commentary**.

They are **archived as RETIRED, superseded, never claimed and never executed**.
The original defect linkage is preserved on each archived record: **the
requirement survives; only the carrier does not.**

**Re-harvest is forward-only.** The P-004 gate is re-harvested **fresh** by
Stage against the then-current repository state — a new feature, new tasks and
a new shipment — and **only** after `185-S` and `187-S` have actually shipped
and the governing plan holds an independent PASS. The archived records are
**never restored**, no empty queued shipment is created in the interim, and no
restoration of any other archived unit may revive `191-S`, `176-S` or `168-F`.

#### The admission apparatus remains superseded, and no exception survives

The `PRE-0` / staged-`harness-ready` construction existed for exactly one
purpose: to build the **first** actor through a pipeline that already required
it. The actor now exists and is conformant, so that construction has **no
remaining subject**. Accordingly, and without substitution:

* **`PRE-0` is withdrawn as an execution path.** It is not re-described, not
  re-scoped and not carried forward. No step of any live record performs it.
* **The four authored `harness-ready` labels are withdrawn** as invalid live
  queue semantics, removed together with the records they were authored to
  admit.
* **No P-004 bootstrap exception is preserved, revived or invented.** There is
  no carve-out, no grant, no `--force`, no force-audit entry, no expiring
  authority and no self-authorization anywhere on this path. The revision-3
  claim carve-out — withdrawn at revision 4 because P-002's Enforcement
  mechanically filters Ship's ready queue and backlog prose cannot waive an
  installed filter — stays withdrawn and is **not** reinstated in any form.
* **Every remaining unit is subject to the ordinary, unmodified gates**,
  satisfied by each unit's **own** harness generation at claim time against the
  now-conformant actor. If a unit's harness is not generated, P-004 still fails
  closed.

#### `188-S` / `182-F` remain retired and never executed

`188-S`, `182-F` and `182.001-T`…`182.004-T` stay **archived** with
`archived_status: queued` — the status they actually held. They were **never
claimed, never executed and never shipped**, no composed-state token was ever
written to `.autoharness/gates/harness-architect-bootstrap.txt`, and **nothing
here may be read as claiming their planned TDD lifecycle ran.**

#### What is preserved

Historical review evidence is **immutable and untouched**: independent
plan-review attempts 01–08 across the affected plans, the Stage targeted
terminal review, and the `PRE-0` evidence artifact
`docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md`
remain exactly as written. They are truthful records of observations taken
**during planning**; they are **not** execution evidence for any unit and never
became any. The governing plan
`docs/plans/2026-09-20-harness-architect-bootstrap-plan.md` is retained as a
**superseded / completed-externally decision record**, not as a live executable
plan, and its verdict manifest is terminal, superseded and **non-authorizing**,
asserting **no PASS** for plan revision 5, which was never independently
reviewed.

#### Graph effect

Every `188-S` edge existed **solely** to await actor installation, so every such
edge is **removed**: from `176-S`, `178-S`, `180-S`, the archived `184-S`,
`185-S`, `186-S` and `187-S`. The `187-S → 191-S` edge added at revision 6 is
**withdrawn** with the unit that created it. **All non-`188`, non-`191`
technical dependencies are preserved unchanged** — `178-S → 185-S`;
`180-S → 185-S`; `184-S → 182-S`; `185-S → 184-S`; `186-S → 185-S`.

**`187-S` is an explicit `dag-root`.** It declares an **empty dependency set**
and carries the `dag-root` label so `pre_claim` derives `declared_root` rather
than blocking as `UNSEQUENCED_SHIPMENT`. Its only remaining prerequisite — a
conformant actor — is satisfied in the same publication branch, and the
never-technical `184-S` edge remains withdrawn: `181-F` consumes no operation
registry, result model or transport.

**Root status confers no task claim.** `187-S`'s root status means no shipment
must ship before it — nothing more. Execution still requires ordinary
pre-claim, its own P-002/P-004 harness generation over its actual
implementation tasks, independent review, CI and closure. `184-S` remains
conditionally withheld on `TRANSPORT_DECIDED`; `185-S` alone retains its
technical edge on `184-S`, which is why `185-S`, and transitively `186-S`,
`178-S` and `180-S`, stay unclaimable. That is the correct fail-closed outcome
and is entirely unaffected by the actor's installation or conformance.

**One consequence is recorded rather than silently repaired.** `168-S` — an
unrelated shipment that carries the `160-F` family and is **not** a member of
the retired `168-F` task graph — declares `dependencies: ['166-S', '176-S']`.
Retiring `176-S` leaves that edge pointing at an archived record, so `168-S`
becomes unclaimable. The edge is **preserved, not deleted**: it is a truthful
statement of what `168-S` was sequenced behind, deleting it would be an
unreviewed scope expansion, and fail-closed unclaimability is the safe outcome.
Resequencing `168-S` requires its own operator direction.

### D11 — Manifest-tracked installed artifacts are registered in the same atomic unit that creates or modifies them

The current-HEAD review of Push A found the same false contract in six
authoritative carriers: an activation that creates or modifies an installed
artifact tracked in `.autoharness/harness-manifest.yaml`, declared as "one
commit, *N* files, nothing else", with the manifest refresh omitted. Such a
commit leaves the manifest's recorded checksum describing a file that no longer
exists in that form — a silently false installed-state record, and a rollback
unit that does not restore what it claims to restore.

**The invariant, stated once and inherited by every activation in this
portfolio:**

> Any activation that **creates or modifies** an artifact tracked in
> `.autoharness/harness-manifest.yaml` MUST, **in the same commit and the same
> rollback unit**, update or register that artifact's manifest entry — `path`,
> `primitive`, `template` and `checksum` — and MUST then **verify checksum
> parity** between each refreshed entry and the on-disk file it describes. The
> manifest is therefore a member of every such commit, and every "exactly *N*
> files" or "nothing else" statement in the governing plan, feature, shipment
> and task records counts it.

**Scope, stated precisely so the invariant is not over-applied:**

* It binds on **installed artifacts only**, and the binding is stated as a
  **membership rule, not a cardinality**: an artifact is covered **if and only
  if `.autoharness/harness-manifest.yaml` carries an entry for it under the
  `artifacts:` key**, whatever the number of such entries happens to be at any
  moment and whatever directory that path sits in. **THE ENTRY COUNT IS NOT
  LOAD-BEARING AND IS DELIBERATELY NOT RESTATED HERE**: the manifest grows and
  shrinks as the harness is installed, tuned and retired, so any count written
  into this prose goes stale without any decision changing. **MEMBERSHIP IS
  ALSO NOT A PATH-PREFIX RULE**: the tracked set is not confined to `.github/`
  and `.autoharness/` — it includes repository-root files and other tracked
  directories — so coverage MUST be decided by looking the path up in the
  `artifacts:` key and never by inspecting its directory.
* It does **not** bind on `templates/`. No template path is manifest-tracked
  (zero entries), so a template edit carries no manifest obligation and a
  template-and-mirror pair refreshes **one** entry, not two.
* It does **not** bind on untracked paths that merely live under `.github/` —
  `.github/workflows/ci.yml` and `.mcp.json` are not manifest entries and are
  not covered.
* It does **not** change any `declared_surface_count` or surface-enumeration
  rule. Where a unit enumerates declared surfaces by a rule that excludes
  `.autoharness/` (as `169-F`'s rule does), the manifest refresh is a **commit
  member, not a declared surface**, and the digest inputs, freshness bindings
  and resolved-surface counts built on that rule are unchanged.

**Where the obligation is discharged.** In the same ACTIVATE task that performs
the installed-artifact write. Where a unit has a post-activation confirmation
step, checksum parity is re-observed there as well; where it has a VERIFY step
that re-derives installed/template parity, that step also re-derives manifest
parity.

**Rollback.** Because the manifest entry and the artifact move in one commit, a
single-commit revert restores both together. A revert that restored the artifact
without the entry, or the entry without the artifact, is precisely the divergent
state this invariant removes.

**Where the invariant is now stated, and where it is deliberately not.** `D11`
binds every activation in this portfolio, and each governing plan states it at
its own ACTIVATE step with that unit's exact entry count: `177-S` (two),
`178-S` (one), `187-S` (one), `186-S` (two), `180-S` (two), `184-S` (two) and
`176-S` (two). `181-S` is **not** covered and this is a finding, not an
omission: its activation touches `.github/workflows/ci.yml` and `docs/`,
neither of which is manifest-tracked, so it creates no obligation.

`188-S`'s one-entry *registration* of
`.github/skills/harness-architect/SKILL.md` is **removed from that list at
revision 6**, because that unit is retired and never executed. The obligation
it described was nevertheless **discharged exactly as `D11` requires**, by the
installing commit `07b4be79` itself: the artifact and its `artifacts:` entry —
`path`, `primitive`, `template` and `checksum` — landed in the **same commit
and the same rollback unit**, and checksum parity holds against the on-disk
file at
`49f6bae3945bf823aecbe959fa38197c05325d19b14d5608e5b0b47eeda41716`. `D11` is
therefore satisfied for that artifact at the publication baseline, and no unit
in this portfolio carries a residual registration obligation for it. **The
invariant itself is unchanged in substance by this revision.**

`178-S` was omitted from that list in revision 4 and is restored here, because
its branch-ensure activation is an ordinary `D11` case and not an exception.
Its governing plan, `docs/plans/2026-09-18-branch-ensure-operation-plan.md`
(revision 3), activates **two surfaces** — the Ship agent template
`templates/agents/_ship.agent.md.tmpl` and its installed mirror
`.github/agents/_ship.agent.md` — of which **only the installed mirror is
manifest-tracked**, because `.autoharness/harness-manifest.yaml` tracks no
template. Its entry count is therefore **one refreshed entry** — a *refresh*,
not a registration, because the `artifacts:` entry recording
`.github/agents/_ship.agent.md` already exists and carries a digest of the
pre-activation content — and its ACTIVATE commit contains **three files**: the
two edited Ship surfaces plus that single manifest entry. The manifest member is
a **commit member, not a third surface**. It is refreshed to the sha256 of the
mirror *as written by that commit*, in the same commit and the same rollback
unit, followed by a checksum-parity re-digest; no other manifest entry may be
created, refreshed or rewritten. This correction is **decision-only**: the
branch-ensure plan already states this contract at revision 3, so no plan and no
task record changes, and the three-files / one-refreshed-entry shape stated here
is identical in substance to the one `187-S`'s lifecycle carriers state for the
same mirror.
`185-S` has no ACTIVATE step at all.

At **task-record** level the invariant is stated in the records of the units
whose tasks are live and unreserved — `169.015-T`, `180.010-T` and
`181.005-T`. (`182.003-T` and `182.004-T` also stated it; they are retired and
archived at revision 6 and no longer carry a live obligation.) It is **not**
written into the pre-existing task records of `168-F`, `170-F` and `172-F`,
because those units declare task-level decomposition **deferred** and their
existing records **re-sliced** against the delivered foundation surfaces rather
than executed as written. Those records are not authoritative activation
contracts; their plans are, and their plans carry `D11`. Re-harvest inherits it
at the moment those records become authoritative.

**These are future implementation contracts.** `D11` binds the activations
described by these plans and task records. It authorizes **no** edit to
`.autoharness/harness-manifest.yaml` by any staging session, and **no staging
session has made one**. The manifest *has* changed since revision 5, but not on
a staging path and not under this decision's authority: the elective
harness-maintenance commit `07b4be79` registered
`.github/skills/harness-architect/SKILL.md` together with the artifact itself,
in one commit, satisfying `D11` for that entry at the publication baseline.
That is an external harness-maintenance action, is recorded here as fact, and
grants no staging-session manifest authority of any kind.

### D10 — Conditional successors are withheld from the executable queue, not merely ordered (revision 2)

PR #457 threads `PRRT_kwDORzpWpM6kHrxd` and `PRRT_kwDORzpWpM6kHrxK` found that
`184-S` and `181-S` had been **harvested prematurely**. D7 said the spikes gate
them; the graph could not express it.

**Why an edge cannot carry a verdict.** A `blocks` edge is an *ordering*
mechanism, not an *authorization* mechanism: it clears on **predecessor
completion**. `182-S`'s emitter `176.005-T` completes on all three of its
tokens; `183-S`'s emitter `177.006-T` completes on all five of its. Most of
those are non-authorizing. On the edge alone each successor would have become
claimable the moment its spike shipped — *whatever the spike concluded*,
including a state meaning the spike never ran. No installed shipment-claim
predicate reads either findings artifact, and the task-level fail-closed
first-action reads elsewhere in this portfolio (e.g. `169.015-T`'s) are
**intra-shipment** gates between two tasks of one unit, not shipment-claim
gates.

**The decision.** Until such a predicate is genuinely installed, the only
fail-closed representation is that **the successor records do not exist in the
executable queue**. `184-S` + `178-F` + `178.001-T`…`178.006-T`, and `181-S` +
`173-F` + `173.001-T`…`173.011-T`, are **archived** — a repository-supported
backlog operation — with `archived_status: queued`. Their plans are marked
`plan_role: conditional-future` and are **preserved intact and unreduced**.

**No invented status.** A live shipment carrying `blocked` is *malformed legacy
data* under the `pre_claim` live-status vocabulary (`queued`, `active`,
`shipped`, `abandoned`) and fails closed at read time. It is not used.

**Nothing is deleted.** Full plan, feature and task text — including each
record's withholding rationale and re-harvest condition — remains readable
under `.backlogit/archive/`.

**Re-harvest is a Stage act, in a new session, never an edge and never Ship.**

| Verdict token | What Stage may restore |
|---|---|
| `TRANSPORT_DECIDED` (exactly one `COMPOSED_STATE:` line, `absent=0` agreeing with the ledger) | All of `178-F` + its six tasks + `184-S`. |
| `TRANSPORT_UNDECIDED` / `TRANSPORT_NOT_OBSERVED` / malformed / absent | **Nothing.** There is no floor subset for `184-S`: the substrate's transport shape *is* the undecided question, and a partial substrate would inherit the unanswered finding as an assumption. |
| `ISOLATION_CHARACTERIZED` | Every task of `173-F` the findings support. |
| `ISOLATION_FLOOR_ONLY` | **Only** the evidence-and-documentation floor subset, and **only** after a new recorded Stage decision enumerating it task by task. |
| `ISOLATION_CLEANUP_FAILED` / `ISOLATION_UNDETERMINED` / `ISOLATION_NOT_OBSERVED` / malformed / absent | **Nothing.** |

These are the per-state rules `177.006-T` already declares; D10 makes them
structurally binding rather than advisory.

**Downstream consequence, accepted deliberately.** `185-S` genuinely needs
`184-S`'s registry, so it retains that edge and is therefore queued-but-
unclaimable; `186-S`, `176-S`, `178-S` and `180-S` inherit that transitively.
Each record states so explicitly. This is the correct fail-closed outcome: a
portfolio built on an undecided substrate must not be claimable.

---

## State-machine tables

### SM-1 — P-004 red-phase gate (retired carrier; re-harvested fresh)

Reconciled with `docs/plans/2026-09-18-p004-observation-gate-plan.md` **revision
7**. The `expected_green_characterization` set is **removed from the decision
entirely**; the expected-test set is **derived by the gate, never supplied by a
caller**.

| State | Reached when | Terminal |
|---|---|---|
| `RED_CONFIRMED` (pass) | the canonical compile command exits 0, **and** the canonical unittest command exits non-zero, **and** every derived expected harness test fails with its **own** expected marker, **and** no unexpected failure or error exists | yes |
| `RED_NOT_CONFIRMED` (fail) | the commands ran and observation completed, but any derived expectation is unmet — a compile failure, an expected harness test that passes, a marker that does not correlate, or any unexpected failure or error | yes |
| `NO_OBSERVATION` | no trustworthy observation could be taken — discovery failed, a loader error occurred, the derived expected set is empty, or the harness-surface resolver did not return `HARNESS_READY` | yes — classified **fail**, never pass |

**Derivation, not declaration.** Each generated harness test function in the
configured test roots carries a unique sentinel
`raise NotImplementedError("P004:<qualified-test-id>")`. The gate parses those
roots with a safe AST walk, validates that each marker matches the qualified
discovered test ID, and requires at least one. Discovery remains
whole-suite: established unrelated tests may pass, but any unexpected failure,
error or skip **of an expected harness test** blocks.

**Resolver precondition is separate from the gate token.** The harness-surface
resolver's `UNRESOLVED` and `NO_HARNESS` states are preserved as distinct
precondition detail with distinct exit codes; **neither executes any command**,
and both collapse to the final gate token `NO_OBSERVATION`.

Producer: the typed operation `harness/p004-gate`, registered through the
`184-S`-delivered registry and transport substrate and reachable identically as
`autoharness op harness p004-gate` and over MCP.
Consumer: the Ship pre-task harness-generation lifecycle (created in `P4`).
Carrier status: `176-S` / `168-F` are **RETIRED, never executed (D9)**. This
table binds the **fresh** unit that Stage re-harvests once `185-S` and `187-S`
have shipped and the plan holds an independent PASS.
Reachability: `RED_CONFIRMED` is reachable — it is the state the live policy's
postcondition `Compilation: PASS` + `Red Phase: CONFIRMED` already describes.


### SM-2 — Review-authority gate (`P3`)

| State | Reached when | Terminal |
|---|---|---|
| `HARVEST_ADMITTED` (pass) | the normalized manifest for `plan_id` reports `verdict: PASS` at `latest_attempt` **and** `latest_attempt` was taken against the plan's current revision | yes |
| `HARVEST_REFUSED` (fail) | manifest absent, unnormalizable, non-`PASS`, or `PASS` against a superseded revision | yes |
| `MANIFEST_QUARANTINED` | normalization cannot classify the record | yes — classified **fail** |

Producer: the atomic review recorder (`P3`).
Consumer: `harvest` skill, template **and** installed mirror (F7).
Activation commit: `P3` ACTIVATE — migrates all four F7 surfaces at once.
Reachability: `HARVEST_ADMITTED` is reachable; Family-A manifests already carry
`verdict` and `latest_attempt` in the required positions (F5).

> **Self-hosting note.** `P3` changes the review system that gates `P3`. It is
> therefore authored and reviewed under the **current** inline-marker system,
> and its ACTIVATE commit is what switches the workspace onto the manifest
> system. The new gate is never used to admit its own plan.

### SM-3 — Branch-ensure operation (`178-S`)

| State | Reached when | Terminal |
|---|---|---|
| `ON_EXPECTED_BRANCH` (pass) | postcondition observed: `git rev-parse --abbrev-ref HEAD` equals the resolved branch | yes |
| `ENSURE_REFUSED` (fail) | name fails validation, `git check-ref-format --branch` rejects it, or the postcondition does not hold after the attempt | yes |

Producer: `autoharness op git ensure-branch` (`178-S`, on `P2`).
Consumer: Ship agent template **and** installed mirror, invoking the operation
by name and never receiving the branch value.
Activation commit: `178-S` ACTIVATE.

Two attempt-08 corrections are recorded here explicitly:

* The normative creation command is **not** `git checkout -b -- <branch>`.
  In `git checkout -b`, `--` separates revisions from *pathspecs*, so placing
  it before the new-branch operand makes the name parse as a pathspec. The
  operation uses `git switch --create <branch>` / `git switch <branch>` with
  the name as a plain argv element under `shell=False`, preceded by
  `git check-ref-format --branch <branch>` as the authoritative validator.
* Atomicity is achieved by **asserting the postcondition after the attempt**,
  not by checking before it. A compare-then-create pair is a TOCTOU window;
  a single ensure whose success criterion is "HEAD is now exactly this branch"
  has none.

### SM-4 — Guarded checkpoint create (`180-S`)

| State | Reached when | Terminal |
|---|---|---|
| `CHECKPOINT_WRITTEN` (pass) | `resume_hint` present and shape-valid, record written atomically | yes |
| `CHECKPOINT_REFUSED` (fail) | `resume_hint` absent or invalid | yes |

Producer: `autoharness op checkpoint create` (`180-S`, on `P2`).
Consumer: Stage and Ship agents (templates + installed mirrors).
Activation commit: `180-S` ACTIVATE — which **must** include narrowing
`'backlogit/*'` in `_ship.agent.md` (+ template) and `"tools": ["*"]` in
`.mcp.json`. Per F8 this is proven syntax, not a spike.

> The guard is only a gate if the unguarded path is closed in the **same**
> commit. Narrowing the wildcard is not an accompanying cleanup task; it is
> part of the activation.

### SM-5 — SAFE_CLOSE conformance (`181-S`)

| State | Reached when | Terminal |
|---|---|---|
| `REFUSAL_OBSERVED` (pass) | the isolated Linux job records the external binary's refusal of the record transition | yes |
| `CONFORMANCE_INCONCLUSIVE` (fail) | isolation preconditions unmet, or acquisition fails digest verification | yes |

Producer: isolated CI job (`181-S`, on `S2`).
Consumer: the upstream report and `002-C`'s evidence trail.
Activation commit: `181-S` ACTIVATE.
`002-C` is **not** a consumer, **not** a member, and is **not** transitioned by
any state above.

---

## Compatibility decision

| Corpus | Size | Families | Handling |
|---|---|---|---|
| Verdict manifests | 7 live | A (21-key, ×6), B (17-key, ×1), C (pre-review nulls, synthetic) | versioned `normalize()` → canonical → strict validate |
| Checkpoints | 134 | v1-closed, legacy-unversioned, torn (×2) | versioned `normalize()` → canonical or typed QUARANTINE |
| Immutable review history | all of `docs/reviews/review-history/` | n/a | **never read for mutation, never rewritten** |

The canonical format is **open at the boundary and closed at the core**: a
fixed required set plus a preserved-extras map. A closed-everything format was
tried in `179-S` and F5 shows it rejects every record in the live corpus.

## Security boundary

| Boundary | Enforced by | Not enforced by |
|---|---|---|
| Command execution | `subprocess.run(argv_list, shell=False)` inside a Python operation, executable allowlist per operation | agent prose promising `shell=False` |
| Untrusted value handling | value never leaves Python; agent passes an **identifier**, never a name | escaping rules in a Markdown document |
| Path traversal | containment primitive resolving against the declared workspace root, rejecting escapes | path conventions in prose |
| Partial writes | atomic write primitive (`temp-in-dir → fsync → os.replace`) | writer discipline |
| Tool authority | explicit per-tool allowlist in agent frontmatter and `.mcp.json` | `backlogit/*` wildcard + a wrapped operation |
| External binary | network-denied disposable Linux container, no credentials, read-only/absent repo | digest verification alone |

Digest verification answers *what did I download*. It does not answer *what am
I about to execute* or *what can it reach* — that is the containment layer's
job, and it is why D5 moves execution rather than adding another check.

## Scope

**In scope.** The four foundations (`P1`–`P4`), the two spikes (`S1`, `S2`),
and the five reduced defect units carrying the seven source IDs.

**Out of scope, explicitly.**

* `173.012-T` — correcting `002-C`'s role wording. `002-C` is finalized and
  outside every manifest; scheduling a Ship mutation of it pulls a non-member
  into a shipment change set (attempt-08 `B2` on `181-S`). **Archived, not
  rescheduled.**
* Any administrative-close transition or rollback (D5).
* Repository-wide plan migration and the plan-budget contract — already moved
  out by the superseded decision's revision 3, and they stay out.
* `169-S` and `175-S` — untouched.
* `168-S → 176-S` and `167-S → 168-S` — pre-existing edges, untouched.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | `S1` concludes an MCP SDK dependency is unacceptable for a PyPI-distributed CLI | The CLI transport is unconditional and ships regardless; the sidecar becomes a separately-installed optional surface. The spike exists to make this a decision, not a surprise. |
| R2 | `S2` concludes hosted runners cannot deny egress post-acquisition | `181-S` degrades to evidence-and-documentation only, which D5 already names as the floor. `002-C` stays blocked either way. |
| R3 | `P3` is self-hosting — it changes the gate that governs it | Authored and reviewed under the current system; the new gate never admits its own plan (SM-2 note). |
| R4 | The foundations add four release units before any defect is fixed | Accepted deliberately. Seven cycles of fixing consumers ahead of producers produced zero closures; the ordering is the remedy, not overhead. |
| R5 | ACTIVATE tasks are the widest tasks in the portfolio | They are wide by construction and must stay within 2 hours by *limiting the number of surfaces per contract*, never by splitting an activation across commits. A contract touching too many surfaces to activate in one task is too large a contract and must be re-scoped. |
| R6 | Provenance corrections touch records referenced by immutable review artifacts | The review artifacts recorded the phantom IDs as a *finding*; correcting the executable record does not alter the finding's truth at the revision it was taken. History is not rewritten. |

## Portfolio re-slicing

Full disposition, source provenance and dependency detail are carried in the
plans harvested from this decision. The summary map is:

| Unit | ID | Feature | Kind | Sources | Depends on | Disposition |
|---|---|---|---|---|---|---|
| `B0` | `188-S` | `182-F` | bootstrap | — (D9) | — | **RETIRED at revision 6 — archived, externally satisfied, never claimed or executed (D9)** |
| `C0` | `191-S` | `185-F` | corrective | — (D9) | — | **RETIRED at revision 7 — archived, never claimed or executed; diagnosis withdrawn as false, deliverable satisfied by `1cb0dc81` + `b8ac632a`, and held structurally unexecutable by attempt-08 `S26` (D9)** |
| `S1` | `182-S` | `176-F` | spike | 71200CBB, 76EBDE6D | — (**`dag-root`**) | new |
| `S2` | `183-S` | `177-F` | spike | 7F9CB5E9 | — (**`dag-root`**) | new |
| `P1` | `184-S` | `178-F` | foundation | 86498B64+14F4D6F3, 71200CBB, 76EBDE6D | `S1` | **WITHHELD — archived, conditional future (D10)**; `B0` edge removed at revision 6 |
| `P2` | `185-S` | `179-F` | foundation | 86498B64+14F4D6F3, 71200CBB, C9CD24F3 | `P1` | queued, unclaimable while `P1` withheld; `B0` edge removed at revision 6. **Not to be confused with the retired `185-F` feature** (D9), which is unrelated and never executed. |
| `P3` | `186-S` | `180-F` | foundation | C9CD24F3 | `P2` | **absorbs `179-S`**; `B0` edge removed at revision 6 |
| `P4` | `187-S` | `181-F` | foundation | 76EBDE6D | — (**`dag-root`**) | `P1` edge removed at revision 2, `B0` edge at revision 6, the revision-6 `191-S` edge at revision 7 (D9) — an explicit root with an empty dependency set |
| — | `176-S` | `168-F` | defect | 76EBDE6D | — | **RETIRED at revision 7 — archived, superseded design, never claimed or executed; re-harvested fresh after `P2` and `P4` ship (D9)** |
| — | `177-S` | `169-F` | defect | 3EF5AAF2 | — (**`dag-root`**) | retained, reduced |
| — | `178-S` | `170-F` | defect | 86498B64 + 14F4D6F3 | `P2` | retained, reduced; `B0` edge removed at revision 6 |
| — | `179-S` | `171-F` | defect | C9CD24F3 | — | **archived → absorbed into `P3`** |
| — | `180-S` | `172-F` | defect | 71200CBB | `P2` | retained, reduced; `B0` edge removed at revision 6 |
| — | `181-S` | `173-F` | defect | 7F9CB5E9 | `S2` | **WITHHELD — archived, conditional future (D10)** |

Six defect units become four. The four foundations exist because four separate
units were each assuming the same four missing producers. Two additional units
were added later and **both are now retired without ever having executed** (D9):
`B0`/`188-S` at revision 2, to build the *first* actor through a pipeline that
already required it, and `C0`/`191-S` at revision 6, to correct that actor's
behaviour. Neither subject survives — the actor is installed by `07b4be79` and
made conformant by `1cb0dc81` and `b8ac632a` — so every edge awaiting either is
removed. **`176-S` is retired at revision 7** as a superseded design and is
re-harvested fresh rather than restored, leaving four live defect units. Two
units remain withheld from the executable queue because no installed claim gate
can enforce the verdict that authorizes them (D10).

### Governing plans

Each unit above is governed by exactly one plan, each with a verdict manifest
in `docs/reviews/`. The six 2026-09-17 defect plans are marked
`plan_role: superseded` and are not edited further.

| Unit | Plan | Supersedes |
|---|---|---|
| `B0` | `docs/plans/2026-09-20-harness-architect-bootstrap-plan.md` (**`plan_role: superseded`** — retained as a completed-externally decision record, not a live plan; **no PASS for revision 5**) | — |
| `C0` | — (**no governing plan was ever authored**; the unit was harvested at revision 6 and retired at revision 7 without execution) | — |
| `S1` | `docs/plans/2026-09-18-operation-transport-spike-plan.md` | — |
| `S2` | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` | — |
| `P1` | `docs/plans/2026-09-18-operation-substrate-transport-plan.md` (`plan_role: conditional-future`, preserved intact) | — |
| `P2` | `docs/plans/2026-09-18-safe-operation-primitives-plan.md` | — |
| `P3` | `docs/plans/2026-09-18-review-authority-foundation-plan.md` | `2026-09-17-single-governing-plan-contract-plan.md` |
| `P4` | `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (**revision 10**; attempt 08 FAIL against revision 9; awaiting independent attempt 09) | — |
| `176-S` (retired) | `docs/plans/2026-09-18-p004-observation-gate-plan.md` (**revision 7**; attempt 01 FAIL against revision 6; awaiting attempt 02; **withheld from harvest** until `P2` and `P4` ship) | `2026-09-17-p004-red-phase-precondition-scoping-plan.md` |
| `177-S` | `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` | `2026-09-17-post-claim-member-status-contract-plan.md` |
| `178-S` | `docs/plans/2026-09-18-branch-ensure-operation-plan.md` | `2026-09-17-workspace-authoritative-branch-resolution-plan.md` |
| `180-S` | `docs/plans/2026-09-18-checkpoint-authority-plan.md` | `2026-09-17-checkpoint-resume-hint-contract-plan.md` |
| `181-S` | `docs/plans/2026-09-18-safe-close-conformance-plan.md` (`plan_role: conditional-future`, preserved intact) | `2026-09-17-safe-close-record-transition-disposition-plan.md` |

### Note on `179-S`'s terminal state

`179-S` was intended to reach `abandoned`. That status proved **unreachable
under Stage's authority**: `backlogit`'s `validate_status_transition` pre-hook
rejects both `queued → abandoned` and `blocked → abandoned`, and the only
observed path into `abandoned` runs through `active`, which requires a Ship
claim that Stage must not perform (P-010).

`backlogit archive 179-S` was used instead — non-destructive, terminal, and
within Stage's authority — with absorption provenance recorded on the archived
record. The record is truthful: the shipment is archived and its scope lives in
`186-S`. The transition-table limitation is reported here rather than worked
around, and it is **not** silently re-described as an abandonment.
