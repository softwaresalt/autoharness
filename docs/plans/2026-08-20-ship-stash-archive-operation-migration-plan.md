---
title: "Migrate Ship post-merge Step 7 to backlogit_stash_archive"
date: 2026-08-20
stash_id: 8D570CF8
deliberation: docs/decisions/2026-08-20-ship-stash-archive-operation-migration-deliberation.md
hardening: docs/plans/2026-08-20-ship-stash-archive-operation-migration-hardening.md
requires_plan_hardening: yes
hardening_present: yes
blast_radius: "elevated (multi-family: agent template plus dogfood mirror, policy registry, backlog registry, verifier, contract tests, manifest checksums)"
---

# Implementation Plan - Ship Step 7 stash-archive migration

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `8D570CF8`
Deliberation: `docs/decisions/2026-08-20-ship-stash-archive-operation-migration-deliberation.md`
Classification: **chore / deprecated-API migration on a shipped contract surface**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make every **prescriptive** carrier name `backlogit_stash_archive` as the
operation Ship uses to retire a source stash entry at post-merge Step 7, leaving
every **historical** record untouched.

## Non-goals

* No change to backlogit itself.
* No edit to `docs/closure/`, `docs/memory/`, or the shipped 2026-08-18 hardening
  record - these are immutable history (deliberation lists them by name).
* No back-porting of drifted content between `_ship` template and mirror.
* No change to the live `.autoharness/backlog-registry.yaml`.
* No deletion of `stash_remove` from the registry - deprecate in place.

## Task A (ATOMIC) - Ship template + dogfood mirror + verifier + contract tests + manifest checksum

> **REVISED 2026-08-20 (review-fix).** Tasks A, C and D were merged into this
> single atomic task. See "REVISION - atomic task restructure" at the end of this
> plan for the reason. Backlog IDs: surviving task `137.003-T`; superseded and
> archived `137.005-T` (old Task C), `137.006-T` (old Task D).

**Files**
* `templates/agents/_ship.agent.md.tmpl` - line 38 (Role Boundary), line 819 (Step 7)
* `.github/agents/_ship.agent.md` - line 47 (Role Boundary)
* `src/autoharness/verify_workspace.py` - line 296 (`ship_source_artifact_cleanup` marker)
* `tests/test_verify_workspace.py` - lines 1860, 3135 (marker-list fixtures)
* `tests/test_scope_containment_policy_contract.py` - line 595
* `tests/test_scope_containment_boundary_contract.py` - lines 79, 87, 332, 552 (comments only)
* `.autoharness/harness-manifest.yaml` - checksum for `.github/agents/_ship.agent.md`

Replace the operation name with `backlogit_stash_archive` at each site. Preserve
the surrounding clause wording exactly, including the existing parenthetical
distinguishing this **manifest-derived closure operation** from **discretionary**
removal - that distinction is load-bearing for P-021 C5 and must survive.

