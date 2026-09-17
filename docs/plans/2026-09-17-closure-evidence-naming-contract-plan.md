---
title: "Closure-evidence naming contract: single source of truth, rewired consumer, write-time validation, composed pinning test"
description: "Implementation plan reconciling the closure-evidence producer/consumer naming contract via a single authoritative contract module, a workspace-anchored path builder, a rewired pipeline-topology closure reader with position-anchored shipment attribution and distinguishable discovery diagnostics, a write-time validation gate that reuses the consumer's own acceptance predicate, atomic producer-spec reconciliation across template and installed mirror, and a composed producer/consumer state-machine test built entirely from temporary fixtures — unblocking 162-S/174-S closure recognition and therefore 163-S, with zero closure artifacts modified."
doc_type: plan
source: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 is a full canonical rewrite of this document. The plan is maintained as one coherent specification of the final intended design rather than as an accreting record of corrections; prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body. The authoritative review record, including its bounded audit trail, lives in `linked_review`."
deferred_scope_expansions:
  - AE612665
source_decision: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
source_bug_report: docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md
source_stash_id: FD0CCB42
stash_ids:
  - FD0CCB42
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_review: docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md
tags:
  - "closure"
  - "contract-drift"
  - "pipeline-topology"
  - "producer-consumer"
  - "fail-closed-design"
---

# Closure-Evidence Naming Contract — Implementation Plan

Source decision: `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md`
(Option C adopted; decisions **D1**–**D9** are binding on this plan and are
referenced by ID throughout).

## Problem Frame

`FilesystemTopologyReaders.closure_complete()`
(`src/autoharness/gates/topology.py:714-725`) discovers post-merge closure
evidence with a single hard-coded glob:

```python
matches = sorted(closure_dir.glob(f"{shipment_id}-*-post-merge-closure.md"))
if not matches:
    return None
```

The `operational-closure` skill — in both the template
(`templates/skills/operational-closure/SKILL.md.tmpl:23`, which carries the
`{{DOCS_CLOSURE}}` placeholder) and the installed dogfood mirror
(`.github/skills/operational-closure/SKILL.md:23`, which carries the rendered
literal `docs/closure`) — documents its output as
`{YYYY-MM-DD}-{slug}-closure.md`. No filename satisfies both contracts.
Discovery is filename-first, so a conforming producer output is never opened,
and the reader's `None` is consumed by `_shipment_readiness_check`
(`topology.py:1866-1882`) as `PREDECESSOR_CLOSURE_INCOMPLETE`.

Verified in this workspace, read-only, 2026-09-17:

| Shipment | Closure artifact present | `closure_complete()` | Effect |
|---|---|---|---|
| `162-S` | `docs/closure/2026-09-11-162-s-154-f-closure.md` (valid, `READY`, `done`) | `None` | **blocks `163-S`** |
| `174-S` | `docs/closure/2026-09-16-174-s-166-f-closure.md` | `None` | blocks any future dependent |
| `173-S` | both namings (ID-anchored authored as a `supersedes:` repair) | `True` | masked by a hand repair |
| `160-S`, `161-S` | ID-anchored only | `True` | unaffected |

`autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json`
returns `exit_code: 1`, `token: PREDECESSOR_CLOSURE_INCOMPLETE`,
`details.predecessor_source: "explicit"`, `details.closure_complete: null`.
Predecessor derivation is correct; only discovery fails.

## Requirements Trace

| # | Requirement (decision / source-report criterion) | Implementation unit(s) |
|---|---|---|
| RQ-1 | `closure_complete("162-S")` is `True` from the committed tree with **zero** closure-artifact changes; `163-S` no longer blocks on `PREDECESSOR_CLOSURE_INCOMPLETE` (D3, D8; criterion 1) | U1, U2 + one-time publication/runtime evidence (see `## Runtime Verification and Closure`) |
| RQ-2 | The filename contract is stated in exactly one machine-readable place; producer and consumer both derive from it (D1; criterion 2-naming half) | U1, U5, U9 |
| RQ-3 | Canonical WRITE pattern is `{DOCS_CLOSURE}/{shipment_id}-{feature_id}-post-merge-closure.md` (D2) | U1, U10, U5, U6 |
| RQ-4 | The RECOGNIZED READ set is permanent, closed, and exactly two fully-anchored patterns (D3) | U1, U8, U12 |
| RQ-5 | Discovery resolves deterministically for zero-, one-, and multi-match (D5; criterion 4) | U1, U2, U7 |
| RQ-6 | Absent / unrecognized-name / invalid-metadata are separately diagnosable; the unrecognized case names the candidate path found and the pattern expected (D4; criterion 5) | U2, U3 |
| RQ-7 | Write-time validation fails a non-conforming artifact at authoring time, using the **same** validity definition as the consumer (D6; criterion 3) | U4, U11, U5 |
| RQ-8 | Producer spec reconciled in template **and** installed mirror atomically (D1, R4) | U5 |
| RQ-9 | Ship agent references aligned in template **and** installed mirror atomically (D1, R4) | U6 |
| RQ-10 | A composed test drives the documented producer path into the real consumer reader and fails if either side changes alone, using **temporary fixtures only** — never the committed corpus (D7; criterion 6) | U7, U10 |
| RQ-11 | Regression coverage for the three historical failure shapes plus the ID-collision hazard (criterion 7, R2) | U8, U12 |
| RQ-12 | A non-drift guard ties documented pattern text to the code constant, and the documented constant is **derived** from the machine template (R8; criterion 1) | U1, U9 |
| RQ-13 | The gate remains fail-closed: validity predicate byte-unchanged, malformed frontmatter still raises (D3, R1, R3; criterion 6, non-goals) | U2, U8, U12 |
| RQ-14 | Zero files under `docs/closure/` are created, renamed, edited, or deleted (D8) | verification step (all units) |
| RQ-15 | Path construction is anchored to the **resolved workspace root**. `workspace_root` resolves first; a relative `closure_dir` is anchored as `workspace_root / closure_dir` and is **never** resolved against the process CWD. Separators, traversal, absolute, drive, UNC, and malformed IDs are rejected, and the resolved closure directory, the resolved output path, and the output's parent are all asserted against the resolved root, including through symlinks and Windows junctions | U10 |
| RQ-16 | The contract change adds **no** member to the `TopologyReaders` protocol and modifies **no** existing implementer or test double | U2, U3 |
| RQ-17 | There is exactly **one** canonical ID domain. The write grammars are uppercase-only and case-sensitive; the canonical read pattern **R1** is composed from them and is uppercase-only, so R1's accepted domain and the builder's accepted domain are identical **in both directions**. Lowercase tolerance exists **only** in the legacy read pattern **R2** and its case-folded comparison | U1, U10 |
| RQ-18 | Candidate attribution parses the shipment ID from its **designated filename position** under the anchored R1/R2 grammar and compares the parsed identifier using **that position's own comparison rule** — exact, case-sensitive for the canonical position, `str.casefold()` for the legacy position, mirroring RQ-17 so casefold tolerance never leaks onto the canonical position. A requested shipment token is **never** searched for elsewhere in a filename, and in particular never inside an R2 free-form suffix | U1, U3 |
| RQ-19 | The **authoritative contract module itself** is a registered member of the contract-owned runtime surface, so the runtime-scope non-drift scan is satisfiable without creating a second narrative allowlist | U1, U9 |
| RQ-20 | Write-time and read-time validity are proven identical across **every** consumer-predicate branch. Because the authoritative predicate returns a boolean, the CLI's frontmatter rejection is a **generic authoritative-predicate rejection**; field- and reason-specific diagnostics are emitted only for the checks the CLI itself owns | U4, U11 |

## Contract Specification

This section is the normative statement of the contract. Every unit below
implements a part of it; no unit restates it.

### C1 — Identifier grammars (write side, uppercase-only, case-sensitive)

```text
CLOSURE_SHIPMENT_ID_PATTERN = \A(?P<ordinal>[A-Za-z0-9]+)-(?P<kind>S)\Z
CLOSURE_FEATURE_ID_PATTERN  = \A(?P<ordinal>[A-Za-z0-9]+)-(?P<kind>F)\Z
```

The ordinal is ASCII alphanumeric with **no** internal hyphen. The kind letter
is the uppercase canonical form. These two grammars are the single definition
of what an identifier *is* in this contract; every other component consumes
them rather than restating them.

