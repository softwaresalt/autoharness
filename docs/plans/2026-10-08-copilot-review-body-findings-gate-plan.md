---
title: "Copilot review-body findings: deterministic P-018 BLOCK with disposition markers, plus body-aware shadow-review loop"
description: "Fix stash 38D29192. Teach autoharness gate copilot-review to detect threadless findings in Copilot review bodies and block on them until a PR disposition comment names the review. Teach the PR-automation loop, the P-018 policy, and Ship 7c to read, handle, and record review-body findings."
doc_type: plan
status: reviewed
created: 2026-10-08
source_stash: 38D29192
source_deliberation: docs/decisions/2026-10-08-copilot-review-body-findings-gate-deliberation.md
source_learning: docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md
review_record: docs/reviews/2026-10-08-copilot-review-body-findings-gate-plan-review.md
operator_decision: "Stage this shipment FIRST, ahead of the queued DAG; declared root with the dag-root label (operator-authorized, 2026-10-08, Orchestrator relay)."
requires_plan_hardening: "yes"
---

# Copilot review-body findings: P-018 BLOCK with disposition markers

## Outcome

After this plan ships:

* `autoharness gate copilot-review` returns the new BLOCK verdict
  `UNDISPOSITIONED_BODY_FINDINGS` (exit 1) under these conditions:
  * a completed Copilot review on the PR, in any round, carries threadless
    findings in its body (`Previously missed (N)`, `Suppressed comments (N)`, or
    unanchored open findings);
  * no PR conversation comment carries the line
    `Copilot-Review-Body-Disposition: <review databaseId>`.
* The agent clears the block itself. It handles each finding (fix and push, or
  P-021 C2 capture, or decline with rationale), then posts one disposition
  comment that quotes the findings and cites the SHA or stash ID. This mirrors
  reply-and-resolve for threads. No `--force` is needed.
* The PR-automation instruction, the P-018 policy, and Ship 7c name the new
  verdict and teach the loop to read every review body. The Local Review
  Readiness block records body findings explicitly, so a body-only finding can
  no longer be reported as "0 comments".
* The exit codes, `PASS_VERDICTS`, enforcement modes, `--max-wait`, and
  `--force` auditing are unchanged.

## Problem Frame

PR #506 rounds 2 to 5 (HEADs `fb68e399`, `b879a045`, `24d5fc13`, `a5e571a5`) each
carried one valid finding only in a collapsed `Previously missed (1)` body
section, under a `0 open findings` headline, with no thread. The gate returned
`SATISFIED` each time, for these reasons:

* `_GRAPHQL_QUERY` in `src/autoharness/gates/copilot_review.py` does not fetch
  the review `body` or `databaseId`, or the PR conversation `comments`.
* `parse_graphql_response()` builds `ReviewRecord(state, commit_oid)` only.
* `classify()` checks only `completed_for_head()` and
  `copilot_unresolved_thread_ids`.

On the instruction side, `github-pr-automation.instructions.md` handles comments
and threads in §1.2 to §1.8, and §1.9.2's readiness block has no body-finding
field.

This is the fourth recorded recurrence: 114-S / PR #297, PR #436, PR #444
(stash 58A85283), and PR #506. The full analysis, the observed body formats,
and the option comparison are in the source deliberation.

## Requirements Trace

| # | Requirement (deliberation decision) | Unit |
|---|---|---|
| R1 | Pure detector counting threadless findings `max(S, PM) + U` over both observed formats (D2) | U1 |
| R2 | Fetch review `databaseId` and `body` and PR conversation `comments`, and parse them fail-closed (D3, D4, D5) | U2 |
| R3 | Recognize disposition markers `^Copilot-Review-Body-Disposition: <databaseId>$` from non-Copilot comments (D4) | U2 |
| R4 | New BLOCK verdict after `UNRESOLVED_THREADS`; result and JSON carry the undispositioned review IDs; PASS set and exit codes unchanged (D1) | U3 |
| R5 | CLI human output prints the undispositioned count and the marker hint (D1) | U4 |
| R6 | Gate reference doc covers the verdict, the detector rules and limits, the marker contract, and rollout; CHANGELOG entry (D1 to D5, OQ-1, OQ-2) | U5 |
| R7 | PR-automation loop reads bodies, classifies findings, handles threadless findings, posts the disposition comment, defines a clean round, counts cycles, and updates the readiness field and Check 5 / §1.9.5 (D6) | U6 |
| R8 | P-018 policy text: third condition and the new verdict (D6) | U7 |
| R9 | Ship 7c: the new verdict and its remediation (D6) | U8 |
| R10 | Cross-surface pin: verdict name and marker literal in every surface, derived from code constants (risk mitigation) | U9 |
| R11 | Advisory detail when a body carries `ccr-overview-v<N>` with N ≠ 2 (OQ-1) | U1 (detect), U3 (surface) |

