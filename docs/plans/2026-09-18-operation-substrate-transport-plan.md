---
title: "Foundation: agent-safe operation substrate — registry and dual transport"
description: "Creates src/autoharness/ops/ with a typed operation result model and a single operation registry, and derives TWO transports from that one registry: the autoharness op CLI namespace following the established gate-command convention, and an MCP/sidecar surface whose handlers call the identical registered functions. Parity is asserted by a registry-enumerating test rather than by prose. Markdown agents invoke operations by name and never interpolate an untrusted value. Transport shape is decided by spike 182-S. Rolls out PREPARE inert, VERIFY, then one ACTIVATE commit."
doc_type: plan
source: docs/plans/2026-09-18-operation-substrate-transport-plan.md
date: 2026-09-18
plan_id: operation-substrate-transport
plan_path: docs/plans/2026-09-18-operation-substrate-transport-plan.md
plan_role: conditional-future
harvest_status: withheld
harvest_withheld_reason: "Shipment 184-S, covering feature 178-F and its tasks were harvested prematurely and are archived as a conditional future unit. A blocks edge onto the predecessor spike clears on predecessor COMPLETION and cannot enforce the spike's verdict token, and no installed shipment-claim predicate reads the findings artifact. Withheld by archival - a repository-supported backlog operation - because a live shipment carrying an invented blocked status is malformed data under the pre_claim status vocabulary. PR #457 review thread PRRT_kwDORzpWpM6kHrxd."
harvest_gate_artifact: docs/spikes/2026-09-18-autoharness-operation-transport-findings.md
reharvest_condition: "Stage re-harvests this plan's records only in a NEW staging session, after reading the gate artifact and observing TRANSPORT_DECIDED. Non-authorizing states harvest nothing. This plan is PRESERVED INTACT and UNREDUCED; only its live, claimable records are withdrawn."
withheld_records: .backlogit/archive/
revision: 5
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 was a fresh document authored under the strategic redesign, not a remediation of a prior revision. Revision 2 bound decision D11 - the manifest checksum refreshes the ACTIVATE commit requires - into the Rollout section as commit members rather than activation surfaces. Revision 3 stated and enumerated the activation arithmetic exactly - FIVE declared activation surfaces (.mcp.json, two agent templates, two installed mirrors) and SIX commit files once the single manifest file is counted, with exactly two manifest entries refreshed - corrected the stale R3 risk row that read the surface count as 'fixed at five files', extended the rollback unit to all six members, and added an owned fail-closed checksum verification contract in place of the generic verify-workspace command. Revision 4 remediates the independent manifest-contract review by binding that verification to the EXACT INDEX SNAPSHOT the commit records: it asserts the staged set equals exactly the six intended commit members, rejects any unstaged difference for them, hashes each installed mirror from :<path>, parses the manifest from :.autoharness/harness-manifest.yaml, rejects missing/extra/duplicate/metadata/checksum divergence, freezes the index between verification and commit (git write-tree recorded, no intervening index mutation, git commit -a and path arguments prohibited), and exits non-zero before the commit is created. The arithmetic is unchanged at five declared surfaces, six commit files, exactly two refreshed entries, rollback across all six. Declared-surface and digest inputs are preserved: the manifest is a commit member, not a declared activation surface. No task is added, no transport decision is pre-empted, and the live manifest is not edited: this is a future implementation contract. Revision 5 closes the terminal review finding that the post-commit tree comparison was described as preventing commit creation, which is impossible: the exact index prechecks (staged-set equality, no unstaged difference, index-read hashing, index-read manifest, total entry adjudication, recorded write-tree identity with re-staging prohibited) all run BEFORE the commit and are what fail closed and leave the commit uncreated; the commit is then created NORMALLY and git rev-parse HEAD^{tree} is compared against the recorded tree immediately afterwards as an ACCEPTANCE adjudication that claims no power to prevent local commit creation and makes no concurrency-proof claim - on mismatch the activation is NOT ACCEPTED and NOT PUBLISHABLE, it blocks the push and every downstream state token, verdict, manifest advance and handoff, and the local commit must be reverted or corrected and the whole contract re-run before proceeding. The arithmetic is unchanged at six commit members. It carries REMEDIATED-PENDING-REVIEW because it still awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-operation-substrate-transport-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
source_stash_ids:
  - 86498B64
  - 14F4D6F3
  - 71200CBB
  - 76EBDE6D
merged_stash_ids:
  - 14F4D6F3
feature_id: 178-F
shipment_id: 184-S
unit_role: precursor-foundation
depends_on_shipments:
  - 182-S