### C2 — Recognized read set (closed, exactly two, fully anchored)

```text
R1 canonical: \A(?P<shipment_id>[A-Za-z0-9]+-S)-(?P<feature_id>[A-Za-z0-9]+-F)-post-merge-closure\.md\Z
R2 legacy:    \A(?P<date>\d{4}-\d{2}-\d{2})-(?P<shipment_id>[A-Za-z0-9]+-[Ss])-(?P<suffix>.+)-closure\.md\Z
```

Both are module-level compiled constants. A module-level constant is compiled
at import time and therefore cannot interpolate a call-time `shipment_id`: the
patterns are **generic and capture the identifier**, and shipment matching is an
explicit comparison on the captured group — never a substring search and never a
per-call recompile.

**R1 is the read side of what the builder writes.** Its two identifier segments
are composed from C1's grammars, including their uppercase kind letters, so
R1's accepted domain and the builder's accepted output domain are the same set
in both directions:

* every name the builder emits matches R1, with `shipment_id` captured **exactly
  equal** to the builder's input; and
* every `(shipment_id, feature_id)` pair R1 captures is accepted by
  `validate_closure_id` for the corresponding field.

R1's shipment comparison is therefore **exact, case-sensitive string equality**.

**R2 is read-only over a closed, immutable, already-committed corpus.** Its
suffix is a free-form legacy slug (`154-f`, `165-f`, and older shapes); binding
it to a grammar would silently de-recognize committed history. Its kind letter
accepts `[Ss]` and its shipment comparison is `str.casefold()` equality, because
the legacy corpus lowercases identifiers
(`2026-09-11-162-s-154-f-closure.md`). **Lowercase tolerance exists here and
nowhere else.** No claim of domain coincidence is made for R2 in either
direction; the only cross-pattern property asserted is that **no builder output
can ever match R2** (its second hyphen-delimited token is the literal kind
letter, which can never satisfy R2's `\d{2}` date component), which is what
makes the write contract singular while the read contract is plural.

### C3 — Candidate attribution (designated-position parse, never a token search)

```text
attribute_closure_candidate(filename, shipment_id) -> bool
```

Attribution answers whether a file in a shared closure directory is a candidate
*for the requested shipment* at all. It is a **parse at a designated position**,
not a search:

1. Try the legacy shipment position
   `\A\d{4}-\d{2}-\d{2}-(?P<shipment_id>[A-Za-z0-9]+-[Ss])(?:-|\Z)` — the
   position R2 reserves for the identifier, immediately after the date prefix.
2. Otherwise try the canonical shipment position
   `\A(?P<shipment_id>[A-Za-z0-9]+-[Ss])(?:-|\Z)` — the leading position R1
   reserves for the identifier.
3. If neither position parses, the file is **not attributed**.
4. Otherwise compare the **single parsed group** to the requested identifier
   using the comparison rule **of the position that matched**: **exact,
   case-sensitive** whole-captured-group equality when the **canonical**
   position (step 2) matched, and **`str.casefold()`** equality when the
   **legacy** position (step 1) matched.

This mirrors C2/RQ-17 exactly: lowercase tolerance exists **only** in the
legacy position's comparison. A canonically-positioned name such as
`162-S-167-F-post-merge-closure.md` is **not** attributed to a differently-cased
request such as `162-s`, because the canonical position's comparison is exact —
casefold tolerance does not leak from the legacy position onto the canonical
one.

The requested shipment token is never looked for anywhere else in the filename.
In particular it is never looked for inside an R2 free-form suffix: a foreign
record such as `2026-09-11-16-S-supersedes-162-S-closure.md` parses to `16-S`
and is **not** attributed to a request for `162-S`, even though the requested
token appears literally in its suffix. Because the parse consumes a whole
delimited identifier at a fixed position, `16-S` and `162-S` never collide in
either direction.

`unrecognized_candidates` contains only attributed files that match neither
recognized pattern. **Zero attributed candidates yields `absent`**, regardless
of how many foreign records the directory holds — a shared `docs/closure/`
holding 54 artifacts must not turn a correct `absent` verdict into a spurious
`unrecognized` block.

### C4 — Path construction and workspace containment

```text
build_closure_path(closure_dir, shipment_id, feature_id, *, workspace_root) -> Path
```

`workspace_root` is an **explicit, required, keyword-only** parameter. It is
never inferred from the process CWD, never discovered by walking parents, and
never defaulted. Callers supply it from their own established workspace
context: the topology reader passes `FilesystemTopologyReaders.workspace`, and
the `gate closure-evidence` CLI passes its `--workspace` value.

The ordered algorithm is:

1. Validate **both** identifiers through `validate_closure_id` **before** any
   path join.
2. **Resolve `workspace_root` first**: `root = Path(workspace_root).resolve()`.
   This is the only resolution in the call that may consult the process CWD,
   and only because the caller's declared root is the caller's own context.
3. **Anchor `closure_dir` to `root`**: if `closure_dir` is relative it becomes
   `root / closure_dir`; if it is absolute it is taken as given. The anchored
   path is then resolved (`Path.resolve()` collapses `..`, symlinks, reparse
   points, and Windows junctions). A relative `closure_dir` is **never**
   resolved against the process CWD.
4. Assert the resolved closure directory lies inside `root`. This rejects an
   absolute out-of-root directory, a traversal escape, and a symlink or
   junction whose target leaves the tree.
5. Render the canonical filename and resolve the joined output path.
6. Assert the resolved output path also lies inside `root`.
7. Assert the resolved output path's parent equals the resolved closure
   directory.

Any failing assertion raises `ClosureContractError` naming the escaping path and
the root it escaped, rather than returning a path. Step 7 alone is insufficient
and is never the only containment check: an escaping `closure_dir` trivially
contains its own child, so containment must be anchored to the workspace root,
not to the caller's argument.

### C5 — Diagnostic contract

The authoritative validity predicate
(`topology._closure_artifact_complete` / `_closure_conditions_satisfied`,
`topology.py:281-337`) returns a **boolean**. It reports *whether* an artifact
is acceptable, not *why* it was refused. This plan reuses that predicate
unmodified, so no caller may present a field- or reason-specific explanation of
a frontmatter rejection: deriving one would require a second implementation of
the validity logic, which is the exact defect this feature exists to remove.

Diagnostics are therefore partitioned by ownership:

| Check | Owner | Diagnostic granularity |
|---|---|---|
| Filename matches the canonical write pattern | CLI (U4) | Specific — names the filename and the canonical pattern |
| Artifact is discoverable for the declared shipment | CLI (U4) | Specific — names the path, the filename-encoded shipment, and the declared shipment |
| Path is absent, unreadable, or unparseable | CLI (U4) | Specific — names the path; exit `2` |
| Frontmatter satisfies the acceptance predicate | `topology._closure_artifact_complete` (unchanged) | **Generic** — names the path and the authoritative predicate, and quotes the predicate's documented requirement summary from a single contract-owned constant |
| Discovery outcome at gate time | Gate (U3) | Token-level — `PREDECESSOR_CLOSURE_UNRECOGNIZED` names attributed candidate paths and the expected pattern; `PREDECESSOR_CLOSURE_INCOMPLETE` otherwise |

### C6 — Durable-test fixture policy (explicit exception for legacy shapes)

Every durable test in this plan builds its fixtures in a **temporary scratch
workspace**. No durable test reads, globs, stats, or asserts against
`docs/closure/`.

Within that rule there is one explicit, necessary exception. The canonical
builder cannot emit an R2 name — by C2 no builder output can ever match R2 —
so an R2 fixture cannot be builder-created and **must not be required to be**:

* **R1 (canonical) fixture names MUST come from `build_closure_path(...)`.** A
  hand-written canonical literal is a defect, not a shortcut: such a fixture
  would have passed throughout all six historical occurrences of this defect.
* **R2 (legacy) fixture names come from exactly one dedicated, test-only legacy
  filename helper**, `legacy_closure_filename(...)` in
  `tests/_closure_legacy_names.py` — following the repository's established
  `tests/_*.py` shared test-helper convention (`_assertion_render.py`,
  `_env_patch.py`, `_git_env.py`). The helper is **not** part of the contract
  module, is never imported by production code, and exists in exactly one place
  so that the legacy shape has a single test-side definition.

Real-corpus verification is **one-time publication/runtime evidence** captured at
execution time into this work's closure artifact, not a durable assertion. A
durable corpus sweep would couple the normal suite to mutable repository
history, and is already unsatisfiable: `docs/closure/138-S-129-F-cancellation-closure.md`
matches neither recognized pattern.

## Implementation Units

Twelve units. Each satisfies the 2-hour rule (< 3 production files,
< 5 functions, ≤ 4 named test scenarios), width isolation (a single domain per
unit), and produces an atomic verifiable milestone. They are listed in
execution order.

### U1 — Closure-evidence contract module *(domain: Python source)*

**Files**: `src/autoharness/gates/closure_contract.py` (new),
`tests/test_closure_contract.py` (new).

**Changes**

* `CANONICAL_CLOSURE_FILENAME_TEMPLATE` — the single authoritative write pattern
  string (D2).
* `CANONICAL_CLOSURE_PATTERN_DOC` — **derived, not authored**: computed from
  `CANONICAL_CLOSURE_FILENAME_TEMPLATE` by a pure function
  `_render_pattern_doc(template)`, so the human-readable text the producer
  skills must quote verbatim cannot be edited independently of the machine
  pattern. A duplicated literal here would be a second source of truth and is a
  defect (R8).
* `CLOSURE_SHIPMENT_ID_PATTERN` and `CLOSURE_FEATURE_ID_PATTERN` exactly as
  specified in **C1**.
* `RECOGNIZED_CLOSURE_PATTERNS` — an ordered, **closed** tuple of exactly the
  two compiled patterns specified in **C2**, with R1's identifier segments
  composed from C1's grammars rather than re-typed.
* `CLOSURE_PREDICATE_REQUIREMENT_DOC` — the single contract-owned summary of
  the authoritative acceptance predicate's documented requirements, quoted by
  the CLI's generic rejection message (**C5**). It is descriptive text only and
  makes no validity judgement.
* `attribute_closure_candidate(filename, shipment_id) -> bool` exactly as
  specified in **C3**, including the two designated-position patterns.
* `classify_closure_candidates(closure_dir, shipment_id) -> ClosureDiscovery` —
  returns a frozen dataclass carrying `canonical_matches`, `legacy_matches`,
  `unrecognized_candidates`, and an `outcome` of
  `absent | unrecognized | recognized`, applying D5's ordering: the canonical
  partition wins outright when non-empty; within a partition, candidates are
  returned in deterministic sorted order. Candidate collection is gated by
  `attribute_closure_candidate`.
* `CONSUMER_SITES` — an enumerated tuple of the runtime and producer sites that
  derive from this contract: the topology reader, the validation CLI, the two
  producer skill files, and the two Ship agent files.
* `CONTRACT_DEFINITION_SITE` — the in-source declaration of this module's own
  repository-relative path (`src/autoharness/gates/closure_contract.py`).
  `CONSUMER_SITES` enumerates *consumers*; the authoritative definition is not a
  consumer, yet it lives under `RUNTIME_SCAN_ROOTS` and necessarily contains the
  pattern definition. Registering it **inside the contract** keeps U9's accepted
  set derivable as `(CONTRACT_DEFINITION_SITE,) + CONSUMER_SITES` — one
  contract-owned surface, not a second narrative allowlist.
* `RUNTIME_SCAN_ROOTS` — the declared scan scope for U9: `src/autoharness/`,
  `templates/skills/operational-closure/`, `templates/agents/`,
  `.github/skills/operational-closure/`, `.github/agents/`. Narrative
  directories (`docs/`) and test code (`tests/`) are outside the scan scope by
  construction, because plans, decisions, reviews, closure records, and compound
  learnings legitimately quote the pattern as prose.

**Scope guard**: this module performs **no** frontmatter parsing and makes **no**
validity judgement. It answers "which files are candidates for this shipment,
and how are they classified by name" and nothing else. Path construction,
workspace containment, and ID validation are U10's surface.

**Tests (4)** — scenarios 1 and 2 are parametrized:

1. **Classification matrix** — canonical / legacy / both / neither, parametrized
   to include the uppercase-only rejects: a canonical-shaped name whose feature
   segment carries an internal hyphen, a wrong kind letter, or a free-form slug
   is **not** canonical, and a canonical-shaped name with **lowercase** kind
   letters (`162-s-154-f-post-merge-closure.md`) is **not** R1 — lowercase
   tolerance is R2-only (RQ-17).
2. **Attribution matrix** — parametrized over: `16-S` versus `162-S` in the
   **designated primary position** of both grammars, in both directions;
   `16-S` versus `162-S` where the requested token appears **only in a
   free-form suffix** (`2026-09-11-16-S-supersedes-162-S-closure.md` requested
   as `162-S`, and the R1-shaped equivalent) — **not attributed**; a
   **canonical-position name requested under a differently-cased token**
   (`162-S-167-F-post-merge-closure.md` requested as `162-s`) — **not
   attributed**, proving the legacy position's casefold tolerance does not leak
   onto the canonical position's exact comparison (RQ-17); and an **absent
   requested shipment in a non-empty directory**, which yields
   `outcome == absent` with **empty** `unrecognized_candidates` (RQ-18).
3. **Deterministic ordering** under multiple matches.
4. `RECOGNIZED_CLOSURE_PATTERNS` has exactly two members (H1.4 cardinality pin).

**Posture**: test-first.

### U10 — Closure path builder with strict ID validation and workspace containment *(domain: Python source)*

**Files**: `src/autoharness/gates/closure_contract.py` (extended),
`tests/test_closure_contract_path.py` (new).

The builder is the only part of the contract module that accepts caller-supplied
identifiers and turns them into a filesystem path, so it carries an
input-validation obligation the rest of the module does not.

**Changes**

* `validate_closure_id(value, *, field) -> str` — **field-aware**. `field` is
  `"shipment_id"` or `"feature_id"`, and the value is checked against the
  corresponding grammar from **C1**; the validator **consumes** those grammars
  and does not restate them, so builder and classifier cannot drift (RQ-17). It
  raises `ClosureContractError` naming the offending **field and value** when
  the input is empty or whitespace, contains a path separator (`/` or `\`),
  contains a traversal segment (`.` or `..`), is absolute (`/…`), carries a
  drive designator (`C:`), is a UNC path (`\\server\share`), contains a null
  byte or control character, carries an internal hyphen in the ordinal segment,
  carries a lowercase or wrong kind letter, or otherwise fails its field's
  pattern.
* `build_closure_path(closure_dir, shipment_id, feature_id, *, workspace_root) -> Path`
  implementing **C4** exactly — resolve the root first, anchor a relative
  `closure_dir` under the resolved root, never resolve `closure_dir` against the
  process CWD, then assert directory containment, output containment, and parent
  equality in that order. This is the **only** construction path U7's composed
  test may use for canonical names.

**Scope guard**: no frontmatter parsing and no validity judgement. The builder
never creates a directory, never writes a file, and never touches
`docs/closure/` (D8).

**Tests (4)** — bounded negative battery, all four parametrized:

1. **Accepted-domain round-trip, both directions** (RQ-17) — parametrized over
   the complete accepted boundary set (numeric ordinal, alphanumeric ordinal,
   single-character ordinal, long ordinal). Forward: every accepted
   `(shipment_id, feature_id)` pair builds a path that
   `classify_closure_candidates` classifies as **canonical** for that shipment,
   with the captured `shipment_id` **exactly equal** (no case folding) to the
   input. Reverse: every identifier pair R1 captures is accepted by
   `validate_closure_id` for its field. The two accepted domains are asserted to
   be the same set.
2. **Path-escape inputs are rejected** — parametrized over separators (`a/b`,
   `a\b`), traversal (`..`, `.`, `../x`), absolute (`/162-S`), drive
   (`C:162-S`), UNC (`\\srv\share`). Each raises `ClosureContractError` naming
   the field.
3. **Grammar rejects** — parametrized over empty, whitespace, a null byte, a
   leading/trailing/doubled hyphen, an internal-hyphen ordinal (`16-2-S`), a
   **lowercase kind letter** (`162-s`) on the write path, a cross-field kind
   letter (`162-F` as `shipment_id`, `154-S` as `feature_id`), and a non-ASCII
   segment. Each raises `ClosureContractError` naming the field and the value.
4. **Workspace-anchoring and containment matrix** (RQ-15) — the whole scenario
   runs with the **process CWD set to a temporary directory outside the
   workspace root** (`monkeypatch.chdir`), which is what makes the anchoring
   assertions meaningful. Parametrized over: a **relative** `closure_dir`
   (accepted, and the built path is asserted to lie under `workspace_root` and
   **not** under the CWD); an absolute in-root `closure_dir` (accepted); an
   absolute out-of-root `closure_dir` (**rejected**); a relative `closure_dir`
   that traverses out of the root (**rejected**); an in-root `closure_dir`
   reached through a symlink that stays inside the root (accepted); an in-root
   `closure_dir` whose target is a symlink or junction pointing outside the root
   (**rejected**); and a resolved output path landing outside the root
   (**rejected**). Each rejection names the escaping path and the workspace
   root. The symlink/junction rows are skipped with an explicit reason on
   platforms where the test process cannot create them, and never silently
   passed.

**Posture**: test-first.

**Depends on**: U1.

### U2 — Rewire the topology closure reader onto the contract *(domain: Python source)*

**Files**: `src/autoharness/gates/topology.py`, `tests/test_gates_topology.py`.

**Changes**

* `FilesystemTopologyReaders` gains a **reader-internal** structured discovery
  method `closure_discovery(shipment_id) -> ClosureDiscovery` that delegates to
  `classify_closure_candidates`. This is the **single source of filesystem
  observation** for closure evidence: `closure_complete()` is reimplemented as a
  thin predicate over `closure_discovery(...)`'s result and performs no
  directory listing of its own, so the two can never disagree about what is on
  disk.
* `closure_complete()` keeps its existing `bool | None` return type and its
  existing signature.
* **No change to the `TopologyReaders` protocol** (`topology.py:118-131`) and
  **no change to `_NullReaders`** (`topology.py:728-751`). Adding a member to
  the broad structural protocol would force a mechanical edit across the ~16
  in-repo test doubles in `tests/test_gates_topology.py`, which both exceeds
  this unit's granularity envelope and contradicts the compatibility this change
  claims. U3 reaches the richer diagnostics through a **capability accessor**
  instead, which duck-types the optional method and returns `None` for any
  reader that does not expose it. Every existing protocol implementer remains
  valid **unmodified** (RQ-16).
* Evaluation order per D5: evaluate canonical matches first, accept on the first
  candidate satisfying `_closure_artifact_complete`; only if the canonical
  partition is empty, evaluate legacy matches the same way.

**Explicitly unchanged (RQ-13)**: `_closure_artifact_complete`
(`topology.py:303-337`) and `_closure_conditions_satisfied`
(`topology.py:281-300`) are **byte-identical** after this unit. `_frontmatter`'s
`BacklogUnavailableError` raise path is untouched, so malformed frontmatter
still fails closed as `BACKLOG_UNAVAILABLE`. The protocol declaration,
`_NullReaders`, and every test double in `tests/test_gates_topology.py` are
likewise untouched.

**Tests (3)**: legacy-named valid artifact now returns `True`; canonical takes
precedence when both exist; malformed frontmatter under a recognized name still
raises `BacklogUnavailableError`.

**Posture**: characterization-first — pin current behaviour for the ID-anchored
corpus before changing discovery.

**Depends on**: U1.

### U3 — Distinguishable gate diagnostics *(domain: Python source)*

**Files**: `src/autoharness/gates/topology.py`, `tests/test_gates_topology.py`.

**Changes**

* `_shipment_readiness_check` obtains structured discovery through a new
  module-level **capability accessor**
  `closure_discovery_for(readers, shipment_id) -> ClosureDiscovery | None`,
  which duck-types the optional `closure_discovery` method introduced on
  `FilesystemTopologyReaders` in U2 and returns `None` for any reader that does
  not expose it. When it returns `None`, the gate's behaviour is **exactly**
  today's behaviour, so the protocol and its implementers stay unmodified.
* When the outcome is `unrecognized`, it emits the new token
  `PREDECESSOR_CLOSURE_UNRECOGNIZED` with a message naming **the attributed
  candidate path(s) found and the canonical pattern expected**; `absent` and
  `recognized-but-invalid` continue to emit `PREDECESSOR_CLOSURE_INCOMPLETE`
  unchanged (D4). Because attribution is a designated-position parse (**C3**),
  a foreign shipment's record in the shared closure directory can never produce
  this token for a genuinely absent shipment.
* `_shipment_readiness_details` gains `closure_discovery_outcome`,
  `closure_candidate_paths`, and `closure_expected_pattern`. The existing
  `closure_complete` detail key is **retained with unchanged semantics** so no
  existing consumer of the JSON payload breaks.

**Scope guard**: no gate is relaxed. `PREDECESSOR_CLOSURE_UNRECOGNIZED` is a
**blocking** token; it renames a failure, it never permits one. No protocol
member is added in this unit either.

**Tests (3)**: an attributed unrecognized candidate produces the new token with
the candidate path in `details`; a reader that does not expose the capability
produces exactly today's behaviour and the original token; the JSON payload
still carries `closure_complete`.

**Posture**: test-first.

**Depends on**: U2.

### U4 — `autoharness gate closure-evidence` write-time validation *(domain: Python CLI)*

**Files**: `src/autoharness/cli.py`, `tests/test_cli_gate_closure_evidence.py` (new).

**Changes**

* New subcommand `autoharness gate closure-evidence --path <file>
  [--shipment <id>] [--workspace <path>] [--json]`, added as one additional
  branch in the flat dispatcher at `cli.py:369-389`, plus its usage/help block
  alongside the existing `pipeline-topology` / `dag-readiness` blocks.
  `--workspace` is this command's **workspace-root context** and is the value
  passed as U10's required `workspace_root` argument whenever the command
  constructs or validates a closure path (RQ-15).
* Validation, in order:
  1. the filename matches the **canonical write pattern** from U1 — a
     legacy-named artifact is a **write-time failure**, because recognition is
     read-side only (D3);
  2. the artifact satisfies the **complete consumer acceptance predicate**;
  3. the artifact is discoverable for its declared shipment via
     `classify_closure_candidates`.
* **Single validity definition.** Step 2 MUST call the existing consumer
  predicate `topology._closure_artifact_complete` (and, through it,
  `_closure_conditions_satisfied`) directly, by import. Re-implementing a
  scalar-enum check here is a **defect**, not a simplification: such a check
  would accept a `READY_WITH_CONDITIONS` artifact with an unsatisfied or absent
  `conditions:` block that the consumer then rejects, so the write-time gate
  would certify an artifact the read-time gate blocks — a second, weaker
  definition of validity for the same contract. Reuse is import-only; the
  predicate is **not modified**, preserving H1.1 byte-identity.
* **Diagnostic granularity follows C5.** Steps 1 and 3, and an absent or
  unreadable `--path`, are CLI-owned checks and emit **specific** diagnostics
  naming the offending filename, shipment, or path. Step 2 emits a **generic
  authoritative-predicate rejection**: it names the artifact path, names
  `topology._closure_artifact_complete` as the deciding authority, and quotes
  `CLOSURE_PREDICATE_REQUIREMENT_DOC`. It does **not** assert which field or
  which condition caused the refusal, because the predicate returns a boolean
  and deriving a cause would require duplicating validity logic.
* Exit codes follow the established gate convention: `0` pass, `1` validation
  failure, `2` invalid input.

**Scope guard**: validation only. This command never writes, renames, or repairs
an artifact (D8). It is not wired into any pre-existing gate path.

**Tests (4)**: canonical filename + acceptable frontmatter passes with exit `0`;
a legacy filename fails with exit `1` and the canonical pattern quoted; an
absent or unparseable path exits `2` naming the path; the `--json` payload
carries a `failed_check` discriminator (`filename`, `frontmatter_predicate`,
`discoverability`, `input`) together with the path. The semantic battery is U11.

**Posture**: test-first.

**Depends on**: U1, U10.

### U11 — Closure-evidence semantic validation battery *(domain: tests)*

**Files**: `tests/test_cli_gate_closure_evidence.py` (extended).

Proving that the write-time gate and the read-time consumer agree on validity
needs more scenarios than U4's 2-hour envelope allows, and those scenarios are
the evidence for the single-validity-definition decision rather than for the CLI
surface itself.

Equivalence is only credible when **every branch of the consumer predicate** is
exercised on both sides. The predicate
(`_closure_artifact_complete` / `_closure_conditions_satisfied`) has exactly
these branches, enumerated from the live source: `compaction_status` present and
in `{done, degraded}` (case-insensitive, stripped); the **legacy `compaction`
alias key** the consumer falls back to; `compaction` missing or out-of-enum;
`closure_status` missing, non-string, or blank; `closure_status == READY`;
`closure_status == READY_WITH_CONDITIONS` routed through the conditions block;
`BLOCKED` and any other value; and, inside the conditions block, non-list, empty
list, non-mapping entry, `satisfied` not the literal boolean `True` (including
the truthy string `"true"`), and missing / non-string / blank `evidence`.

**Tests (4)** — scenarios 1 and 3 are parametrized:

1. **Consumer-branch parity matrix** — one parametrized scenario whose rows
   cover **every** branch above, each row asserting that the write-time CLI
   verdict and the read-time `_closure_artifact_complete` verdict on the *same
   artifact* are **identical**:
   * accepted — `READY` + `compaction_status: done`
   * accepted — `READY` + `compaction_status: degraded`
   * accepted — `READY` via the legacy `compaction:` alias key, included because
     the consumer supports it and a write-time gate that rejected it would be a
     *stricter* second definition — the same defect mirrored
   * accepted — `READY_WITH_CONDITIONS` + every condition `satisfied: true` with
     non-empty `evidence`
   * rejected — `READY_WITH_CONDITIONS` + absent `conditions:`
   * rejected — `READY_WITH_CONDITIONS` + empty `conditions:` list
   * rejected — `READY_WITH_CONDITIONS` + malformed `conditions:` (not a list; a
     non-mapping entry)
   * rejected — `READY_WITH_CONDITIONS` + `satisfied: "true"` (truthy string,
     not the literal boolean)
   * rejected — `READY_WITH_CONDITIONS` + missing, non-string, or blank
     `evidence`
   * rejected — `closure_status: BLOCKED`
   * rejected — `closure_status` missing / blank / non-string
   * rejected — `closure_status: MAYBE` (out-of-enum)
   * rejected — `compaction_status` missing entirely
   * rejected — `compaction_status: partial` (out-of-enum)

   A row where the two verdicts differ is the exact failure mode under repair
   and fails the suite. The assertion is **equality of the two verdicts**, never
   that each is independently "correct".
2. **Generic predicate-rejection diagnostic** (RQ-20, C5) — a rejected artifact
   (a `READY_WITH_CONDITIONS` record with unsatisfied conditions) exits `1` with
   a message that names the artifact path, names
   `topology._closure_artifact_complete` as the deciding authority, and quotes
   `CLOSURE_PREDICATE_REQUIREMENT_DOC`. The scenario **also asserts the negative
   form**: the message and the `--json` payload carry **no** field-level or
   reason-level cause for the frontmatter refusal, and `failed_check` is
   `frontmatter_predicate`. This is the guard against a future contributor
   re-deriving a per-field explanation and thereby reintroducing a second
   validity definition.
3. **CLI-owned diagnostic fidelity** (parametrized) — for each check the CLI
   itself owns, the diagnostic is specific: a legacy filename names the filename
   and the canonical pattern (`failed_check: filename`); a canonically-named,
   predicate-acceptable artifact whose filename encodes a **different** shipment
   than `--shipment` declares fails with exit `1` naming the path, the
   filename-encoded shipment, and the declared shipment
   (`failed_check: discoverability`); an absent or unreadable path exits `2`
   naming the path (`failed_check: input`).
4. **Predicate reuse is structural** — the CLI module imports
   `_closure_artifact_complete` and contains no independent membership test over
   `closure_status` or `compaction_status` values, asserted by source
   inspection of `src/autoharness/cli.py`. This converts "no second definition"
   from a review observation into a machine check.

**Posture**: test-first.

**Depends on**: U4.

### U5 — Producer spec reconciliation *(domain: skill documentation — template + installed mirror, ATOMIC)*

**Files**: `templates/skills/operational-closure/SKILL.md.tmpl`,
`.github/skills/operational-closure/SKILL.md`.

**Changes** (both files, in **one commit** — R4 / the `165.008-T`+`165.010-T`
precedent):

* Line 23's Output bullet changes to the canonical pattern. The template keeps
  its `{{DOCS_CLOSURE}}` placeholder
  (`{{DOCS_CLOSURE}}/{shipment_id}-{feature_id}-post-merge-closure.md`); the
  installed mirror keeps the rendered literal
  (`docs/closure/{shipment_id}-{feature_id}-post-merge-closure.md`). Both quote
  `CANONICAL_CLOSURE_PATTERN_DOC` verbatim modulo that one substitution, so U9's
  guard can compare them.
* The Output section gains an explicit **required frontmatter keys** statement
  (`closure_status`, `compaction_status`), which the shipped producer spec
  leaves implied by prose alone — the metadata half of the drift under repair.
* A new Required Protocol step mandates invoking
  `autoharness gate closure-evidence` before the closure artifact is committed
  (RQ-7).
* A short note records that the date is carried in frontmatter rather than the
  filename, and that legacy date-prefixed names remain **readable but are never
  written** (D2/D3), so the asymmetry cannot be misread as permission.

**Scope guard**: no other skill section is edited. No other skill file is
touched.

**Tests**: covered by U9's non-drift guard; no runtime behaviour changes here.

**Posture**: migration-first — the documentation must not land before U1 defines
the constant it quotes.

**Depends on**: U1.

### U6 — Ship agent reference alignment *(domain: agent documentation — template + installed mirror, ATOMIC)*

**Files**: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`.

**Changes** (both files, in **one commit**):

* The post-merge closure step (`_ship.agent.md.tmpl:863`, and the corresponding
  installed step) names the canonical closure path and the mandatory
  `autoharness gate closure-evidence` invocation, instead of naming only the
  closure directory. The template retains its `{{DOCS_CLOSURE}}` placeholder and
  the installed mirror retains the rendered literal.
* The step's gate-relevant metadata list names **both** `compaction_status` and
  `closure_status`. The source bug report identifies the omission of
  `closure_status` from the Ship-side guidance as the compounding half of the
  metadata axis; this closes it.

**Scope guard**: no change to Ship's role boundary, closure procedure, P-015
handling, or any other step.

**Posture**: migration-first.

**Depends on**: U5.

### U7 — Composed producer/consumer state-machine test *(domain: tests)*

**Files**: `tests/test_closure_contract_compose.py` (new),
`tests/_closure_legacy_names.py` (new).

**Changes** — the binding construction rule from **D7**: the test **must**
obtain each canonical closure filename from `build_closure_path(...)` exactly as
the producer documentation directs, write a minimal acceptable artifact there,
and feed the result to the **real** `FilesystemTopologyReaders.closure_complete`.
A hand-written literal canonical filename in this test is a **defect**, not a
shortcut: such a fixture would have passed throughout all six occurrences of
this defect.

This unit also creates the single test-only legacy filename helper required by
**C6** (`tests/_closure_legacy_names.py::legacy_closure_filename`), which U8 and
U12 reuse. The helper exists because the canonical builder cannot emit an R2
name; requiring builder creation of an R2 fixture would be unsatisfiable.

**Tests (4)** — all against temporary scratch workspaces; `docs/closure/` is
never read or written:

1. **Composed round-trip** — producer builder → real consumer reader → `True`.
   Fails if either the builder's pattern or the reader's recognition changes
   alone.
2. **Composed precedence** — a temp workspace holding both a builder-created
   canonical artifact and a `legacy_closure_filename(...)` artifact for the same
   synthetic shipment resolves `True`, **and** the canonical artifact is the one
   that produced the verdict (D5 partition precedence). This is the `173-S`
   shape, reproduced as a fixture rather than pinned to the committed record.
3. **Composed legacy acceptance** — a temp workspace holding *only* a
   `legacy_closure_filename(...)` artifact for a synthetic shipment resolves
   `True`. This is the `162-S` / `174-S` shape — the behaviour RQ-1 depends on —
   proven structurally, with the real-corpus instance proven once at publication
   time.
4. **Composed validity coupling** — a builder-created artifact whose frontmatter
   is unacceptable (`READY_WITH_CONDITIONS` with unsatisfied conditions)
   resolves `False`, and a temp workspace containing only a **foreign**
   shipment's builder-created artifact resolves `None`. Recognition never
   implies acceptance, and attribution never admits a neighbour, end-to-end
   across the composed path.

**Posture**: test-first.

**Depends on**: U1, U10 (the builder), U2, U3, U4.

### U8 — Historical failure-shape and ID-collision regressions *(domain: tests)*

**Files**: `tests/test_gates_topology.py` (extended).

All fixtures are temporary; R2 names come from
`tests/_closure_legacy_names.py::legacy_closure_filename` and R1 names from the
builder, per **C6**.

**Tests (4)** — these four shapes are **required** and may not be substituted:

1. **Date-prefixed name, acceptable content** — the shape that silently failed
   for `001-S`, `008-S`, `162-S`, `174-S` — now resolves `True` and is reported
   as a **legacy** match, not a canonical one.
2. **Recognized name, missing frontmatter** — still raises
   `BacklogUnavailableError` → `BACKLOG_UNAVAILABLE` (the `005-S` shape;
   RQ-13).
3. **Recognized name, `compaction_status` without `closure_status`** — still
   fails closed (the second `005-S` axis; predicate unchanged).
4. **Adversarial ID collision, both patterns** — an artifact for `16-S` must not
   satisfy `closure_complete("162-S")`, and an artifact for `162-S` must not
   satisfy `closure_complete("16-S")`, under **both** R1 and R2, including the
   case where the foreign identifier appears only in an R2 free-form suffix.

**Posture**: test-first.

**Depends on**: U2, U7 (for the legacy filename helper).

### U12 — Conditional-state and case-fold regression battery *(domain: tests)*

**Files**: `tests/test_gates_topology.py` (extended, after U8).

All fixtures are temporary; R2 names come from
`tests/_closure_legacy_names.py::legacy_closure_filename` and R1 names from the
builder, per **C6**. These scenarios are the concrete discharge of hardening
items **H1.2** and **H1.3**.

**Tests (3)**:

1. **`BLOCKED` under a recognized name still blocks** (H1.2) — an artifact
   matching R2 whose `closure_status` is `BLOCKED` must still fail the gate,
   proving read-side widening did not weaken the validity predicate: recognition
   admits the file, never the verdict.
2. **`READY_WITH_CONDITIONS` without satisfied conditions still blocks** (H1.3)
   — exercises the `_closure_conditions_satisfied` path
   (`topology.py:281-300`) for both an absent and an unsatisfied `conditions:`
   block. This is the read-time counterpart of U11's write-side parity matrix.
3. **Case-folded legacy ID segment** — a lowercase `162-s` identifier in an R2
   name is recognized through R2's `[Ss]` kind segment and case-folded
   comparison, while a foreign identifier in the same case form is still
   rejected by attribution. Both halves are asserted: case tolerance must not
   become case blindness, and it must not leak onto the R1 path.

**Posture**: test-first.

**Depends on**: U2, U8 (same file; sequenced to avoid a concurrent edit).

### U9 — Producer/consumer non-drift guard *(domain: tests)*

**Files**: `tests/test_closure_contract_nondrift.py` (new).

**Tests (4)**:

1. **Documented pattern equals code constant** — parse the Output bullet from
   `templates/skills/operational-closure/SKILL.md.tmpl` and
   `.github/skills/operational-closure/SKILL.md`, and assert each equals
   `CANONICAL_CLOSURE_PATTERN_DOC` (modulo the `{{DOCS_CLOSURE}}` ↔
   `docs/closure` substitution, which is the only difference the template and
   its installed mirror may have). Changing the pattern in prose alone fails;
   changing it in code alone fails.
2. **Template/installed parity** — the two producer files agree with each other,
   and the two Ship agent files agree with each other, modulo the same
   placeholder substitution (R4).
3. **Consumer-site registry completeness, scoped to runtime surfaces** — every
   path listed in `CONSUMER_SITES` exists, and no file under
   `RUNTIME_SCAN_ROOTS` outside the **registered set** contains a
   closure-filename pattern definition. The registered set is
   `(CONTRACT_DEFINITION_SITE,) + CONSUMER_SITES`, both read from the contract
   module (RQ-19). Registering the authoritative module is required for
   satisfiability: `closure_contract.py` lives under `src/autoharness/` and
   necessarily *is* the pattern definition, so a scan that recognized only
   `CONSUMER_SITES` could never pass. Keeping the registration inside the
   contract — rather than as an exclusion list in the test — is what prevents it
   from becoming a second inventory of the very thing `CONSUMER_SITES` exists to
   be the only copy of. Narrative `docs/` prose and test code are out of scope by
   construction, because the scan roots are read from the contract module.
4. **Pattern-doc derivation guard** — assert
   `CANONICAL_CLOSURE_PATTERN_DOC == _render_pattern_doc(CANONICAL_CLOSURE_FILENAME_TEMPLATE)`,
   i.e. the documented text is *derived from* the machine template rather than
   maintained beside it. Editing the template alone, or the doc constant alone,
   fails. Without this, test 1 would only pin prose to a constant that could
   itself drift away from the pattern the code actually matches.

**Posture**: test-first.

**Depends on**: U1, U5, U6.

## Dependency Graph

```text
U1 (contract module)
 ├─► U10 (path builder + ID validation/containment) ─┐
 ├─► U2 (reader rewire) ─► U3 (gate diagnostics)     │
 ├─► U4 (validation CLI) ◄───────────────────────────┘
 │     └─► U11 (semantic validation battery)
 └─► U5 (producer spec) ─► U6 (Ship agent)

U1,U2,U3,U4,U10 ─► U7 (composed test + legacy filename helper)
U2,U7           ─► U8 (historical shapes + collision) ─► U12 (conditional-state + case-fold)
U1,U5,U6        ─► U9 (non-drift guard)
```

Topologically sorted execution order:
**U1 → U10 → U2 → U3 → U4 → U11 → U5 → U6 → U7 → U8 → U12 → U9**.
No cycles. U3 and U4 are independent of each other; U5/U6 are independent of
U2/U3/U4 beyond their shared dependency on U1. U8 follows U7 because U7 creates
the single legacy filename helper U8 and U12 consume. U12 follows U8 because
both extend `tests/test_gates_topology.py`.

**Critical path**: U1 → U2 → U3 → U7 (the chain that produces RQ-1's unblock
proof).

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| P-D1 | Contract lives in a **new module**, not inside `topology.py` | `topology.py` is a consumer, not the definition. Putting the contract there reproduces the "definition co-located with one consumer" structure that generated the drift. A sibling module also matches `shipment_closure.py` / `bootstrap_grant.py` precedent. |
| P-D2 | `closure_complete()` keeps its `bool \| None` signature; diagnostics arrive via a **reader-internal sibling method** reached through an optional capability accessor | Minimises blast radius on a fail-closed gate. Every existing caller, test double, and protocol implementer keeps working; the richer outcome is opt-in. |
| P-D3 | Name classification (U1) is strictly separated from content validity (U2's use of the untouched predicate) | Keeps the fail-closed validity predicate byte-unchanged and independently reviewable — the single largest safety property of this change (R1, R3). |
| P-D4 | Legacy naming is a **write-time failure** even though it is a read-time success, and no builder output can ever match R2 | The asymmetry *is* the decision (D2/D3). Without a write-side failure, recognition would silently become permission and the canonical pattern would decay into a suggestion. |
| P-D5 | Producer template and installed mirror change in **one** unit | Direct application of the `165.008-T`/`165.010-T` precedent: a split leaves a window where the documented contract and the dogfooded contract disagree — the exact defect shape under repair. |
| P-D6 | Canonical fixture filenames come from the builder; legacy fixture filenames come from one test-only helper | D7 plus C6. A literal canonical filename would have passed through every one of the six historical occurrences and would pin nothing. An R2 fixture cannot come from the builder by construction, so requiring it would make the unit unsatisfiable. |
| P-D7 | Real-corpus assertions on `162-S`/`174-S` are **one-time publication evidence**, not durable tests | They are point-in-time proof of RQ-1 against a corpus that unrelated shipments continue to archive, rename, and extend. Pinning the normal suite to it couples every future change to mutable history and produces failures that name neither the contract nor the cause — and a durable sweep is already unsatisfiable, because `138-S-129-F-cancellation-closure.md` matches neither pattern. |
| P-D8 | New token `PREDECESSOR_CLOSURE_UNRECOGNIZED` rather than overloading the existing one | Compound lesson 8, "Overloading is a defect" and "Unrecognised is loud". The silent `None` conflation is the defect's real cost; a distinct token is the fix. |
| P-D9 | The CLI's frontmatter rejection is **generic**, not field-specific | The authoritative predicate is boolean. A field-specific message would require a second implementation of validity logic, reintroducing the generative defect. Specificity is preserved exactly where the CLI owns the check (C5). |

## Risks and Caveats

Carried from the decision (R1-R9), with plan-level mitigations:

| # | Risk | Mitigation in this plan |
|---|---|---|
| R1 | Read-side widening weakens a fail-closed gate | Closed two-regex enumeration in U1; `_closure_artifact_complete` byte-unchanged in U2 (explicit unit scope guard); U8 tests 2-3 and U12 tests 1-2 assert the fail-closed paths survive. |
| R2 | In-filename ID match collides across shipments | Module-level generic patterns capture the ID; matching is whole-captured-group equality — exact for R1, case-folded for R2 — never a substring search; candidate collection is additionally gated by the designated-position attribution parse (C3). U8 test 4 is a bidirectional adversarial collision test across both patterns including a foreign identifier in an R2 suffix; U1 test 2 covers the attribution boundary; U12 test 3 covers the case-folded form. |
| R3 | `BACKLOG_UNAVAILABLE` regresses to a silent skip | `_frontmatter` untouched (U2 scope guard); U8 test 2 asserts the raise. |
| R4 | Template / installed mirror split-commit window | U5 and U6 are each single atomic units spanning both files; U9 test 2 asserts parity modulo the placeholder substitution. |
| R5 | Composed test degenerates into a fixture | P-D6 states the construction rule as binding: canonical fixtures come from the builder, so a hand-written canonical literal cannot satisfy the unit; legacy fixtures come from one named test-only helper whose non-builder provenance is explicit. The composed-precedence, composed-legacy, and composed-negative scenarios each exercise a distinct reader branch end-to-end, and the one-time real-corpus evidence supplies the non-simulatable point-in-time proof without coupling the durable suite to the corpus. |
| R6 | Scope creep into closure artifact content or adjacent stash entries | RQ-14 verification step; every unit carries an explicit scope guard; the decision's OUT-of-scope list names the excluded stash IDs. |
| R7 | New `blocks` edge introduces a cycle | The fix's shipment is `dag-root` with no outgoing edges (D9); `autoharness gate dag-readiness --json` must report `cycle_detected: false` after the edge is added. |
| R8 | Future producer convention change drifts again | U9 test 1 fails the build unless the change is made at the single source, and U9 test 4 pins `CANONICAL_CLOSURE_PATTERN_DOC` as **derived from** `CANONICAL_CLOSURE_FILENAME_TEMPLATE` so the "single source" cannot itself split into two constants. |
| R9 | New CLI subcommand regresses gate dispatch | Additive branch only (U4); existing gate CLI tests must pass unchanged. |
| R10 | Adding a protocol member breaks third-party and in-repo implementers | Eliminated by design: the protocol is **not** changed. Structured discovery is reader-internal (U2) and reached through an optional capability accessor (U3), so `_NullReaders`, the protocol declaration, and all in-repo test doubles are untouched (RQ-16). The residual risk is a *silent* capability miss — a reader that should expose discovery but does not — which degrades to exactly today's diagnostics rather than to a wrong verdict, and is covered by U3 test 2. |
| R11 | Caller-supplied paths or identifiers escape the workspace root | U10 validates both IDs against their grammars before any join, resolves the workspace root first, anchors a relative `closure_dir` under that resolved root rather than the process CWD, and asserts directory containment, output containment, and parent equality (C4). The containment scenario runs from a CWD outside the root precisely so anchoring is proven rather than assumed. |
| R12 | The write-time gate and the read-time consumer define validity differently | U4 reuses `_closure_artifact_complete` by import instead of re-checking enums; U11 test 1 is a parity matrix asserting identical write-time and read-time verdicts across every consumer-predicate branch; U11 test 4 asserts by source inspection that no second membership test exists in the CLI. |
| R13 | The non-drift consumer-site scan becomes unsatisfiable or spawns a second inventory | The scan is scoped to `RUNTIME_SCAN_ROOTS` and its accepted set is `(CONTRACT_DEFINITION_SITE,) + CONSUMER_SITES`, all read from the contract module itself, so narrative `docs/` prose is out of scope by construction **and** the authoritative module is registered rather than exempted by a hand-maintained list (U9 test 3). |
| R14 | The builder emits a name its own classifier cannot round-trip | There is one canonical ID domain (C1/C2): R1 is composed from the write grammars and is uppercase-only, so its accepted domain is the builder's accepted domain in both directions. U10 test 1 asserts the two domains coincide in both directions with exact identifier equality; U10 test 3's lowercase and internal-hyphen rows are the direct regression. Lowercase tolerance is confined to R2 and its case-folded comparison. |
| R15 | A foreign shipment's record makes an absent shipment look `unrecognized` | Candidate collection is gated by the designated-position attribution parse, so a requested token appearing in a foreign record's free-form suffix is never attributed; U1 test 2 asserts `absent` with an empty candidate list in a non-empty directory, and covers both the primary-position and foreign-suffix `16-S`/`162-S` boundaries. |
| R16 | The authoritative contract module fails its own runtime scan | `CONTRACT_DEFINITION_SITE` registers the module inside the contract, so the scan's accepted set is contract-owned and self-consistent; a future move of the module updates one constant rather than an external allowlist. |
| R17 | Durable tests are coupled to mutable repository history | Every durable scenario builds its fixtures in a temporary scratch workspace (C6); the real-corpus proof is one-time publication/runtime evidence recorded in the closure artifact. `138-S-129-F-cancellation-closure.md` — which matches neither pattern — is the concrete demonstration that a durable corpus sweep is already unsatisfiable. |
| R18 | A field-specific frontmatter diagnostic reintroduces a second validity definition | C5 partitions diagnostics by ownership and P-D9 makes the frontmatter rejection generic; U11 test 2 asserts the negative form (no field-level cause in the message or the JSON payload) and U11 test 4 asserts the CLI contains no independent membership test. |

**Caveat — bootstrap ordering.** This fix's own closure artifact is authored
*after* it merges, so the merged contract governs it and it is discoverable
under either recognized pattern (D9 bootstrap note). `163-S`'s new blocking edge
therefore cannot deadlock on the defect being repaired.

## Plan Hardening Signals (REQUIRED)

| Signal | Present | Justification |
|---|---|---|
| Public API, schema, or contract change | **YES** | The closure-evidence naming contract is a cross-component contract; a new gate token `PREDECESSOR_CLOSURE_UNRECOGNIZED` enters the gate's public token vocabulary; a new CLI subcommand enters the distributed CLI surface. The `TopologyReaders` protocol itself is **unchanged** — recognition is reader-internal discovery, and the diagnostic surface is an **optional duck-typed capability** the gate probes for and degrades without, so no protocol member is added and no existing implementation is invalidated. No JSON schema under `schemas/` changes (OQ-2 deferred). |
| Security, auth, permission, or compliance-sensitive behavior | No | No authentication, authorization, secret handling, or permission surface is touched. Filesystem reads stay within the existing `docs/closure/` traversal already performed by the reader, and the path builder tightens rather than widens the reachable set. |
| Migration, backfill, destructive data/config action, irreversible step | No | **Zero** closure artifacts are created, renamed, edited, or deleted (D8/RQ-14). Recognition is added rather than the corpus migrated — deliberately, so that no irreversible rewrite of committed closure history occurs. |
| External integration, operator checkpoint, or external dependency | No | No external service, network call, or new third-party dependency. backlogit interaction is unchanged. |
| High runtime, rollout, or rollback risk | **YES** | The change rewires a **fail-closed release gate** that authorizes shipment claims. An over-permissive regression would let a shipment claim without genuine closure evidence; an over-restrictive regression would block the entire queue. Blast radius additionally spans the distributed CLI and two template families (`templates/skills/`, `templates/agents/`) plus their installed dogfood mirrors. |

**Requires plan hardening: yes** — 5/5 signals assessed, exactly 2 present.

## Plan Hardening

Applied 2026-09-17 per **P-006**. Hardening was triggered both by the two
present signals above and by the elevated blast radius (fail-closed release gate
+ distributed CLI + two template families).

### H1 — Fail-closed verification is a first-class deliverable, not a side effect

The dominant hazard is **over-permissiveness**: a discovery change that lets a
shipment claim without genuine closure evidence. Hardening requires that the
following be demonstrated, with captured evidence, and not merely asserted:

1. `_closure_artifact_complete` and `_closure_conditions_satisfied` are
   **byte-identical** before and after U2, and remain so through U4's reuse-by-
   import. Evidence: a diff over those line ranges showing zero changes. This is
   a hard acceptance criterion on U2 and U4, not a review observation.
2. An artifact with a recognized name and `closure_status: BLOCKED` still
   blocks. **Discharged by U12 test 1.**
3. An artifact with a recognized name and no satisfied `conditions:` block under
   `READY_WITH_CONDITIONS` still blocks. **Discharged by U12 test 2**, with its
   write-time counterpart in U11 test 1's rejected rows.
4. The recognized-read set is asserted to have **exactly two** members; a test
   fails if a third pattern is added without a corresponding deliberate contract
   change. This converts D3's "closed enumeration" from prose into a machine
   check. **Discharged by U1 test 4.**
5. Caller-supplied identifiers cannot escape the workspace root.
   **Discharged by U10 tests 2-4** (RQ-15).
6. Path resolution is anchored to the resolved workspace root: the root resolves
   first, a relative `closure_dir` is anchored beneath it rather than against the
   process CWD, and the resolved directory, the resolved output, and the
   output's parent are all checked, so containment survives an escaping
   `closure_dir` and symlink/junction indirection.
   **Discharged by U10 test 4**, which runs from a CWD outside the root (RQ-15).
7. The builder's accepted input domain and R1's accepted output domain
   **coincide in both directions**, with exact identifier equality; lowercase
   tolerance is proven to exist only on the R2 path. This converts "round-trip"
   from an assumption into a machine check. **Discharged by U10 test 1, U10 test
   3's lowercase and internal-hyphen rows, and U1 test 1's lowercase-canonical
   row** (RQ-17).
8. Write-time and read-time validity are proven **equivalent across every
   branch** of the consumer predicate, not agreeing at a single sampled point,
   and no caller derives a second field-level judgement from the boolean
   predicate. **Discharged by U11 tests 1, 2, and 4** (RQ-20).

### H2 — Ordering constraint: the gate must not change before the contract exists

U2 must not merge ahead of U1, and U5/U6 must not merge ahead of U1, because
each would create exactly the transient split-contract state this work exists to
eliminate. The dependency graph already encodes this; hardening makes it a
**merge-order constraint**, and U9's parity test (test 2) is the mechanical
detector if it is violated.

### H3 — Explicit negative scope assertion for `docs/closure/`

RQ-14 is hardened from an intention into a verification step with a concrete
command: `git diff --name-status <base>..HEAD -- docs/closure/` must return
**empty** at every commit of this work. Any non-empty result is a halt, not a
discussion — it means the seventh per-artifact workaround is being performed
under the contract fix's name.

### H4 — Rollback is bounded and proven trivial by construction

Because D8 forbids artifact migration, rollback is a pure code/doc revert with
no data-state to unwind. Hardening records this explicitly so a future reader
does not assume a migration exists: **there is no backfill, no state file, no
ledger, and no irreversible step in this plan.** The single reversibility
question — "does reverting re-block `163-S`?" — has the answer "yes, to exactly
its current state", which is a safe restoration rather than a corrupted one.

### H5 — Unsatisfiable-gate check (compound lesson 6)

For every gate outcome introduced or modified, a concrete legitimate passing
state and a concrete legitimate failing state are named in the decision's D3
outcome table. Re-verified during hardening: all seven rows name a real or
constructible state; **no row is unreachable**. Specifically,
`PREDECESSOR_CLOSURE_UNRECOGNIZED` is reachable (a file named `162-S-notes.md`,
which attribution parses to `162-S` at the canonical position) and escapable
(rename to the canonical pattern), so it is not a trap state.

### H6 — Operator checkpoint at the token-vocabulary boundary

Adding `PREDECESSOR_CLOSURE_UNRECOGNIZED` widens the gate's public token
vocabulary. Any downstream consumer that switches on the token set must fail
**loudly** on an unrecognised token rather than falling through (compound lesson
8). Hardening adds a verification item to U3: grep the repository for
token-dispatch sites over `PREDECESSOR_CLOSURE_*` and confirm each either
handles the new token or fails closed on unknown tokens. If a silent
fall-through site is found, it is a **blocking** finding for U3, not a
follow-up.

### H7 — Residual risk accepted

`R2` (ID-collision in the legacy pattern) is the highest residual risk after
mitigation, because the legacy corpus lowercases shipment IDs and therefore
requires case-insensitive matching on that one path, which is inherently weaker
than an exact match. It is accepted because (a) matching is fully anchored with
literal delimiters on both sides of the identifier, (b) attribution parses a
whole identifier at a designated position rather than searching, (c) a dedicated
bidirectional adversarial test covers the realistic collision shape including a
foreign identifier inside a legacy suffix, and (d) the legacy pattern is
read-only and applies to a **closed, finite, already-committed** corpus that
will never grow.

## Runtime Verification and Closure

| Unit | Changes a runtime surface? | Runtime verification required | Closure expectation |
|---|---|---|---|
| U1 | No (library only) | Unit tests green | — |
| U10 | No (library only) | Unit tests green; negative and containment batteries green, including the out-of-root CWD rows | — |
| U2 | **Yes** — topology gate behaviour | `autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json` transitions from `exit_code: 1` / `PREDECESSOR_CLOSURE_INCOMPLETE` to a pass on this check, captured verbatim before and after. **Plus the one-time real-corpus proof**: `closure_complete("162-S") is True`, `closure_complete("174-S") is True`, and `closure_complete("173-S") is True` with the canonical artifact producing the verdict, executed once against the committed `docs/closure/` tree and captured verbatim. This is the non-simulatable, point-in-time evidence for RQ-1 that the durable suite deliberately does not pin (RQ-10). | Before/after gate JSON **and** the one-time real-corpus transcript in the closure artifact |
| U3 | **Yes** — gate token vocabulary and JSON payload | Construct an attributed unrecognized candidate in a scratch workspace and confirm `PREDECESSOR_CLOSURE_UNRECOGNIZED` with the candidate path in `details`; confirm `details.closure_complete` still present; confirm the gate degrades cleanly when the reader does **not** expose the optional diagnostic capability | Token-vocabulary change recorded |
| U4 | **Yes** — new CLI subcommand | `autoharness gate closure-evidence --help`; one passing and one failing invocation with exit codes and `failed_check` recorded | CLI surface addition recorded |
| U11 | No (tests) | Semantic battery green; the consumer-branch parity matrix green across every branch | — |
| U5 | No (documentation) | `autoharness verify` / harness verification passes; rendered template resolves `{{DOCS_CLOSURE}}` with no unresolved `{{...}}` | Template-contract change recorded |
| U6 | No (documentation) | Same as U5 for the agent template family | Agent-contract change recorded |
| U7 | No (tests) | Full test suite green. Fixtures are **corpus-independent** — every scenario builds into a temporary scratch workspace, so the suite does not read or depend on `docs/closure/` (RQ-10) | Composed-test existence recorded as the durable non-drift guarantee |
| U8, U9, U12 | No (tests) | Full test suite green | Non-drift and semantic guards recorded |

**Rollback trigger**: any post-merge observation of a shipment passing
`pre_claim` without genuine, valid closure evidence, or of a previously-passing
shipment newly blocked, is an immediate rollback trigger. Rollback is a plain
revert — no data migration is involved, which is a direct consequence of D8.

**Validation window**: the next `pre_claim` evaluation of `163-S` is the first
real-world exercise of the change and is the designated observation point.

## Review Status

**Current verdict: PASS** — 0 × P0, 0 × P1 open. The authoritative review
record, including its bounded audit trail of superseded findings, is
`docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md`. That
record is the single place review history is kept; this plan states only the
design it currently specifies.