## Implementation Units

Every unit follows the 2-hour rule and width isolation. Code units pair one
production file with its test file. Rendered-surface units are the accepted
**template + mirror + manifest-checksum triple** (precedent: 192-F A5/A5b/A6,
192.025-T). Canonical test gate:
`$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

### U1: Pure review-body threadless-finding detector (code + tests)

**Files (2):**

* `src/autoharness/gates/copilot_review.py`
* `tests/test_gates_copilot_review_body.py` (new)

**Changes:**

* Add a frozen dataclass `BodyFindings`:
  * `count: int`
  * `markers: tuple[str, ...]`, with values from
    `{"previously_missed", "suppressed", "unanchored_open"}`
  * `overview_version: int | None`
* Add a pure `detect_body_findings(body: str) -> BodyFindings` (standard library
  `re` only).
* Define module-level compiled patterns, case-insensitive. Each count group
  allows optional `**` or `<strong>`/`</strong>` wrappers:
  * `Previously missed \((\d+)\)` gives PM;
  * `Suppressed comments \((\d+)\)` gives S;
  * open findings `(\d+) open findings?` gives N_open, taking the first
    occurrence;
  * the anchor `#discussion_r\d+`;
  * the overview marker `<!--\s*ccr-overview-v(\d+)\s*-->`.
* Compute U (revised per plan review PR-3):
  * When N_open ≥ 1, the open-findings span runs from the end of the
    open-findings match to the next **section header** or the end of the body.
    A section header is a `<summary>` whose first child is `<strong>`
    (`<summary>\s*<strong>`) or a `### ` heading line.
  * Nested per-finding `<summary><picture>…` blocks are not section headers,
    so a nested `</details>` cannot truncate the span.
  * Count the anchors `A` in that span. U = max(0, N_open − A).
  * The anchors in a `resolved since last review` section lie outside the span
    because that section starts with its own `<summary><strong>` header.
* `count = max(S, PM) + U`. The empty string gives `count=0`.
* Export the constants `DISPOSITION_MARKER = "Copilot-Review-Body-Disposition:"`
  and `KNOWN_OVERVIEW_VERSION = 2`. U2 and U9 consume them.

**Tests (3 scenario groups, each a table of fixture-to-expectation rows run
with `subTest`).** Fixtures are trimmed verbatim excerpts of real bodies, held
as module string constants with icons and images removed. Each fixture keeps
the section structure.

1. **`ccr-overview-v2` bodies:**
   * PR #506 round 2 (`Previously missed (1)`, `**0 open findings**`, and a
     `1 resolved since last review` block with an anchor) gives `count == 1`
     and markers `("previously_missed",)`.
   * PR #506 round 1 (`1 open finding` with one `#discussion_r` anchor) gives
     `0`.
   * PR #506 round 6 (clean) gives `0`.
   * The PR-3 case gives `0`: a synthetic `2 open findings` section with two
     anchored items, one wrapping a nested
     `<details><summary><picture>…</summary>…</details>`.
2. **Legacy and unanchored bodies:**
   * PR #444 legacy (`Suppressed comments (5)` with nested
     `Previously missed (2)`) gives `5`.
   * A synthetic `**2 open findings**` with no list gives `2`
     (`unanchored_open`).
3. **Version and empty:**
   * `<!-- ccr-overview-v3 -->` gives `overview_version == 3`.
   * A body with no markers gives `count == 0` and
     `overview_version is None`.
   * `""` gives `count == 0`.

**Functions touched:** 1 new function and 1 new dataclass.

**Posture:** test-first.

**Size / complexity:** S / medium.

**Depends on:** none.

### U2: Query and parse review bodies and disposition comments, fail-closed (code + tests)

**Files (2):**