input_contract: docs/spikes/2026-09-18-autoharness-operation-transport-findings.md
requires_plan_hardening: true
hardening_rationale: "Introduces a new public surface on a globally-installed, PyPI-distributed CLI, adds an MCP server to the workspace tool graph, and becomes the boundary every later safety control is built on. Elevated blast radius across CLI distribution, agent tool declarations, and .mcp.json."
tags:
  - foundation
  - operation-substrate
  - cli
  - mcp
  - agent-native-parity
  - precursor
---

# Foundation: agent-safe operation substrate

## Problem frame

Four release units in this portfolio each specify a *consumer* of an operation
surface that does not exist, and none of them builds it.

| Unit | What it assumes | Attempt-08 finding |
|---|---|---|
| `178-S` | an executable argv boundary reached from an agent | `A1` (P0) — the consuming site is a Markdown document |
| `180-S` | a guarded MCP operation | `B3` — no server, no owner, no registration |
| `176-S` | an MCP parity boundary for the gate | `B6` — the gate is CLI-only |
| `180-S` | a callable the agent invokes instead of raw CLI argv | `C2` — inline argv exposed in prose |

`src/autoharness/cli.py` dispatches on a hand-rolled `argv` table with exactly
ten commands (`home`, `version`, `verify-workspace`, `gate`, `telemetry`,
`eval`, and four `setup-*`). There is **no operation namespace at all**.

This unit builds the missing producer once, so the four consumers stop each
inventing their own.

## The reframe this foundation encodes

A Markdown agent does not execute an argument vector. A model composes a shell
string from the document's prose. That is why attempt-08 `A1` on `178-S` is
unfixable in the agent surface: `--` cannot terminate an argument vector that
does not exist.

The substrate's contract is therefore not "make the agent escape the value
correctly". It is:

> **The agent never receives the value.** It passes an *identifier* to an
> operation; the operation resolves, validates and applies the sensitive value
> entirely inside Python. A value the agent never holds is a value the agent
> cannot mis-escape.

## Contract

A **safe operation** is a Python function in `src/autoharness/ops/` that:

1. takes typed parameters and returns a typed `OperationResult` carrying an
   explicit outcome token — never a string for the caller to re-parse;
2. is registered exactly once under a `namespace/name` pair;
3. is reachable through **both** transports, derived from that one registration.

**CLI transport.** `autoharness op <namespace> <operation> [--flags]`, added to
`cli.py` as `_parse_op_args` / `_op_command`, following the convention `gate`
already demonstrates across its five subcommands
(`_gate_check_command`, `_gate_pre_review_command`, `_gate_size_command`,
`_gate_pipeline_topology_command`, `_gate_dag_readiness_command`).

**MCP/sidecar transport.** A real `autoharness` server whose handlers call the
**identical registered functions**. Implementation shape is supplied by
`182-S`; this plan must not be harvested against an assumed transport.

**Parity.** A test enumerates the registry and requires both transports to
expose the same operation set with the same parameter names. Parity is
*checked*, not asserted in prose — which is the difference between this and the
`B6` finding it closes.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `PARITY_HELD` — every registered operation reachable through both transports with identical parameter names |
| Fail state | `PARITY_BROKEN` — any operation exposed by one transport only, or with divergent parameters |
| Producer | the operation registry (`178.002-T`) |
| Consumer | the parity test (`178.003-T`); later, every operation-invoking agent surface |
| Activation commit | `178.006-T` |

`PARITY_HELD` is reachable: with zero operations registered the set is trivially
equal, and it remains checkable as operations are added by `185-S`, `176-S`,
`178-S` and `180-S`.

## Rollout

**PREPARE (inert).** `178.002-T`, `178.004-T`, `178.005-T`. Inert means no CLI
command routes to a registered operation from any agent path, no MCP server is
registered in `.mcp.json`, no agent, skill, policy or registry entry directs
anything to the namespace. Live workspace behaviour is byte-identical before
and after every PREPARE task.

**VERIFY.** The first half of `178.006-T`: every RED assertion observed
failing, the same assertions observed passing, parity green across both
transports.

**ACTIVATE.** The second half of `178.006-T` — **one task, one commit** across
**five declared activation surfaces**: register the `autoharness` server in
`.mcp.json`, and state the operation-invocation contract in
`templates/agents/_ship.agent.md.tmpl`,
`templates/agents/_stage.agent.md.tmpl` and **both** installed mirrors,
simultaneously.

> Sequential task edges are **not** atomic. An edge from task *A* to task *B*
> permits a commit between them, and therefore a reachable state in which the
> server is registered but the agents do not know the contract, or one mirror
> has drifted from its template. Every surface that must not disagree is in
> this one task.