At the Step 7 site, also update the follow-on sentence so the already-retired
case reads in archive terms ("if the stash entry is already archived, skip and
log it").

**Paired-edit obligation**: both sides edited in this same change, per the
maintenance contract landed earlier in this shipment. The mirror carries only
the Role Boundary site; that asymmetry is expected and is **not** to be
"fixed" here.

**Also performed here (absorbed from old Tasks C and D)**
* Update the `ship_source_artifact_cleanup` `must_contain` marker to the archive
  wording landed above; leave `source_stash_id`, `source_deliberation_id` and
  `backlogit_archive_item` unchanged.
* Update the two `tests/test_verify_workspace.py` marker-list fixtures to match.
* Update `tests/test_scope_containment_policy_contract.py` line 595 without
  weakening any C5 removal/archival assertion.
* Correct the false "no `stash remove` subcommand" claim in the
  `tests/test_scope_containment_boundary_contract.py` comments (lines 87, 552):
  on v1.10.0 `stash remove` is a **deprecated alias** of `stash archive`, not absent.
* Refresh the `.github/agents/_ship.agent.md` manifest checksum from the
  LF-normalized committed blob (`git cat-file -p :<path>`).

**Acceptance**
* No prescriptive occurrence of `backlogit_stash_remove` remains in any edited file.
* No file claims the CLI lacks a `stash remove` subcommand.
* Role Boundary clause semantics unchanged apart from the operation name.
* These assertions still pass unchanged: `workflow_policy_text` contains
  "manifest-derived retirement of the source stash entry that fed the shipped scope";
  both ship carriers contain "a manifest-derived closure operation, distinct from
  discretionary removal", "discretionary removal or archival of stash entries", and
  "create a capture-only stash entry (P-021 C5)".
* `verify-workspace` clean AND the full configured suite green **at the single
  completion gate for this task** - no red intermediate state at any point.
* Manifest checksum matches the actual committed bytes of the edited mirror.
* Everything lands in one commit.

## Task B - Policy registry + backlog registry templates

**Files**
* `templates/policies/workflow-policies.md.tmpl` - line 726 (P-021 C5)
* `templates/backlog/registries/backlogit.registry.yaml` - line 278

For C5: name the archive operation. **Preserve verbatim** the clause's existing
treatment of removal and archival as *separately named prohibited discretionary
dispositions*, and the manifest-derived exception. This clause was hardened
deliberately (H2); do not simplify it while renaming the operation.

For the registry: keep the `stash_remove` mapping present but marked deprecated,
and ensure `stash_archive` is the operation **this registry** resolves to for the
Ship post-merge stash-retirement path (MCP primary `backlogit_stash_archive`, CLI
fallback parameterized as below). Note the starting state: the `stash_archive`
mapping already declares `mcp_tool` and `params.stash_id` but declares **no
`cli_command` at all**, so Task B *adds* that key rather than editing one.

**Required exact value (P1).** The CLI fallback MUST be written verbatim as:

```yaml
cli_command: "backlogit stash archive {{stash_id}}"
```

A bare `backlogit stash archive` with no stash identifier is **invalid** and must
not be written. Verified against the installed CLI: `backlogit stash archive
--help` declares `Usage: backlogit stash archive <stash-id>` - exactly one
**required** positional stash identifier, with no flag form and no default. A
bare command is unexecutable, and a P-012 degraded-mode consumer that logs or
runs the declared fallback verbatim (`TOOL_DEGRADED: {tool_name} - CLI fallback:
{cli_command}`) would emit a command that cannot run, silently defeating the very
fallback leg this migration exists to establish. Registry convention embeds
operation parameters as `{{...}}` placeholders directly in `cli_command` - see
`stash` -> `backlogit stash add --text {{text}}`, `get_task` -> `backlogit get
{{id}}`, `move_task` -> `backlogit move {{id}} --status {{status}}`. The
placeholder MUST be spelled exactly `{{stash_id}}` so it binds to the mapping's
existing `params.stash_id` key; any other spelling leaves the parameter unbound.

This exact value is the **authority** for the registry `cli_command`. Where other
migration artifacts (the `137-F` feature description, `137.003-T`, the hardening
addendum, the deliberation, and the staging memory record) name `backlogit stash
archive` in bare form, they describe the CLI *subcommand's existence* or contrast
it with the deprecated `stash remove` alias - they do not quote a registry value,
are correct as written, and do not license a bare `cli_command` here.

**Scope boundary**: Task B owns the policy clause and the registry mapping only.
It does not edit - and does not *validate* - the Ship agent contract, verifier,
contract tests, or manifest checksum; those belong to Task A (`137.003-T`). Every
Task B acceptance criterion is therefore evaluated against Task B's own two files.
That is what keeps Task B order-independent of Task A with no dependency edge in
either direction.

**Acceptance**
* C5 still prohibits discretionary removal **and** discretionary archival.
* The manifest-derived post-merge exception still reads as allowed.
* Registry still describes both operations; `stash_remove` marked deprecated and
  not resolved by any prescriptive execution path.
* The registry's `stash_archive` mapping names `backlogit_stash_archive` (MCP
  primary) and declares its CLI fallback as the exact string `backlogit stash
  archive {{stash_id}}`. **Verify literally**: the `{{stash_id}}` placeholder is
  present in the `cli_command` value and matches the mapping's `params.stash_id`
  key, so the stash identifier is passed through to the command. A `cli_command`
  of bare `backlogit stash archive`, or one using any placeholder name other than
  `{{stash_id}}`, **fails** this criterion. Evaluated against
  `templates/backlog/registries/backlogit.registry.yaml` **only**, never against
  the Ship agent contract.