* `src/autoharness/gates/copilot_review.py`
* `tests/test_gates_copilot_review.py`

**Changes:**

* `_GRAPHQL_QUERY`:
  * the `reviews(last:100)` nodes add `databaseId body`;
  * `pullRequest` adds
    `comments(last:100){ nodes{ author{ login } authorAssociation body } pageInfo{ hasPreviousPage } }`.
  * The argv arity of `build_query_argv` is unchanged, because the query is one
    element.
* `ReviewRecord` adds `database_id: int | None = None`,
  `body_findings: int = 0`, and `overview_version: int | None = None`. The
  defaults keep existing constructors valid. All three are set here from one
  `detect_body_findings` call (PR-2: the parse path stays in one unit).
* `ReviewState` adds:
  * `dispositioned_review_ids: frozenset[int] = frozenset()`;
  * `comments_complete: bool = True`;
  * a property `undispositioned_body_finding_review_ids -> tuple[int, ...]`.
    It covers completed Copilot reviews (states in `_COMPLETED_STATES`) with
    `body_findings > 0` whose `database_id` is not in
    `dispositioned_review_ids`. It returns them in review order.
* `parse_graphql_response()` additions, fail-closed with `_ambiguous()`:
  * For a Copilot review, a `body` that is neither a string nor None gives
    ambiguous. A None body is treated as `""`.
  * Call `detect_body_findings(body)` and store `.count`.
  * A Copilot review with `count > 0` and a `databaseId` that is not an
    integer (bool rejected) gives ambiguous.
  * The `comments` connection is missing or malformed, or `_strict_nodes`
    returns None: ambiguous.
  * A comment with an unreadable author login: ambiguous.
  * Collect the marker IDs only from **trusted** comments (revised per plan
    review PR-1, the trust boundary). A comment is trusted when both hold:
    * its author is not `COPILOT_LOGIN`;
    * its `authorAssociation` is in the module constant
      `TRUSTED_DISPOSITION_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})`.
  * A comment with any other, missing, or non-string `authorAssociation` is
    **ignored**: it can never clear a disposition. It is **not** ambiguous,
    because ignoring it is already the fail-closed direction.
    * Why: on a public repository any user can post a PR conversation comment,
      but resolving a review thread requires write access. Without the
      association filter, an outside commenter could clear a P-018 BLOCK.
  * The marker pattern is
    `re.compile(rf"^{re.escape(DISPOSITION_MARKER)}[ \t]*(\d+)[ \t]*$", re.MULTILINE)`.
  * `comments_complete = _page_complete(comments, "hasPreviousPage")`. A
    truncated connection is **not** ambiguous by itself. U3 decides.
* `_strict_nodes` and the existing review, thread, and request rules are
  unchanged.
* Update the shared test builders `_graphql(...)` and `_pr(...)`:
  * emit an empty, complete `comments` connection by default;
  * emit `databaseId` and `body` on review nodes when supplied.
  * All 30+ existing tests must then pass unmodified apart from the builders.

**Tests (3 new scenario groups in a new `BodyFindingParseTests` class, table-driven with `subTest`):**

1. **Marker recognition** (a Copilot review with a `Previously missed (1)` body
   and `databaseId` 101):
   * no comments gives `undispositioned_body_finding_review_ids == (101,)`;
   * a non-Copilot comment with `authorAssociation: "MEMBER"` and the line
     `Copilot-Review-Body-Disposition: 101` gives `()`;
   * each of these still gives `(101,)`:
     * the same line authored by `copilot-pull-request-reviewer`;
     * the same line with association `NONE`, `CONTRIBUTOR`,
       `FIRST_TIME_CONTRIBUTOR`, or a missing association (PR-1);
     * the line `…: 101 later`.
2. **Fail-closed cases** each give `parse_ok False`:
   * a non-string body;
   * a body-finding review without an integer `databaseId`;
   * a missing `comments` connection;
   * a comment with a null author.
3. **Review-state scope:**
   * a `DISMISSED` Copilot review with body findings is not counted;
   * a `COMMENTED` review on a stale HEAD with body findings **is** counted
     (D3, all rounds).

**Functions touched:** `parse_graphql_response` and 1 new private helper,
`_parse_disposition_ids`.

**Posture:** test-first. Update the builders first and confirm the existing
suite is green, then add the new tests.

**Size / complexity:** M / medium.