**Manifest parity is part of that same atomic unit (decision `D11`).** Both
installed mirrors — `.github/agents/_ship.agent.md` and
`.github/agents/_stage.agent.md` — are **manifest-tracked installed
artifacts**: `.autoharness/harness-manifest.yaml` carries an `artifacts:`
entry for each, recording a `sha256` of its pre-activation content. The two
templates are **not** tracked — the manifest tracks no template — and
`.mcp.json` is **not** tracked either, so the ACTIVATE commit refreshes
**exactly two** manifest entries while touching **five declared activation
surfaces**, and therefore contains **exactly six files**: `.mcp.json`,
`templates/agents/_ship.agent.md.tmpl`,
`templates/agents/_stage.agent.md.tmpl`, `.github/agents/_ship.agent.md`,
`.github/agents/_stage.agent.md` and `.autoharness/harness-manifest.yaml`. In
the **same commit** and the **same rollback unit**, rewrite each of those two
checksums to the `sha256` of the installed file *as written by this commit*,
then **verify checksum parity** under the index-bound fail-closed contract
below. A
commit that states the invocation contract in either mirror without its
manifest refresh leaves the manifest asserting a digest of a file the same
commit has already rewritten — an installed-artifact parity hole — and is an
**immediate revert**, not a fixup commit. The manifest refreshes are **commit
members, not activation surfaces**: they add no transport, no command, no
server registration and no contract clause, the declared activation-surface
count stays **five**, and they change no surface count stated anywhere in this
plan. `git revert` of the single ACTIVATE commit restores **all six commit
members** — the two mirrors, the two templates, `.mcp.json` **and** both
manifest checksums — together. This binds a **future implementation commit**;
it authorizes no staging-time edit to the live manifest, and none has occurred.

**Fail-closed verification bound to the exact index snapshot, not generic
`verify-workspace`.** Parity is adjudicated by a verification step this unit
owns, run **after all commit members are staged and before the commit is
created**, and bound to the **exact index snapshot the commit will record**.
The generic `verify-workspace` command is **not** that gate: it reports
whole-workspace install state read from the working tree, it does not
adjudicate a named staged digest against a named `artifacts:` entry, and its
exit status is therefore not a checksum assertion. The owned step:

1. **Asserts the staged set is exactly the intended commit members.**
   `git diff --cached --name-only` equals, as a set, the six members
   enumerated above — `.mcp.json`, the two agent templates, the two installed
   mirrors and `.autoharness/harness-manifest.yaml`. A **missing** member, an
   **extra** staged path, or a **duplicate** entry each fails.
2. **Rejects any unstaged difference for those members.** `git diff
   --name-only --` restricted to the six members must be empty, and none may
   be untracked. If the working tree differs from the index for any commit
   member, the bytes verified are not the bytes committed, and the step fails
   rather than verifying the wrong content.
3. **Hashes the installed artifacts from the index.** For each of the two
   touched installed mirrors, recompute SHA-256 over the **staged blob read
   as `:<path>`** (`git cat-file -p :.github/agents/_ship.agent.md`,
   `git cat-file -p :.github/agents/_stage.agent.md`) — never a working-tree
   read.
4. **Parses the manifest from the index too**, as
   `:.autoharness/harness-manifest.yaml`, so the entries compared against are
   the entries this commit records rather than any the working tree may hold.
5. **Adjudicates the entry set totally.** For each touched installed mirror
   there is **exactly one** `artifacts:` entry whose literal `path` matches;
   its `primitive` and `template` metadata are exactly as required and
   unchanged by this commit; and its `checksum` equals the digest from (3)
   byte-for-byte. A **missing** entry, an **extra** entry — any `artifacts:`
   entry this commit adds or removes — a **duplicate** `path`, a **metadata**
   divergence, or a **checksum** mismatch each fails. This activation installs
   no new artifact — `.mcp.json` and both templates stay untracked — so **no
   new entry is required here**; where a future activation does install one,
   the same step asserts the new entry exists with exact `path`, `template`
   and `primitive` values before comparing its checksum.
6. **Records the index identity and forbids re-staging.** Record the index
   identity with `git write-tree` immediately after (5) passes, then create the
   commit with **no intervening index mutation** — no `git add`, `git rm`,
   `git stash`, checkout or restore. `git commit -a` and path arguments to
   `git commit` are **prohibited**, because both re-stage content after
   verification and would commit bytes the gate never adjudicated.
7. **Fails closed before the commit exists.** Steps (1)-(6) all run *before*
   the commit is created, so any failure among them, any unreadable input, or
   any digest mismatch **exits non-zero and the commit is not created**. This
   is the whole of the pre-commit gate.