## Task C - MERGED INTO TASK A (superseded 2026-08-20)

**Was**: update `src/autoharness/verify_workspace.py` line 296 so the
`ship_source_artifact_cleanup` check no longer requires `backlogit_stash_remove`.

**Status**: **merged into Task A.** Backlog task `137.005-T` is superseded by
`137.003-T` and archived.

**Why merged**: this task and Task A were mutually breaking (H1). Task A alone
removes the marker the verifier demands; Task C alone demands a marker the mirror
does not yet carry. Either ordering leaves a red gate, and Ship evaluates the full
configured suite before completing **each** task - so neither could ever complete.
An "adjacent commits in one PR" mitigation is insufficient, because the gate is
per-task, not per-PR.

## Task D - MERGED INTO TASK A (superseded 2026-08-20)

**Was**: update the contract tests and refresh the `.github/agents/_ship.agent.md`
manifest checksum.

**Status**: **merged into Task A.** Backlog task `137.006-T` is superseded by
`137.003-T` and archived.

**Why merged**: Task D existed only to repair assertions and a checksum that its
own predecessors invalidated, so the dependency graph deadlocked - A and C could
not go green without D, and D could not go green before them. All of Task D's
content, including the H3 historical-record protections and the H6 checksum
rationale, is carried into Task A.

**Dependency note**: old Task D also depended on Task B. That edge is **not**
carried into Task A. Re-verified during this restructure: Task B touches only
`templates/policies/workflow-policies.md.tmpl` and
`templates/backlog/registries/backlogit.registry.yaml`; no assertion Task A
touches reads either file, and B's H2 constraint preserves every asserted C5
marker string. Task B is independently gate-green and order-independent.

## Verification (Ship)

1. `grep -r backlogit_stash_remove` returns **only** historical records, the
   deprecated-but-retained registry mapping, and the Stage reference text that
   describes the deprecation.
2. `verify-workspace` clean.
3. Full test suite green.
4. `git diff --name-only` contains no path under `docs/closure/` or `docs/memory/`.
5. The `stash_archive` mapping in `templates/backlog/registries/backlogit.registry.yaml`
   declares `cli_command: "backlogit stash archive {{stash_id}}"` - the
   `{{stash_id}}` placeholder is literally present and matches that mapping's
   `params.stash_id` key. A bare `backlogit stash archive` fails this check.

## Sequencing

Second within its shipment, **after** the paired-edit maintenance contract.

Executable order after the atomic restructure (shipment `145-S`):

1. `137.002-T` - maintenance contract document (no dependencies).
2. `137.001-T` - parity contract test annotations (requires `137.002-T`).
3. `137.003-T` - **atomic** stash_archive migration (requires `137.002-T`).
4. `137.004-T` - policy clause + backlog registry (no dependencies; order-independent).

No cycles. Every task is independently gate-green: each leaves `verify-workspace`
and the full configured suite passing at its own completion gate.

## Plan Review (plan-review gate)

**Verdict: PASS WITH CONDITIONS.** Reviewed 2026-08-20 by Stage.