**Depends on:** U1.

### U3: Verdict, classify ordering, and result payload (code + tests)

**Files (2):**

* `src/autoharness/gates/copilot_review.py`
* `tests/test_gates_copilot_review.py`

**Changes:**

* Add `Verdict.UNDISPOSITIONED_BODY_FINDINGS = "UNDISPOSITIONED_BODY_FINDINGS"`
  and a `_VERDICT_MESSAGES` entry. The message says that a Copilot review body
  carries findings with no review thread, and it gives the BLOCK remediation:
  * fix the finding, or capture it (P-021 C2), or decline it with a rationale;
  * then post a PR comment quoting the findings, with the line
    `Copilot-Review-Body-Disposition: <review id>`.
* `PASS_VERDICTS` is unchanged.
* `classify()` checks run in this order. Only the last check is new.
  1. disabled
  2. verify_failed
  3. parse
  4. engagement
  5. completed_for_head (WAITING / TIMEOUT)
  6. `UNRESOLVED_THREADS`
  7. **new:** if `state.undispositioned_body_finding_review_ids` is non-empty,
     return `DETECTION_AMBIGUOUS` when `not state.comments_complete` (D5: the
     marker could be on an unfetched page), else return
     `UNDISPOSITIONED_BODY_FINDINGS`
  8. `SATISFIED`
* `CopilotReviewResult` adds:
  * `undispositioned_body_finding_review_ids: tuple[int, ...] = ()`;
  * `advisory: tuple[str, ...] = ()`.
* `to_dict()` emits both keys.
* Every `CopilotReviewResult(...)` construction in `evaluate()` that carries
  state also passes the undispositioned IDs.
* The OQ-1 advisory: when any Copilot review body had
  `overview_version not in (None, KNOWN_OVERVIEW_VERSION)`, add
  `"unrecognized ccr-overview version v<N>: review-body detection may be incomplete; read review bodies manually"`
  to `advisory`. The verdict is unaffected.
  * The advisory reads `ReviewRecord.overview_version`, which U2 sets. U3 adds
    no parse code (PR-2).

**Tests (3 scenario groups):**

1. **Verdict and ordering:**
   * threads resolved with undispositioned body findings gives
     `UNDISPOSITIONED_BODY_FINDINGS`, `blocked`, and exit 1;
   * unresolved threads with body findings gives `UNRESOLVED_THREADS`;
   * a `REVIEW_TIMEOUT` state with body findings stays `REVIEW_TIMEOUT` (I7).
2. **Truncation:**
   * an undispositioned list with `comments_complete=False` gives
     `DETECTION_AMBIGUOUS`;
   * an empty list with `comments_complete=False` gives `SATISFIED`.
3. **Verdict set and payload:**
   * update `test_only_satisfied_and_na_pass` and
     `test_all_block_verdicts_exit_nonzero` to include the new verdict;
   * add the parameterized every-member check (Plan Hardening);
   * `to_dict()` round-trips through `json.dumps` with the two new keys;
   * an overview-v3 review yields a non-empty `advisory`.

**Functions touched:** `classify`, `evaluate`, and the `CopilotReviewResult`
dataclass.

**Posture:** test-first.

**Size / complexity:** S / medium.

**Depends on:** U2.

### U4: CLI human-readable rendering (code + tests)

**Files (2):**

* `src/autoharness/cli.py`
* `tests/test_gate_copilot_review_cli.py`

**Changes:** in `_gate_copilot_review_command`'s non-JSON branch, after the
unresolved-thread line, add:

* when `result.undispositioned_body_finding_review_ids` is non-empty, print
  `  undispositioned Copilot review-body findings in reviews: <comma-separated ids>`;
* print the hint
  `  post a PR comment containing 'Copilot-Review-Body-Disposition: <id>' after handling each finding`;
* print each `result.advisory` entry prefixed with `  advisory: `.

The `--json` path already emits the new keys through `to_dict()`. The `--force`
audit is unchanged.

**Tests (2 scenarios):**

1. The human output for an injected `UNDISPOSITIONED_BODY_FINDINGS` result
   contains the ID line and the hint, and the exit code is 1.
2. The `--json` output contains `undispositioned_body_finding_review_ids` and
   `advisory`.

Reuse the existing CLI test pattern for patching `copilot_review.evaluate`.