8. **Adjudicates acceptance after the commit is created.** The commit is then
   created normally; this step does **not** prevent its creation and claims no
   such power. Immediately afterwards, compare `git rev-parse HEAD^{tree}`
   against the tree recorded in (6). On a match the activation is accepted. On
   a **mismatch** the commit records a tree the gate never adjudicated, so the
   activation is **NOT ACCEPTED and NOT PUBLISHABLE**: it **blocks the push**,
   blocks every downstream state token, verdict, manifest advance and handoff
   that would otherwise depend on this activation, and the local commit **must
   be reverted or corrected, and the whole contract re-run, before any further
   step proceeds**.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `178.001-T` | RED | operation registry + result-model contract tests observed failing | S | medium |
| `178.002-T` | PREPARE | ops package, typed `OperationResult`, registry | S | medium |
| `178.003-T` | RED | CLI/MCP parity contract test observed failing | S | medium |
| `178.004-T` | PREPARE | `autoharness op` CLI namespace dispatch | M | medium |
| `178.005-T` | PREPARE | MCP/sidecar transport per the `182-S` findings | M | high |
| `178.006-T` | VERIFY+ACTIVATE | parity evidence, then one commit registering transport and contract | M | high |

Edges: `178.001-T` → `178.002-T` → `178.003-T` → {`178.004-T`, `178.005-T`} →
`178.006-T`. `178.004-T` and `178.005-T` are **independent successors** and are
not serialized against each other.

### RED import safety

Every RED module imports cleanly under `unittest.defaultTestLoader` with zero
loader errors and zero `_FailedTest` placeholders. Not-yet-existing symbols are
imported **inside the test body**, because a module that raises on import
produces a *missing observation*, not a red one — the exact distinction the
P-004 work in `176-S` exists to enforce, applied to this unit's own tests.

## Out of scope

* Any domain operation. `ensure-branch`, `p004-gate` and `checkpoint create`
  belong to `178-S`, `176-S` and `180-S`, on top of `185-S`'s primitives.
* The safety primitives themselves — `185-S` owns them.
* Narrowing the `backlogit/*` tool wildcard. That is part of `180-S`'s
  activation, where the guarded operation it protects lands.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | `182-S` finds no acceptable MCP transport | The CLI transport ships unconditionally; the sidecar becomes an optional separately-installed surface and the parity requirement is restated against it. `178.005-T` implements the recommended alternative rather than being abandoned. |
| R2 | The `op` namespace collides with an existing command | The ten existing commands are enumerated above; `op` is not among them. `178.004-T` asserts no existing command changes behaviour. |
| R3 | The activation task is the widest in the unit | It is wide by construction. It stays inside the 2-hour bound because the declared activation-surface count is fixed at **five** — six commit members once the single manifest file is counted — and each edit is a contract statement, not an implementation. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | If an operation is registered but reachable through only one transport, does anything catch it? | Yes — the parity test enumerates the registry, so a single-transport operation fails `PARITY_HELD`. A prose claim of parity would not have caught it, which is the `B6` finding. |
| H2 | Can an agent reach a registered operation before ACTIVATE? | No. PREPARE registers nothing in `.mcp.json` and states no contract in any agent surface. Registry membership without a transport declaration is unreachable from an agent. |
| H3 | Does the CLI transport change behaviour of the ten existing commands? | It must not. `178.004-T` asserts the existing dispatch table is unchanged and that `op` is a new, previously unused token. |
| H4 | Can a caller pass a shell string through the operation boundary? | Parameters are typed and the exec primitive from `185-S` takes an argv list. There is no parameter whose value reaches a shell, because no operation constructs one. |
| H5 | What if the MCP SDK is an unacceptable new runtime dependency? | `pyproject.toml` currently declares exactly two runtime dependencies. Adding a third is a distribution decision, not an implementation detail — `182-S` must report the dependency cost, and if it is unacceptable the sidecar becomes an optional extra rather than a core dependency. |

### Blast radius

`src/autoharness/` gains a new package; `cli.py` gains one dispatch branch;
`.mcp.json` gains one server; two agent templates and two installed mirrors
gain one contract statement; and the harness manifest gains two refreshed
checksums as a commit member of the same activation. The CLI is globally
installed and PyPI-distributed, so a defect in the dispatch branch reaches
every installation.

### Rollback

PREPARE tasks are inert and roll back by reverting the commit with no workspace
state to repair. The ACTIVATE commit rolls back as a unit across **all six
commit members**: reverting it removes the server registration, the agent
contract statements in both templates and both mirrors, **and** restores both
manifest checksums together, returning the workspace to the pre-activation
state exactly because they landed together.

### Verification floor

The unit is not verifiable without `182-S`'s findings, and this plan must not be
harvested into tasks against an assumed transport. That gate is stated in the
frontmatter as `input_contract`.