| Check | Result |
|---|---|
| Prescriptive vs historical boundary explicit | PASS - both lists enumerated by file and line |
| Each task within the 2-hour rule | PASS |
| Width isolation | **SUPERSEDED 2026-08-20** - the original A/B/C/D width split was the defect, not a virtue: it distributed a mutually-breaking change set across four tasks and deadlocked the per-task quality gate. Now: A (atomic migration, deliberate multi-family carve-out), B (policy/registry). Width isolation yields to gate-green atomicity where the two conflict |
| Acceptance criteria falsifiable | PASS |
| Blast radius honestly stated | PASS - elevated |
| Hardening required (P-006) | **YES** - elevated blast radius, multiple template families, and a live policy clause. Hardening performed; see linked hardening record |
| Coupling to `6D62077C` acknowledged | PASS - ordering stated and justified |

**Conditions carried into execution** (from hardening):
1. ~~Tasks A and C must not land in isolation from one another (H1).~~
   **DISCHARGED BY CONSTRUCTION 2026-08-20** - A and C are now one task, so no
   intermediate red state is reachable. Do not re-split Task A.
2. The C5 removal/archival distinction must survive the rename verbatim (H2).
3. No historical record may be edited; verified by an explicit `git diff` check (H3).
4. **Every task must leave the full configured suite green at its own completion
   gate.** No task may depend on a temporarily red predecessor.

---

## ADDENDUM (Stage, 2026-08-20) - tool surface ground truth

> **RETRACTION (Stage review-fix cycle 3, 2026-08-20).** An earlier revision of
> this addendum asserted the MCP and CLI surfaces were *inverted* and that
> `backlogit_stash_archive` was **not exposed** on MCP. That was **false** and is
> retracted in full, together with the CLI-canonical-plus-deprecated-alias-MCP-fallback
> direction it produced. Tasks A and C execute as a direct rename to the archive
> operation.

Verified read-only against the installed `backlogit v1.10.0` (`backlogit manifest`,
`backlogit stash --help`, `backlogit stash archive --help`):

| Surface | `stash_archive` | `stash_remove` |
|---|---|---|
| **MCP** | **EXPOSED - primary** (`backlogit_stash_archive`, "Archive an active stash entry") | EXPOSED, self-described `[Deprecated: use backlogit_stash_archive]` |
| **CLI** | **EXPOSED - canonical** (`backlogit stash archive <id>`) | present only as an **alias** of `archive`, resolving to the same handler |

`.mcp.json` runs the same `backlogit mcp` executable with `tools: ["*"]`, so
`backlogit_stash_archive` is reachable in this workspace.

### Consequence for the migration

A direct rename of the Ship contract to the archive operation is **correct,
executable, and complete on both surfaces**. There is no nonexistent-tool hazard
and no need for a deprecated-alias fallback.

### Confirmed direction (binding on Task A and Task C)

The Ship contract names both surfaces in P-012 MCP-first / CLI-fallback order:

1. **MCP primary**: `backlogit_stash_archive`.
2. **CLI fallback**: `backlogit stash archive <id>` - exposed, non-destructive.
3. `backlogit_stash_remove` **must not** be specified as an execution fallback or
   any other prescriptive path. It may appear only as non-prescriptive
   legacy/deprecation context describing the behaviour being removed.
4. Task B still keeps both registry mappings, for a **descriptive** reason only:
   the deprecated tool genuinely still exists upstream and the registry should
   describe reality. That supports hardening H5's "deprecate in place, do not
   delete"; it never authorises a prescriptive fallback.

This preserves the deprecation intent (stop naming removal semantics) and keeps
both P-012 legs satisfied by the replacement operation itself.

---

## REVISION - atomic task restructure (Stage review-fix, 2026-08-20)

**Finding (P1).** The original A/B/C/D decomposition could not pass Ship's
per-task quality gate. Ship runs the full configured suite before completing
**each** task, but the staged contracts admitted that predecessor tasks would
leave the verifier, the contract tests, and the manifest checksum **red** until a
later task repaired them. Concretely:

| Edit | Immediately invalidates | Repair originally deferred to |
|---|---|---|
| `.github/agents/_ship.agent.md` (Task A) | `verify_workspace.py` `ship_source_artifact_cleanup` marker | Task C |
| `templates/agents/_ship.agent.md.tmpl` (Task A) | `test_scope_containment_policy_contract.py::test_post_merge_step7_source_artifact_cleanup_is_unweakened` | Task D |
| `.github/agents/_ship.agent.md` bytes (Task A) | `test_manifest_checksum_matches_actual_dogfood_bytes_for_all_eight_pairs` | Task D |
| `verify_workspace.py` (Task C) | `test_verify_workspace.py` marker-list fixtures (lines 1860, 3135) | Task D |

Task D in turn could not go green before A and C landed. The graph deadlocked.

**Resolution.** The mutually-breaking set was collapsed into **one atomic task**,
so every invalidated assertion and checksum is repaired by the same task that
invalidates it. The "adjacent commits within a single PR" mitigation in H1 was
insufficient, because the gate is evaluated per **task**, not per PR.

**Backlog effect** (all via official backlogit operations):

* `137.003-T` - **survives**, rewritten as the atomic task; size `S` -> `M`,
  complexity `medium` (two-axis 2h gate re-applied; still within the 2-hour rule
  as ~11 mechanical, fully-specified edit sites plus one checksum refresh).
* `137.005-T` - **superseded by `137.003-T`**, stamped and archived.
* `137.006-T` - **superseded by `137.003-T`**, stamped and archived.
* `137.004-T` - unchanged; re-verified as independently gate-green.
* `137.001-T`, `137.002-T` - unchanged.
* Shipment `145-S` membership: **all six children of `137-F` are manifest
  members** - `137-F`, `137.002-T`, `137.001-T`, `137.003-T`, `137.004-T`,
  `137.005-T`, `137.006-T`. An earlier revision of this bullet reduced the
  manifest to five items; that reduction was **closure-invalid** and was
  reverted 2026-08-20 (see "Closure-validity correction" below). The
  **executable** set is unchanged and is still the four queued tasks.
* Dependency edges removed: `137.006-T -> 137.005-T`, `137.006-T -> 137.004-T`,
  `137.005-T -> 137.003-T`. Remaining edges: `137.001-T -> 137.002-T`,
  `137.003-T -> 137.002-T`. Acyclic.

**Scope preserved.** No approved work was dropped and none was added; the same
edits are performed, redistributed so that no gate ever observes a red state.

### Closure-validity correction (2026-08-20)

Reducing `145-S`'s manifest to the four executable tasks made the shipment
unclosable on **both** supported paths, so full-child membership was restored
via the official `backlogit_add_to_shipment` operation.

* **Cascade path.** `autoharness.gates.shipment_closure.classify_shipment_close_path`
  enumerates a root feature's children across **both** `.backlogit/queue/` and
  `.backlogit/archive/`. With `137.005-T` / `137.006-T` omitted it returned
  `safe_close: feature member '137-F' has children outside the manifest`.
* **Safe-close path.** P-015 then places every omitted child in the **protected
  set**, whose baseline integrity gate requires each protected member to be
  present in `queue/`. Both are already archived, which safe-close classifies as
  a pre-existing cascade - closure halts before archiving any manifest item.
  The `pre-archived` exemption applies to manifest items **only**; the protected
  set has none.
* **After restoration** the classifier returns
  `cascade: every feature member is a verified fully-covered root`, and P-015
  exception item 7 explicitly tolerates a pre-archived manifest member: the
  cascade operation is idempotent and still returns it in `archived_ids`, so
  shipment-reconcile's exact-match post-condition holds unchanged.
* **Nothing became executable again.** `137.005-T` / `137.006-T` stay in
  `.backlogit/archive/` with `status: archived`, keep their superseded-by
  pointers to `137.003-T`, and declare no dependencies. Ship's pre-mode
  reconcile classifies them `pre-archived` (valid); its Step 0.5 item 1a scan
  halts only on `active`/`done`, never `archived`; and its Step 2 loop has no
  queued or active record to claim. `137.003-T` retains sole atomic ownership.