**Functions touched:** 1.

**Posture:** test-first.

**Size / complexity:** XS / low.

**Depends on:** U3.

### U5: Gate reference doc and CHANGELOG (docs)

**Files (2):**

* `docs/copilot-review-gate.md`
* `CHANGELOG.md`

**Changes in `docs/copilot-review-gate.md`:**

* Overview and P-018 summary: the third condition (every threadless review-body
  finding is dispositioned).
* Query paragraph: `databaseId`, `body`, and the PR `comments(last:100)`.
* Verdict table: the new row (BLOCK, exit 1).
* A new `### Review-Body Findings` subsection with:
  * the detector rules (`max(S, PM) + U` and what is not counted);
  * the review scope (all completed Copilot reviews, in any round);
  * the disposition marker contract (exact literal, its own line, non-Copilot
    author with `authorAssociation` OWNER, MEMBER, or COLLABORATOR, one line
    per review, several lines per comment allowed). State the trust rationale
    (PR-1);
  * the fail-closed rules, including truncated comments;
  * the known limitation (a format drift can cause a miss, and the instruction
    layer backstops it);
  * the `advisory` field (OQ-1);
  * a rollout note (OQ-2): open PRs that already handled body findings must
    post marker comments before the gate passes.

**Changes in `CHANGELOG.md`:** under `## Unreleased`, add a `### Changed` entry
or a `### Fixed` entry if that heading exists, citing 38D29192.

**Tests:** none new. U9 pins the doc.

**Functions touched:** 0.

**Posture:** test-after-edit.

**Size / complexity:** S / low.

**Depends on:** U3.

### U6: PR-automation instruction, body-aware loop (template + mirror + manifest checksum)

**Files (3, the rendered-surface triple):**

* `templates/instructions/github-pr-automation.instructions.md.tmpl`
* `.github/instructions/github-pr-automation.instructions.md`
* the mirror entry's `checksum` and `note` in `.autoharness/harness-manifest.yaml`

**Changes (semantically identical in template and mirror).** Apply them at the
corresponding sections. Pre-existing template/mirror drift is **not**
reconciled. The mirror renders `{{REPO_OWNER}}` and `{{REPO_NAME}}` as
`softwaresalt` and `autoharness`, following its existing text.

* **§1.2:**
  * After "Inspect the returned reviews and review comments", add: read every
    Copilot review's **`body`** each round, not only its comments and threads.
  * State that a `0 open findings` headline or zero inline comments does not
    mean clean.
* **§1.3:**
  * Add a paragraph defining review-body findings: items under
    `Previously missed (N)`, `Suppressed comments (N)`, or open findings with no
    `#discussion_r` link. Classify them with the same table.
  * The overview risk line (for example "Needs a closer look") is a risk note,
    not a finding.
  * `resolved since last review` items are not findings.
* **New §1.6.1 "Threadless Review-Body Findings":**
  * There is nothing to reply to or resolve.
  * Fix the finding and push, or run the P-021 C2 capture first for an
    out-of-scope finding, or decline it with a rationale.
  * Then post **one PR comment per Copilot review** that carries body findings.
    The comment quotes each finding with its disposition (`fixed in <sha>`,
    `deferred to stash <id>`, or `declined: <rationale>`) and contains the
    exact line `Copilot-Review-Body-Disposition: <review databaseId>`.
  * Tell agents where to find the review ID (PR-7). It is the GraphQL
    `databaseId`, which equals the REST review `id` returned by
    `mcp_github_pull_request_read` and the number in
    `#pullrequestreview-<id>` URLs.
  * The comment must be posted from the operator's repository account. The
    gate honours only `OWNER`, `MEMBER`, and `COLLABORATOR` authors.
  * A review whose findings were all fixed by later pushes still needs its
    marker.
  * Use the existing Shell-Safe Comment Body Construction rules (§1.5).
  * Post the comment only after the fixing push, as §1.4 step 6 requires.
* **§1.7:** a round is clean only when the current-HEAD review has no open
  Copilot threads **and** every Copilot review with body findings has been
  dispositioned. Each fix push re-arms Copilot.
* **§1.8:**
  * A body finding fixed by a push counts as a review-fix cycle.
  * An in-scope body finding left unhandled at the cycle limit follows the
    existing P-021 C3/C4 halt.
  * With Copilot enabled, undispositioned body findings BLOCK the merge
    (`UNDISPOSITIONED_BODY_FINDINGS`), alongside the existing
    `UNRESOLVED_THREADS` sentence.
