---
title: "Dark-factory staging run 2026-08-31: 48-ID triage, grouping, embedded decisions, and shipment portfolio"
date: 2026-08-31
doc_type: decision
agent: "Stage (planning only — Ship executes)"
route: "claude-opus-5 / anthropic / high"
classification: "staging portfolio / triage + four embedded architecture decisions"
blast_radius: "planning artifacts and backlog structure only; no source, template, schema, or workflow mutation performed by this artifact"
scope_mode: "DARK_MODE_ACTIVE, fixed scope, no expansion"
dark_mode_activated_at: "2026-08-31T21:47:45Z"
source_stash_ids:
  - "47971057"
  - "34AAF1C7"
  - "AE1BC5ED"
  - "F2271F07"
  - "E0A7171E"
  - "61336141"
  - "B57F9E24"
  - "08D71FD5"
  - "B698F01B"
  - "7628C291"
  - "D1A46B8C"
  - "D00CB293"
  - "74C62374"
  - "3B67029C"
  - "57A43F55"
  - "01340569"
  - "6443A499"
  - "56803680"
  - "0A86267A"
  - "11BCE865"
  - "99E4CF94"
  - "91CE2B66"
  - "7645AE19"
  - "D911A3B2"
  - "39AA674D"
  - "926FEA6D"
  - "A02280C8"
  - "3F80F8A3"
  - "C327A8DE"
  - "7A3F570B"
  - "89E833E1"
  - "8CB5A9B9"
  - "B90A5BBF"
  - "C0EA1175"
  - "701073F9"
  - "BA035180"
  - "F0ADCC03"
  - "5CBA0A85"
  - "6A2D62DD"
  - "2E67938C"
  - "8E10B13B"
  - "E738A7D1"
  - "053E2BD2"
source_queue_ids:
  - "028-DL"
  - "029-DL"
  - "030-DL"
  - "080-F"
  - "081-F"
---

# Dark-factory staging run 2026-08-31 — triage, decisions, and portfolio

Route: `claude-opus-5 / anthropic / high` (P-013.5, inherited; propagated to every
skill invoked in this run). Workspace root `C:\Source\GitHub\autoharness`,
single worktree, branch `main`, HEAD `2661c1c8`.

Tool state recorded for this run:

| Surface | State |
|---|---|
| backlogit MCP + CLI | `TOOL_OK` — `backlogit_sync_index` returned `indexed: 1040` (`INDEX_SYNC_OK`) |
| Engram CLI | `ENGRAM_OK` — branch `main`, 201 code files, 15 211 edges, `stale_files: false` |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` — fell back to local `docs/` + repository reads only |
| agent-intercom | `INTERCOM_DEGRADED` — no broadcasts; local `DARK_MODE` phase records emitted instead |

`ALL_TOOLS_OK` is **not** claimed. Effective status: `DEGRADED_MODE:
graphtor-docs, agent-intercom`. No public-web egress of internal context occurred.

## Scope discipline

The scope is exactly the 43 stash IDs plus the 5 queue IDs named by the operator.
The active stash contains exactly 43 entries and the scoped set is the whole
stash — verified by set comparison, zero missing, zero extra. No entry outside
the fixed scope was triaged, mutated, or promoted.

## Step 1 precedence check — deferred-scope-expansion entries (P-021 C2/C5/C6)

Fifteen entries carry the literal `DEFERRED SCOPE EXPANSION` marker as their
first field: `D1A46B8C`, `D00CB293`, `74C62374`, `3B67029C`, `57A43F55`,
`01340569`, `11BCE865`, `99E4CF94`, `B90A5BBF`, `C0EA1175`, `701073F9`,
`BA035180`, `F0ADCC03`, `8E10B13B`, `E738A7D1`. Per the precedence rule these are
forced onto the `deliberate` route regardless of apparent shape or triviality and
may not reach planning without a deliberation artifact. **This artifact is that
deliberation artifact for all of them**, and each carries its source refs (PR
number, review-thread ID, originating work IDs) forward into the plan that
consumes it.

**Duplicate detection (P-021 C5(A), unconditional) — CLEAN SCAN.** Run over all
43 active entries pairwise on subject surface. Near-neighbour pairs examined and
**rejected as non-duplicates**:

| Pair | Why not a duplicate |
|---|---|
| `99E4CF94` / `B90A5BBF` | Both concern archived stash `34D50F2D`, but one is *dangling references inside its text*, the other is *whether its archival was premature*. Different remedies, both required. |
| `6443A499` / `0A86267A` / `56803680` | Same registry file, three distinct contract surfaces: undeclared feature flag, wrong MCP command, product-scope support decision. |
| `2E67938C` / `6A2D62DD` | Enforcement of existing size/complexity fields vs. inventing a range-deterministic threshold. Producer vs. research. |
| `D911A3B2` + 7 siblings | Governed by `031-DL`; the normalization table there already de-duplicated them into S1–S11. |
| `B57F9E24` / `3B67029C` | Both backlogit-owned, but different subsystems (evidence loss vs. checkpoint timestamp writer). |

No entry was found to describe the same expansion as another. **No merge, no
archive-as-duplicate performed.**

**Late-identifier reconciliation (P-021 C5(B)) — triggered on 4 entries.**
`D00CB293`, `57A43F55`, `01340569`, `99E4CF94` record a PR number but no
review-thread ID (`N/A`-shaped). Ship-owned residual-risk records for PR #409 and
PR #411 were read; **no late identifier surfaced** for any of the four. The
recorded gaps stand as truthful terminal records. This is a no-op completion, not
a C3/C6 shortfall, and does not gate anything downstream.

## Full disposition table — all 48 scoped IDs

Legend for `Route`: **SHIP-n** = harvested into shipment n of this run's
portfolio; **RETAIN** = stays active in the stash with a recorded rationale;
**EXTERNAL** = not implementable in this repository; **BLOCKED** = requires
operator input that cannot be safely inferred.

### Stash entries (43)

| # | ID | Prio | Kind | Group | Route | Disposition |
|---|---|---|---|---|---|---|
| 1 | `053E2BD2` | high | bug | A | **SHIP-1** | Two shipped v1.5.0 guardrails unsatisfiable by their own templates. Confirmed at `2661c1c8` and in the published wheel. Consumed. |
| 2 | `B698F01B` | critical | bug | A | **SHIP-1 (partial)** + RETAIN | Blocking symptom gone (waived 2026-08-29). One safe half — the stale `autoharness.supervise.bootstrap` citation in `tests/test_verify_workspace.py` — is harvested. The env-injection replacement mechanism is an architecture decision reserved to the operator; entry stays ACTIVE. |
| 3 | `8E10B13B` | high | bug | B | **SHIP-2** | `release.yml` pre-publish PyPI probe fails open. Verified at L94-L107 + L109-L112. Consumed. |
| 4 | `E738A7D1` | high | bug | B | **SHIP-2** | Immediate hotfix confirmed present (`_clear_ambient_github_head_ref()` at `tests/test_gates_topology.py:929`). Residual: no end-to-end push-context guard. Consumed. |
| 5 | `74C62374` | high | bug | C | **SHIP-3** | Six enumerated file-lock findings; 4 and 5 (unconditional lock deletion) contradict shipped policy. Consumed. |
| 6 | `BA035180` | high | bug | D | **SHIP-4** | Security-reviewer purpose-based suppression can hide a real vulnerability. Consumed. |
| 7 | `C0EA1175` | medium | bug | D | **SHIP-4** | P-007 auto `git restore` conflicts with Constitution VII destructive-command approval. Consumed. |
| 8 | `701073F9` | medium | bug | D | **SHIP-4** | Constitution-reviewer checklist stops at Principle IX. Consumed. |
| 9 | `F0ADCC03` | medium | bug | D | **SHIP-4** | Python-reviewer cites a never-rendered `python.instructions.md`. Consumed. |
| 10 | `7628C291` | medium | bug | D | **SHIP-4** | Leaf-executor rule contradicted by two shipped skills. Decided below (**D4**). Consumed. |
| 11 | `D1A46B8C` | high | bug | E | **SHIP-5** | markdownlint installed but not enforced in CI; pre-push fails open at `.githooks/pre-push.sh:36`. Consumed. |
| 12 | `5CBA0A85` | medium | feature | E | **SHIP-5** | Residual open question from archived `8AC574F1`: fail-closed agent→skill dangling-reference check. Consumed. |
| 13 | `11BCE865` | high | bug | E | **SHIP-5** | 10 docs files with silently truncated frontmatter; guard cannot detect the class. Consumed. |
| 14 | `D00CB293` | medium | bug | F | **SHIP-6** | Unconfigured-gate sentinel strings rendered as executable tool names. Consumed. |
| 15 | `57A43F55` | medium | chore | F | **SHIP-6** | Tool-scoped template branches render the *active* tool's values. Consumed. |
| 16 | `2E67938C` | high | feature | G | **SHIP-7 + SHIP-8** | Split. Registry-parity enabler → SHIP-7; Stage decomposition enforcement → SHIP-8. Consumed. |
| 17 | `6443A499` | medium | task | G | **SHIP-7** | Undocumented implicit resolver default for absent feature keys. Consumed. |
| 18 | `0A86267A` | high | bug | G | **SHIP-7** | backlog-md `mcp_server.command` wrong in two ways. Gated on **D3**. Consumed. |
| 19 | `56803680` | high | deliberation | G | **decided (D3)** → SHIP-7 | Decided below: KEEP-but-DEMOTE. Consumed. |
| 20 | `B90A5BBF` | high | bug | H | **SHIP-9** | Possible premature archival of `34D50F2D`. Consumed. |
| 21 | `99E4CF94` | low | bug | H | **SHIP-9** | Three dangling doc refs inside `34D50F2D`. Consumed. |
| 22 | `7645AE19` | medium | bug | H | **SHIP-9** | Merged closure record asserts a false "no further candidates". Consumed. |
| 23 | `91CE2B66` | medium | chore | H | **SHIP-9** | P-020 Phase 2 backlog: four named candidates. Consumed. |
| 24 | `01340569` | low | chore | H | **SHIP-9** | Half-ignored `.backlogit/checkpoints/` tracking state. Consumed. |
| 25 | `D911A3B2` | critical | epic | I | **RETAIN** | Program epic for `031-DL` S1–S10. `031-DL` open-questions explicitly forbids archiving it. Not re-decomposed (no duplicate hierarchy). |
| 26 | `39AA674D` | critical | feature | I | **RETAIN** | Normalized into portfolio unit **S3** (D-PAR). Not staged this run. |
| 27 | `926FEA6D` | critical | feature | I | **RETAIN** | Normalized into **S7** (D-STATE). Not staged this run. |
| 28 | `A02280C8` | high | feature | I | **RETAIN** | SPLIT by `031-DL`: (a) → **S5**, (b) → **S11** (deferred). Not staged. |
| 29 | `3F80F8A3` | high | feature | I | **RETAIN** | SPLIT by `031-DL`: (a) S4-PROV, (b) S4-DOC, both in **S4**. Not staged. |
| 30 | `C327A8DE` | high | feature | I | **RETAIN — next eligible** | Owns **S2** (D-ART). Prerequisites S0 (`148-F`) and S1 (`149-F`) are now both `done`, so S2 is the first eligible portfolio unit. Explicitly named as the next Stage cursor. |
| 31 | `7A3F570B` | high | feature | I | **RETAIN** | Normalized into **S6** (D-TEST). Not staged. |
| 32 | `89E833E1` | critical | feature | I | **RETAIN** | SPLIT 3 ways by `031-DL`: (a) shipped in S1, (b) → S8, (c) → S10. Not archived. |
| 33 | `8CB5A9B9` | high | feature | I | **RETAIN, dependency-deferred** | Requires a machine-derived cycle count from S9. Not buildable yet. |
| 34 | `34AAF1C7` | medium | feature | J | **RETAIN (living tracker)** | Branch (a) PR-review convergence is consumed by portfolio S9; branch (b) reasoning-state identity remains blocked on inventing node identity (A8). `031-DL` explicitly declines to split a living tracker. |
| 35 | `08D71FD5` | medium | feature | J | **RETAIN** | Owned by `030-DL`, decided below (**D5**): the adversarial-ideation primitive is real but its durability trigger has not fired. Entry stays active pending the trigger. |
| 36 | `B57F9E24` | high | bug | K | **EXTERNAL** | backlogit-owned, re-verified NOT FIXED at upstream `b0772938`. Non-implementable here. No cross-workspace mutation performed. |
| 37 | `3B67029C` | medium | bug | K | **EXTERNAL** | Defect in the backlogit checkpoint writer — different product, different contract surface. Non-implementable here. |
| 38 | `AE1BC5ED` | medium | feature | L | **RETAIN (deferred)** | SkillOpt integration deliberation, intake-only. Feature-evaluation work; ranks below reliability/security/composability under the operator's policy. |
| 39 | `F2271F07` | medium | feature | L | **RETAIN (deferred)** | Waza integration deliberation, intake-only. Same rationale. |
| 40 | `E0A7171E` | medium | feature | L | **RETAIN (deferred)** | witr integration deliberation, intake-only. Same rationale. |
| 41 | `47971057` | high | feature | M | **RETAIN (deferred)** | Capability-pack runtime installer TUI. Genuine high-value feature, but it is *feature delivery* and the nine staged units are all reliability/security/composability. Named as the leading next-cycle feature candidate. |
| 42 | `61336141` | medium | feature | M | **RETAIN (deferred)** | `autoharness install` CLI driving `copilot.exe`. Entry itself says "investigate … before planning" — spike-first, not plan-ready. |
| 43 | `6A2D62DD` | medium | spike | G | **RETAIN** | Range-deterministic sizing threshold is genuinely undetermined ("the threshold value is YET TO BE DETERMINED"). SHIP-8 delivers the *enforcement* half using the thresholds that already exist; the threshold-derivation spike stays open. |

### Queue items (5)

| ID | Type | Prior state | Disposition |
|---|---|---|---|
| `028-DL` | deliberation | queued | **RESOLVED → decided.** Decision **D1** below. Branch (a) is already consumed by portfolio S9; branch (b) is blocked on A8 (reasoning-state identity), which is a research problem, not a planning gap. Nothing further is decidable here. |
| `029-DL` | deliberation | queued | **RESOLVED → decided.** Decision **D2** below. Its artifact `docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md` exists and its ranked candidates were consumed by `031-DL`. Its C4.2 blocker was cleared 2026-08-25 (`031-DL` §R2). |
| `030-DL` | deliberation | queued | **RESOLVED → decided.** Decision **D5** below. |
| `080-F` | feature | blocked | **REMAINS BLOCKED.** Multi-repo/monorepo architecture. Its own DoD states the decision "cannot be inferred from this repo alone". Choosing between per-repo / monorepo-units / parent-spanning / federated changes P-001 release-unit sequencing, P-010 role boundaries and P-016 worktree topology. Under this run's stop conditions ("architecture decision that cannot safely be inferred") it is a recorded halt, not a guess. |
| `081-F` | feature | blocked | **REMAINS BLOCKED.** WSL local Linux builds. Requires the operator to *separately authorize destructive WSL installation/provisioning*. The dark-mode record sets `admin_fallback_pre_authorized: false` and forbids unauthorized destructive operations, so authorization cannot be self-granted. |

Coverage check: 43 stash + 5 queue = **48 IDs, each appearing exactly once.**

## Embedded decisions

Each decision below was produced by the `deliberate` route and then subjected to
the multi-persona adversarial review recorded in §"Adversarial review of the
decisions".

### D1 — `028-DL` / `34AAF1C7`: close the deliberation, keep the tracker

**Decision: mark `028-DL` decided; do not split `34AAF1C7`; do not stage S9 in
this run.**

`028-DL` concluded spike-first because reasoning-state *identity* is undefined.
That conclusion has not been falsified; nothing in this run's evidence changes
it. Its executable branch (a) — PR-review convergence via a finding-ledger,
epoch, and monotone measure — was already absorbed into `031-DL` as portfolio
unit **S9**, which is independent and has no prerequisites. Staging S9 is
therefore *possible* but it is an MVE with a falsification gate, i.e. research,
and this run's ordering policy puts research last. The deliberation itself has
nothing left to decide, so it moves to `done`; the *work* lives in S9.

Splitting the `34AAF1C7` living tracker is an operator-visible reclassification
that `031-DL` explicitly declined to perform. That refusal is re-affirmed.

### D2 — `029-DL`: close the deliberation

**Decision: mark `029-DL` decided.**

`029-DL` is an expansive opportunity map, not a choice. Its artifact exists, its
fifteen ranked candidates were consumed by `031-DL`'s option analysis, and its
C4.2 blocker was cleared on 2026-08-25. A deliberation whose output has already
been consumed by a downstream decided deliberation has no remaining decision
surface. Its central thesis — *a convention survives iff a machine produces it or
penalizes its absence* — is carried forward as a governing law of SHIP-5 and
SHIP-7 rather than left as prose.

### D3 — `56803680`: backlog-md support

**Decision: option (b) KEEP but DEMOTE to explicitly limited/experimental.**

Rejected (a) DROP, rejected (c) KEEP AS-IS.

Reasoning, weighed against the operator's ordering policy:

* Option (c) is indefensible on its own evidence — it advertises 96 operations'
  worth of pipeline on a 39-operation registry, and the one guarded gap
  (`features.shipments`) is guarded *by accident*, via an undocumented
  `setdefault(..., False)` at `verify_workspace.py:2967`, not by declaration.
* Option (a) DROP is the *simpler* end state and the operator's policy does
  prize simplicity — but DROP is a **breaking change requiring a schema enum
  removal across four schema versions plus a migration note**, and the decision
  input "are there any known real backlog-md installs to break?" is unanswerable
  from inside this repository. Under this run's stop conditions, an
  irreversible breaking change taken on an unanswerable input is exactly the
  class of decision that must not be inferred. **DROP is therefore not
  autonomously available**, independent of its merits.
* Option (b) is reversible in both directions: it makes the true support surface
  honest and *preserves* the ability to choose (a) later with better evidence.

Consequences carried into SHIP-7: `6443A499` is resolved by **declaring**
`features.shipments: false` explicitly and documenting the resolver default
rather than relying on it; `0A86267A` is fixed (`backlog.md`, with a dot) because
a demoted-but-supported tool must still have a correct command. `57A43F55` is
*not* resolved by this decision — it needs the real fix in SHIP-6, since option
(a)'s "eliminate the second tool" escape is unavailable.

**Non-goal explicitly recorded:** this decision does not authorize adding the
new `stash` / `queue` / `checkpoints` feature flags that option (b) mentions.
That is a schema change and stays out of this fixed scope.

### D4 — `7628C291`: the leaf-executor contradiction

**Decision: amend the two instruction templates to state a bounded, explicit
one-hop exception for the review family. Do not change skill behaviour.**

The contradiction is real and verified: `harness-architecture.instructions.md`
L163 and `role-enforcement.instructions.md` L81 both say skills are leaf
executors that do not spawn subagents, while
`templates/skills/review/SKILL.md.tmpl` L33-35 declares its own *Subagent Depth
Constraint* and L159 spawns five always-on personas.

Two remedies exist. Making the skills conform would delete the multi-persona
adversarial review capability that this very run depends on — a large behavioural
regression justified only by prose tidiness. Making the *rule* conform codifies
what already ships, and the shipped skill already carries the correct bound
("maximum depth: review skill → persona subagent, 1 hop"; personas may not spawn).

So the rule is wrong, not the code. The amendment must be a **bounded exception,
not a general relaxation**: named review-family skills only, depth 1, spawned
subagents remain leaf executors, and the P-013.5 model-inheritance clause is
unchanged (persona subagents still inherit; they still declare no routing
frontmatter of their own).

### D5 — `030-DL` / `08D71FD5`: adversarial ideation primitive

**Decision: mark `030-DL` decided; keep `08D71FD5` active; do not build the
primitive in this run.**

`030-DL` selected "agent ruling + durability trigger gate" — i.e. the primitive
is authorized *conditionally*, gated on a durability trigger. The trigger is
evidence that the improvised dialectic recurs and is being re-improvised. This
run produced no such evidence: the adversarial machinery used here is the
*existing* review-persona layer, not a re-improvisation. Building a new ideation
primitive now would be premature framework complexity, which the operator's
policy #6 explicitly warns against. The deliberation is decided; the entry stays
active as the durability counter.

## Contextual grouping analysis (Step 1.5)

Thirteen groups emerged. Nine are actionable in this run.

| Group | Theme | Contract surface | Entries | Outcome class |
|---|---|---|---|---|
| **A** | Shipped-guardrail contract restoration | `verify_workspace.py` assertion tables + the templates that must satisfy them + their tests | `053E2BD2`, `B698F01B`(part) | Reliability — every fresh v1.5.0+ install currently fails 2 guardrails |
| **B** | Release/CI pipeline fail-closed gates | `.github/workflows/release.yml`, `tests/_env_patch.py`, `tests/test_gates_topology.py` | `8E10B13B`, `E738A7D1` | Security + reliability of the publish path |
| **C** | Concurrency-pack script security | `templates/skills/file-lock/scripts/**` + `scripts/**` mirror | `74C62374` | Security — workspace containment, mutual exclusion |
| **D** | Agent/policy contract integrity | `templates/agents/review/**`, `templates/policies/**`, `templates/instructions/**` | `BA035180`, `C0EA1175`, `701073F9`, `F0ADCC03`, `7628C291` | Security + constitution conformance |
| **E** | Fail-closed harness gates | CI job composition, `.githooks/pre-push.sh`, `verify-harness`, docs frontmatter guard | `D1A46B8C`, `5CBA0A85`, `11BCE865` | Reliability — gates that currently fail open |
| **F** | Template variable resolution | template authoring/variable-substitution layer | `D00CB293`, `57A43F55` | Composability + simplicity |
| **G** | Backlog registry contract | `.autoharness/backlog-registry.yaml`, `templates/backlog/registries/**` | `2E67938C`(a), `6443A499`, `0A86267A`, `56803680` | Interoperability + composability |
| **H** | Backlog/docs traceability hygiene | `.backlogit/**`, `docs/closure/**`, `docs/plans/**`, `.gitignore` | `B90A5BBF`, `99E4CF94`, `7645AE19`, `91CE2B66`, `01340569` | Documentation/traceability |
| **I** | Deterministic pre-review evidence portfolio | governed by `031-DL` | nine entries | **Not re-decomposed** |
| **J** | Reasoning-determinism / ideation primitives | `028-DL`, `029-DL`, `030-DL` | `34AAF1C7`, `08D71FD5` | Decided, not built |
| **K** | External products | — | `B57F9E24`, `3B67029C` | Non-implementable here |
| **L** | External tool-integration evaluations | — | `AE1BC5ED`, `F2271F07`, `E0A7171E` | Deferred |
| **M** | Installer / CLI feature delivery | — | `47971057`, `61336141` | Deferred |

Grouping alternatives considered and rejected:

* **Merge B into A** (both touch `tests/`). Rejected: A's surface is the
  verifier↔template contract; B's is CI/workflow control flow. Different reviewers
  and different failure modes. Keeping them apart also isolates the one same-file
  overlap (`tests/test_verify_workspace.py`), which is why `B698F01B`'s comment fix
  was placed in **A**, not B.
* **Merge C into D** (both are "review/security template hygiene"). Rejected: C
  edits *executable scripts copied verbatim with checksum validation*; D edits
  *rendered markdown*. Different install mechanisms, different verification.
* **One combined "registry + sizing" shipment (G collapsed)**. Rejected as a giant
  mixed shipment: registry-file parity and Stage-agent decomposition behaviour are
  genuinely different surfaces. Split into SHIP-7 (registry) → SHIP-8 (Stage),
  with a hard `blocks` edge because SHIP-8's fail-closed behaviour is only
  reachable once the installed registry advertises `features.sizing`.

## A material discovery made during grouping

While grounding `2E67938C`, the installed registry was compared to its template:

* `templates/backlog/registries/backlogit.registry.yaml` — 460 lines
* `.autoharness/backlog-registry.yaml` — **269 lines**

The installed registry is missing **22 declared operations** (`stash`,
`stash_edit`, `stash_get`, `stash_archive`, `fetch_stash`, `harvest_stash`,
`deliberate`, `add_link`, `remove_link`, `get_links`, `archive_item`,
`adopt_item`, `get_metadata_catalog`, `get_wit_metadata`, `list_types`,
`list_templates`, `get_version`, `export_command_map`, `merge_sync`,
`telemetry_harvest`, `doctor`, `cleanup_checkpoints`), the entire sizing field
map (`size`, `complexity`, `size_source`, `size_ruleset_version`, on both
`update_task` and `field_mapping`), and **seven feature flags** including
`sizing: true` and `stash: true`.

This is not cosmetic. It is the mechanical cause of three separate symptoms:

1. Step 0.0's registry-driven tool gate under-declares the available surface, so
   an agent that honours the registry believes operations such as `stash_archive`
   do not exist — the exact P-012 ad-hoc-fallback failure the gate exists to
   prevent.
2. `2E67938C`'s sizing mandate cannot resolve through the registry, because the
   installed registry does not advertise `features.sizing`.
3. Stage's own Step 5.6 stash-archive obligation and P-021 C5's
   archive-not-delete tool protocol have no declared operation to bind to.

It is captured **inside** `2E67938C`'s existing scope as its enabling condition —
not as a new stash entry — because `2E67938C` already asserts that the fields
"exist" and must be "robustly and enforceably" used, and this is precisely why
they are not. No scope expansion occurred.

## Priority ordering

Applying the operator's policy in order — cohesion, then product outcome with
reliability and security above features, then composability/interoperability/
simplicity above features, then features above documentation, then
bug→review→feature→task→spike:

| # | Shipment | Class | Why here |
|---|---|---|---|
| 1 | **SHIP-1** guardrail contract restoration | reliability | Highest live product impact: *every* fresh v1.5.0+ merge-install into a backlogit workspace fails two guardrails today, and the failure pushes operators toward unauditable target-only patches the next upgrade silently reverts. |
| 2 | **SHIP-2** release/CI fail-closed gates | security | A permanent property of the unattended publish path: a re-tag can build a green GitHub Release around artifacts the run did not produce. Not release-specific. |
| 3 | **SHIP-3** file-lock script security | security | Shipped scripts contradict shipped policy; any agent can silently break any other agent's lock, so the mutual-exclusion guarantee does not hold. Ranked below 2 only because it affects local concurrency, not published artifacts. |
| 4 | **SHIP-4** agent/policy contract integrity | security + constitution | Contains the security-reviewer suppression defect that can hide a real vulnerability *before it is ever reported* — a review-integrity failure. |
| 5 | **SHIP-5** fail-closed harness gates | reliability | Converts three fail-open gates into fail-closed ones. Direct application of the `029-DL` law. |
| 6 | **SHIP-6** template variable resolution | composability | Rendering correctness for non-active-tool branches and unconfigured gates. Policy #3 places this above feature delivery. |
| 7 | **SHIP-7** installed registry parity | composability + interop | Restores 22 operations and the sizing surface; prerequisite for 8. |
| 8 | **SHIP-8** Stage sizing enforcement | composability | Bounds shipment/session growth. Depends on 7. |
| 9 | **SHIP-9** traceability hygiene | documentation | Policy #4: features outrank documentation, and this is documentation/traceability. Last. |

Dependency edges are genuine, not decorative: **7 → 8** is the only hard
prerequisite (SHIP-8 cannot fail closed on a flag SHIP-7 has not yet installed).
The remaining edges are sequencing edges expressing the priority order under
P-001 single-release-unit discipline, which is what the operator asked to be
encoded.

## Plan-hardening triggers (P-006)

| Shipment | Hardening required? | Trigger |
|---|---|---|
| SHIP-1 | **yes** | Touches the verifier assertion tables, multiple template families, and the dogfood mirror — elevated blast radius. |
| SHIP-2 | **yes** | CI workflow control flow on the irreversible publish path. |
| SHIP-3 | **yes** | Security-sensitive; a wrong containment fix is worse than none. |
| SHIP-4 | **yes** | Security persona semantics + policy text + an architecture rule amendment. |
| SHIP-5 | **yes** | Changes CI composition and hook semantics for every contributor. |
| SHIP-6 | yes | Template variable scheme change — cross-cutting across template families. |
| SHIP-7 | **yes** | Registry is the resolution substrate for every generated agent. |
| SHIP-8 | no | Confined to Stage/harvest template text plus a test; no schema or distribution surface. |
| SHIP-9 | no | Documentation, backlog state, and one `.gitignore`/tracking decision. |

Hardening is applied inline in each plan under "Hardening (P-006)".

## Adversarial review of the decisions

Personas: **Architecture**, **Correctness**, **Maintainability/Scope**,
**Constitution**, **Security**. Verdict recorded per finding with severity.

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| R1 | Scope | **P1** | The registry-drift discovery could be read as scope expansion beyond the fixed 48 IDs. | **Resolved.** It is folded into `2E67938C`'s existing text ("the fields exist; the requirement is that Stage's decomposition actually uses them") as its enabling condition. No new stash entry, no new ID, no work outside the 48. Recorded explicitly in §"A material discovery". |
| R2 | Constitution | **P1** | D3 (keep-but-demote) risks being a decision the operator reserved, since `56803680` lists "decision inputs needed". | **Resolved.** The reserved input ("known real installs to break?") is only load-bearing for option (a) DROP. D3 explicitly records DROP as *not autonomously available* and selects the reversible option, which preserves the operator's ability to choose DROP later. The irreversible branch was not taken. |
| R3 | Architecture | **P1** | D4 amends a NON-NEGOTIABLE-adjacent architecture rule (P-013.5). | **Resolved.** The amendment is bounded to the spawn prohibition and explicitly leaves the model-inheritance clause intact; persona subagents continue to declare no routing frontmatter and continue to inherit. The plan carries this as a binding constraint, not a suggestion. |
| R4 | Security | **P1** | SHIP-3 sequencing: a partially-hardened lock (containment landed, ownership not) is *worse* than none, because operators would trust a guarantee that does not hold. | **Resolved.** SHIP-3's tasks are ordered so containment and ownership land in the same shipment and the manifest/checksum refresh is the last task; no intermediate state is shippable. Recorded as SHIP-3 hardening constraint H3. |
| R5 | Correctness | P2 | `E738A7D1` was described as unfixed; the hotfix is in fact present. | **Resolved.** Verified `_clear_ambient_github_head_ref()` at `tests/test_gates_topology.py:929` and rescoped SHIP-2 to the genuine residual (no end-to-end push-context guard; nothing prevents the next test from re-introducing the pattern). |
| R6 | Correctness | P2 | `B698F01B` is critical and marked "do NOT auto-fix". Harvesting *any* part of it risks overriding operator intent. | **Resolved.** Only the documentation-accuracy half is harvested — correcting a comment that cites a module that does not exist. The three reserved questions (replacement env mechanism, whether to delete `src/autoharness/supervise/`, guard relaxation) are untouched and the entry stays ACTIVE. Deleting the orphaned `__pycache__` is *not* harvested at all: `git ls-files` returns empty for it, so it is untracked and gitignored and cannot be expressed as a PR. |
| R7 | Maintainability | P2 | Nine shipments risks a sprawling session and premature structure. | **Accepted with mitigation.** Each shipment is a single cohesive contract surface with 2–4 tasks; none exceeds the 2-hour rule per task; no new framework is introduced by any of them. The largest *framework* unit in scope (portfolio S2) is deliberately **not** staged. |
| R8 | Architecture | P2 | Not staging S2 leaves the highest-priority (`critical`) in-scope items unharvested. | **Accepted, recorded.** The nine `031-DL` entries are `RETAIN` by that deliberation's own open-questions clause; harvesting them here would duplicate the hierarchy the operator explicitly said not to duplicate. S2's eligibility is newly established (S0 and S1 both `done`) and is handed forward as the named next cursor. |
| R9 | Scope | P3 | `6A2D62DD` overlaps SHIP-8. | **Resolved.** SHIP-8 delivers enforcement against *existing* thresholds only. The spike's open question — deriving a per-session token/complexity threshold — is untouched and the entry stays active. Recorded as SHIP-8 non-goal N2. |
| R10 | Constitution | P3 | Committing planning artifacts on `main` in dark mode. | **Resolved.** Stage's Role Boundary permits committing backlog/planning artifacts on the default branch. No source, template, schema, or workflow file is modified by this run. Push/publication disposition is returned to the Orchestrator rather than improvised. |

**Gate result: PASS.** Four P1 findings raised, four resolved before harvest.
Zero unresolved P0/P1. Two review-fix cycles used of three.

## Genuine out-of-scope observations (P-021 capture candidates, NOT acted on)

Recorded here for visibility only. **None of these were captured as new stash
entries and none are part of this run.** Capture is Ship's C2 duty at the moment
an authorized change is being made; there is no authorized change here to defer
*from*.

1. `docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`
   (untracked, part of this run's inherited artifacts) concludes with
   `promoted_to: ["none"]` and "No repository or release fix is required" — the
   three causes are client-side (a lagging non-PyPI mirror index, a
   non-upgrading plain install command, TLS interception of
   `files.pythonhosted.org`). It is committed as a completed spike record with no
   backlog item, which is the correct disposition for a spike whose conclusion is
   "no repository change".
2. `053E2BD2` names four further wording-brittle assertions
   (`stage/ship_index_sync_gate`, `pipeline_topology_gate_ship_agent_wiring`,
   `ship_source_artifact_cleanup`) that are satisfiable via `{{OP_*}}` substitution
   and explicitly says "separate P3 hardening, do not bundle". Not bundled.
3. `053E2BD2` also records that two of the operator's four reported failures are
   **not recoverable from this repository** and lists the exact target-workspace
   evidence needed. SHIP-1 fixes the two that are provable here and does not guess
   the other two.

## Next-cursor handoff

* **Next portfolio unit**: `031-DL` **S2 — D-ART** (owner `C327A8DE`).
  Prerequisites S0 (`148-F`) and S1 (`149-F`) are both `done`; S2 is `critical`,
  `low` risk, report-only, with day-one blast radius of exactly zero against the
  612 existing tasks. It is the portfolio's own "best promotion candidate".
* **Next feature candidate**: `47971057` (capability-pack runtime installer).
* **Next spike candidate**: `6A2D62DD` (range-deterministic sizing threshold),
  best run after SHIP-8 lands so the spike has a live enforcement point to
  measure against.
* **Operator input required**: `080-F`, `081-F`, and `B698F01B`'s reserved
  env-injection question.

## References

* `docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md` (`031-DL`)
* `docs/decisions/2026-08-29-engram-env-injection-guard-v1_5_0-waiver-deliberation.md` (`B698F01B`)
* `docs/decisions/2026-08-31-v1_5_0-guardrail-template-contract-mismatch-spike.md` (`053E2BD2`)
* `docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`
* `docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md` (`029-DL`)
* `.github/policies/workflow-policies.md` — P-001, P-006, P-007, P-010, P-012, P-016, P-019, P-021
  (corrected in review-fix cycle 1: the path is `.github/policies/`, not
  `.github/instructions/`; the latter does not exist and the reference dangled)

## Review-fix cycle 1 — corrections to this artifact (2026-08-31)

This section records corrections applied to this decision record after an
independent local review blocked the publication diff at HEAD `4d029e55`. The
original text is corrected in place where it was factually wrong; nothing is
silently rewritten without being named here.

| # | Correction | Evidence |
|---|---|---|
| C1 | **"Fourteen entries carry the literal `DEFERRED SCOPE EXPANSION` marker" → fifteen.** The enumerated list always contained fifteen IDs; the word was wrong, not the list. | Count of the enumerated IDs in §"Step 1 precedence check". |
| C2 | **Dangling reference `.github/instructions/workflow-policies.md` → `.github/policies/workflow-policies.md`.** | `.github/instructions/` contains 18 files, none named `workflow-policies.md`; the file exists at `.github/policies/workflow-policies.md` with template `templates/policies/workflow-policies.md.tmpl`. |
| C3 | **Dark-mode activation, scope, and cursor record added** (§"Dark-mode activation and authority record" below) so P-017 audit evidence survives in a committed artifact rather than only in a checkpoint. | — |
| C4 | **Pre-existing artifact inadvertently published** recorded (§"Residual scope note" below). | — |
| C5 | **Queue ordering authority changed** (§"Queue ordering authority" below). | — |
| C6 | **Checkpoint `progress.tasks_completed` corrected** (§"Checkpoint correction" below). | — |

## Queue ordering authority (corrects the inconsistent queue metadata)

The reviewed diff carried inconsistent queue metadata: `155.001-T` at position 36
while its siblings sat at 23–24; no position at all on `151.004-T`, `151.005-T`,
`153.003-T`, or on eight of the nine shipments; and feature/task order drift.

Repair was **attempted first as option (a)** — renumber everything monotonically
with `backlogit queue move`. That attempt **failed for a structural reason worth
recording**, and the failure is the finding:

> `backlogit queue move` operates on the *default active queue view*, which
> **respects dependency constraints**. Once the cycle-1 `blocks` edges were added,
> every dependency-blocked task left that view and returned
> `Error: move in queue: item <id> not found in queue view`. Shipments are not in
> the view either. The partial run left **duplicate positions** (14, 15, 19, 23,
> 26 and 30 each appearing twice) and fresh gaps — strictly worse than the input.

`queue_position` is therefore **a derived, partial, eligibility-scoped projection,
not a complete ordering authority**. It cannot be made complete and monotonic
across a hierarchy that contains blocked tasks and shipments, and no
`create`/`update` operation can even set or clear it — `queue move` is the only
writer, and it cannot reach the items that need it.

**Adopted: option (b) — dependency edges are the sole ordering authority.**
`queue_position` was removed from all 54 in-scope items (38 carried one). Ordering
is now fully expressed by, and only by:

| Level | Authority |
|---|---|
| Between shipments | the `blocks` chain `159-S → 160-S → … → 167-S` |
| Within a shipment | `blocks` edges between tasks (18 edges, enumerated in the session memory) |
| Membership | the shipment `items` manifest, verified against `size_composition.members` |

This is complete (every item's position is derivable), monotonic by construction
(the graph is acyclic — backlogit rejects cycles at insert), and verifiable
item-by-item. Out-of-scope items (`080-F`, `081-F`, both blocked on operator
input) were not touched.

## Checkpoint correction

`.backlogit/checkpoints/checkpoint-20260831-223851.json` listed **27 queued Ship
implementation tasks** under `progress.tasks_completed`. None of them is
completed; all are queued and unstarted, and Ship has not begun `159-S`.

**Repair method — official operations only, no hand-editing.** Checkpoints are
tool-owned and the erroneous record is `status: resolved` and therefore immutable.
The erroneous file was **not edited**. Instead a corrective checkpoint was created
through `backlogit checkpoint create` (schema `V1`, all domain data under
`context`) and written as `status: resolved`, recording: the corrected checkpoint's
filename, the full list of 27 IDs erroneously marked complete, their true status,
an **empty** `progress.tasks_completed`, and an explicit 36-item
`progress.tasks_remaining`. Created as `checkpoint-20260831-233625.json`.

**Why recovery cannot misread either record.** Stage's crash-resumption protocol
enumerates checkpoints and partitions to those whose `status` is `active`. Both
the erroneous and the corrective record are `resolved`, and
`backlogit checkpoint list --status active` returns `total: 0`. No recovery path
can restore either record or interpret a queued task as completed.

## Dark-mode activation and authority record (P-017 audit evidence)

Committed here so the authority under which this run operated is recoverable from
the repository itself, independently of any checkpoint file.

| Field | Value |
|---|---|
| `run_mode` | `DARK_MODE_ACTIVE` |
| `dark_mode_activated_at` | `2026-08-31T21:47:45Z` |
| `scope_mode` | fixed scope, no expansion |
| `scope` | exactly 48 source IDs (43 stash + 5 queue), each triaged exactly once |
| `shipment_order` | `159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 167-S` |
| `last_completed` | `null` |
| `next` | `159-S` |
| `merge_preauthorized` | `true` |
| `admin_authority` | `false` |
| `destructive_command_preauthorized` | `false` |
| `intercom` | `DEGRADED` (no broadcasts; local `DARK_MODE` phase records emitted instead) |
| `graphtor-docs` | `UNAVAILABLE` (fell back to local `docs/` + repository reads) |
| `engram` | `OK` |
| `backlogit` | `OK` |

**Authority bounds, stated explicitly.** `merge_preauthorized: true` authorizes
merging PRs produced from this fixed scope. It does **not** authorize
administrative actions, and it does **not** authorize executing destructive
commands — `admin_authority: false` and
`destructive_command_preauthorized: false` are independent and both hold. Review-fix
cycle 1 relied on this distinction twice: SHIP-9's `git rm --cached` was removed
from scope, and SHIP-4's P-007 `git restore` was gated behind a named,
operator-recorded approval that fails closed when absent.

## Residual scope note — pre-existing artifact inadvertently published

`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`
(published in commit `214347b2` of this Stage series) is a **pre-existing
investigation artifact dated 2026-08-30**, authored before this run's dark-mode
activation at `2026-08-31T21:47:45Z`. It is **outside the fixed 48-ID scope** —
it appears in no `source_stash_ids` or `source_queue_ids` entry above — and was
included in the Stage publication commit rather than being produced by it.

**Disposition for this cycle: recorded, no action.**

* It is **not deleted.** Deletion is a destructive operation and is not
  preauthorized by merge approval (see the authority record above). Removing it
  would require distinct explicit operator approval.
* History is **not rewritten.** The commit stands; the correction is recorded
  forward, consistent with **H1** in SHIP-9.
* **Residual risk: low.** The artifact is a genuine, self-consistent spike record
  that is useful on its own terms. The risk is one of *provenance clarity* only —
  a future reader could mistake it for output of this run's fixed scope. This note
  is the mitigation, and the publication summary carries it too.
* **No further action in this cycle**, by explicit operator instruction.