* **§1.9.1:** the readiness query's `reviews` nodes add `databaseId` and `body`.
* **§1.9.2:** the readiness block template adds the line
  `- Review-body findings: \`none\` | \`<review id>: <n> — <disposition summary>\``.
  The follow-up text requires every body finding to be listed per round.
* **§1.9.4 Check 5:** add `UNDISPOSITIONED_BODY_FINDINGS` to the BLOCK list,
  with its remediation (handle the finding, then post the disposition comment,
  then re-run). Update the "SATISFIED" bullet to add "and every Copilot
  review-body finding dispositioned".
* **§1.9.5:** the existing P-018 row's condition adds "or Copilot review-body
  findings undispositioned".
* **Manifest:** Ship refreshes the mirror checksum from the LF-normalized
  staged blob (`git cat-file blob :<path>`) and appends a dated note clause
  (`38D29192/<task-id>: review-body findings handling`), following the entry's
  convention.

**Tests:** the existing checksum-coherence tests. U9 pins the content.

**Functions touched:** 0.

**Posture:** test-after-edit.

**Size / complexity:** M / medium.

**Depends on:** U3 (verdict name and marker literal are fixed).

**Residual:** three files is the accepted triple.

### U7: P-018 policy text (template + mirror + manifest checksum)

**Files (3):**

* `templates/policies/workflow-policies.md.tmpl`
* `.github/policies/workflow-policies.md`
* the mirror's manifest entry

**Changes in the P-018 section:**

* The statement adds condition (3): every threadless finding in a completed
  Copilot review body is dispositioned by a PR comment carrying
  `Copilot-Review-Body-Disposition: <review id>`. The comment must come from a
  repository OWNER, MEMBER, or COLLABORATOR.
* Add a bullet "Review-body findings (threadless)" with a one-paragraph
  summary.
* The Postcondition BLOCK verdict list adds `UNDISPOSITIONED_BODY_FINDINGS`.
* Template and mirror get byte-identical inserts.
* Manifest checksum refresh and note, as in U6.

**Tests:** the existing policy contract and checksum tests.
`tests/test_scope_containment_policy_contract.py` reads this file, so it must
stay green.

**Functions touched:** 0.

**Posture:** test-after-edit.

**Size / complexity:** XS / low.

**Depends on:** U3.

### U8: Ship 7c gate step (template + mirror + manifest checksum)

**Files (3):**

* `templates/agents/_ship.agent.md.tmpl`
* `.github/agents/_ship.agent.md`
* the mirror's manifest entry

**Changes in step 7c:**

* The `SATISFIED` bullet adds "and every Copilot review-body finding
  dispositioned".
* The BLOCK verdict list adds `UNDISPOSITIONED_BODY_FINDINGS`, with the
  remediation "handle each finding per §1.6.1, post the disposition comment,
  re-run".
* Template and mirror get byte-identical inserts. The mirror's frontmatter and
  model-routing lines are untouched.
* Manifest checksum refresh and note, as in U6.

**Tests:** the existing Ship parity and checksum tests stay green. U9 pins the
content.

**Functions touched:** 0.

**Posture:** test-after-edit.

**Size / complexity:** XS / low.

**Depends on:** U3.

### U9: Cross-surface contract pin (tests)

**Files (1):** `tests/test_copilot_review_body_findings_contract.py` (new).

**Changes.** Import `Verdict`, `DISPOSITION_MARKER`, and `PASS_VERDICTS` from
`autoharness.gates.copilot_review`. Assertions run on whitespace-collapsed text.

**Tests (3 scenarios):**

1. `Verdict.UNDISPOSITIONED_BODY_FINDINGS.value` and `DISPOSITION_MARKER`
   appear in each of the 7 surfaces: U6 template and mirror, U7 template and
   mirror, U8 template and mirror, and `docs/copilot-review-gate.md`.
2. The new verdict is not in `PASS_VERDICTS`, and its value appears in each
   surface's BLOCK verdict enumeration. The check is a same-line or
   same-paragraph co-occurrence with `UNRESOLVED_THREADS`.
3. The instruction template and mirror both contain the `1.6.1` heading text
   `Threadless Review-Body Findings` and the readiness token
   `Review-body findings:`.

**Functions touched:** 0 production; 3 test methods.

**Posture:** test-after-edit.

**Size / complexity:** S / low.

**Depends on:** U5, U6, U7, U8.

## Dependency Graph

```text
U1 ── U2 ── U3 ─┬── U4
                ├── U5 ──┐
                ├── U6 ──┤
                ├── U7 ──┼── U9
                └── U8 ──┘
```

The graph has no cycles. Manifest order: feature, U1, U2, U3, U4, U5, U6, U7,
U8, U9.

## Decisions and Rationale

* **One module, not a new sibling module.** The gate's docstring requires
  standard-library-only code and no reach into other gate modules. A private
  sibling would be legal but would split one gate's contract across files. The
  detector is about 60 lines.
* **Defaulted dataclass fields.** Existing `ReviewRecord` and `ReviewState`
  constructors and tests stay valid. Only the GraphQL fixture builders change.
* **Truncated comments are ambiguous only when they matter.** A PR with more
  than 100 conversation comments and no body findings must not be wedged.
  `reviews(last:100)` truncation stays ambiguous, as today.
* **Per-review markers, not per-finding markers.** Per-finding identity would
  couple the gate to the proprietary item format. The instruction contract
  carries the per-finding content (deliberation, Rejected Alternatives).
* **`DISPOSITION_MARKER` is a code constant.** U9 derives its pins from it, so
  the code, docs, policy, and agent cannot drift (precedent:
  `_RANGE_TOKEN` in 192.026-T).

## Risks and Caveats

* Format drift (OQ-1): mitigated by the instruction backstop and the advisory
  field.
* False BLOCK: fail-closed by design. It is cleared by agent action and needs
  no `--force`.
* Template/mirror drift in `github-pr-automation` already exists, about 146
  differing lines. U6 must apply its edits by section, not by a whole-file
  copy.
* Existing open PRs at rollout (OQ-2): covered by the doc rollout note.
* GraphQL cost: `body` on up to 100 reviews and 100 comments is a modest
  payload, and the request stays one call.

## Plan Hardening Signals (REQUIRED)

| Signal | Present | Justification |
|---|---|---|
| Public API, schema, or contract change | **Yes** | New verdict enum value, new JSON keys, new marker contract, and P-018 policy text. |
| Security, auth, permission, or compliance-sensitive behavior | **Yes** | P-018 is a fail-closed merge gate. The marker is an agent-postable clearance (trust boundary). |
| Migration, backfill, destructive action, or irreversible step | No | No data migration. Open PRs need marker comments (operational, reversible). |
| External integration, operator checkpoint, or external dependency | **Yes** | GitHub GraphQL (new fields) and the Copilot body format, which is unversioned. |
| High runtime, rollout, or rollback risk | Partial | A false BLOCK holds merges. It is clearable without `--force`, and revert is a single PR. |

Requires plan hardening: yes

## Runtime Verification and Closure

* **Runtime surface:** the `autoharness gate copilot-review` CLI (U1 to U4).
* **Runtime verification (Ship, after U4, before PR):** run the installed CLI
  read-only against real PRs:
  * `autoharness gate copilot-review 506 --repo softwaresalt/autoharness --json`
    must return `UNDISPOSITIONED_BODY_FINDINGS`, listing the round 2 to 5 review
    IDs `5450565731`, `5450722020`, `5450864009`, and `5451204580`. Merged
    PR #506 has no marker comments, so this is the regression reproduction.
  * Run the same command against a recent merged PR whose Copilot bodies carry
    no threadless findings. It must return `SATISFIED` (the no-false-block
    check).
  * Record both outputs in the PR's runtime-verification evidence. Do **not**
    post marker comments on historical PRs.
* **Closure:** the operational-closure artifact records the following.
  * **Monitoring:** the first two Ship PRs after merge record the gate verdict
    per round, and any `UNDISPOSITIONED_BODY_FINDINGS`.
  * **Rollback trigger:** a false BLOCK that a marker comment cannot clear, or a
    detector exception.
  * **Rollback:** revert the feature PR.
  * **Owner:** Ship.
  * **Validation window:** the next 2 merged PRs with Copilot engaged.

## Plan Hardening

**Required:** yes. Three signals are present: contract, trust-sensitive gate,
and external format.

**Learnings and instructions consulted:**

* `docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md`
* `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`
* `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md`
* `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`
* `templates/instructions/github-pr-automation.instructions.md.tmpl` §1.2 to §1.9
* `templates/policies/workflow-policies.md.tmpl` P-018
* `templates/agents/_ship.agent.md.tmpl` 7c

### Protected invariants (must hold after every unit)

* **I1:** `PASS_VERDICTS == {SATISFIED, NOT_APPLICABLE}`. The exit codes stay
  0, 1, and 2.
* **I2:** Every malformed or unverifiable input still fails closed. No new
  parse path may yield `SATISFIED` on malformed data. A truncated `comments`
  connection with undispositioned findings is `DETECTION_AMBIGUOUS`.
* **I3:** `build_query_argv` arity and `shell=False` are unchanged. No new
  subprocess. The GraphQL `errors` handling is unchanged.
* **I4:** The module stays standard-library-only, with no imports from other
  gate modules.
* **I5:** `--force` remains operator-only and audited. The new verdict is
  forceable only through the existing audited path. Agents clear it **only**
  through the disposition marker.
* **I6:** Only a trusted comment can clear a disposition:
  * the author is not `COPILOT_LOGIN`;
  * `authorAssociation` is OWNER, MEMBER, or COLLABORATOR.

  This prevents self-clearance by the reviewer bot and clearance by an outside
  commenter (PR-1). Clearance authority matches the write-access requirement
  for resolving a review thread.
* **I7:** The 157-S lesson holds: `REVIEW_TIMEOUT` with empty lists is never
  clean. The new check runs only after `completed_for_head()`.

### ProposedAction / ActionRisk

| ProposedAction | ActionRisk | Approval | Notes |
|---|---|---|---|
| Add a BLOCK verdict to a fail-closed merge gate (U3) | medium | plan review (this gate) | Can hold merges. It is clearable by the agent marker, and revert is a single PR. |
| Extend the GraphQL query and the strict parser (U2) | medium | plan review | Mitigated by I2 and I3. The builder update proves backward compatibility on the existing suite. |
| Define an agent-postable clearance marker (U2, U6) | medium | plan review | Trust parity with thread resolution, as recorded in the deliberation. I6 excludes the bot. |
| Edit policy, agent, and instruction mirrors and manifest checksums (U6 to U8) | low | none | Checksums come from the staged LF blob. U9 pins the content. |

### Added verification

* **U2 backward-compatibility gate:** after the builder update and before the
  new tests, the full existing `test_gates_copilot_review.py` and
  `test_gate_copilot_review_cli.py` must pass.
* **U3:** a parameterized assertion that every `Verdict` member is either in
  `PASS_VERDICTS` or exits 1. This catches a verdict accidentally added to the
  PASS set.
* **Runtime verification:** the PR #506 reproduction and the no-false-block
  check, as described above.

### Rollback and closure

* The rollback is a single-PR revert. No persisted data or schema changes.
* The marker comments posted on PRs are inert after a revert.
* There are no unresolved operator decisions blocking execution. OQ-1 and OQ-2
  are mitigated, not blocking.

### Review-gate capability risk

* Reviewer subagent dispatch is not available in this Stage session.
* Plan review must declare
  `dispatch_mode: single-agent-declared-degradation` and apply every persona
  rubric inline.
* The appended review must carry literal `dispatch_mode:` and `decision:`
  lines.

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

* **Full record:** `docs/reviews/2026-10-08-copilot-review-body-findings-gate-plan-review.md`.
* **Round 1: FAIL.** Findings: 1 P1, 3 P2, 2 P3.
  * PR-1 (P1): untrusted commenters could clear the BLOCK. Fixed with an
    `authorAssociation` filter.
  * PR-2: the parse split across units. Fixed.
  * PR-3: the nested-details span. Fixed.
  * PR-7: the review-ID source. Fixed.
  * Remediation used review-fix cycle 1 of 3.
* **Round 2: PASS.** Only P3 advisories remain:
  * PR-4: U2 may be split by Ship if it exceeds 2 hours;
  * PR-5: the advisory field is accepted;
  * PR-8: an optional pin of the association literals in U9;
  * PR-9: pre-existing template/mirror drift, reported only.
* **Plan hardening:** required and satisfied.
