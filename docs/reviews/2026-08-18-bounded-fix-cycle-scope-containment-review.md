# Plan Review — P-021 Bounded Fix-Cycle Scope Containment & Deferred Expansion Capture

| Field | Value |
|---|---|
| Date | 2026-08-18 |
| Plan | `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-plan.md` |
| Hardening | `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-hardening.md` |
| Deliberation | `019-DL` |
| Source stash | `B48A482A` |
| Reviewer | Stage (`claude-opus-5` / `anthropic` / `high`) |
| Cycles | 1 of 3 |
| **Verdict** | **PASS (with findings applied)** |

## Review dimensions

### Correctness of the problem framing — PASS

The plan correctly identifies that the existing circuit breaker bounds the
*count* of review-fix cycles but not the *scope* of a fix within one, so the
current harness genuinely permits the behavior the operator prohibited. The
claim was verified against
`templates/instructions/circuit-breaker.instructions.md.tmpl` §"Review-Fix
Cycle Definition" (lines 212–217) and the Stop Conditions tables in
`_ship.agent.md.tmpl` (line 793), `circuit-breaker.instructions.md.tmpl`
(line 167), `github-pr-automation.instructions.md.tmpl` (line 306), and
`pr-lifecycle/SKILL.md.tmpl` (line 272). None constrains fix scope.

### Surface completeness — PASS

Spot-checked the negative claims that bound the surface map:

* `.github/policies/` does not exist → `workflow-policies.md.tmpl` is
  template-only. Confirmed, and corroborated by
  `docs/archive/plans/2026-07-29-p020-post-merge-compaction-plan.md`.
* `.github/skills/` contains only the four global skills → `pr-lifecycle` and
  `fix-ci` have no dogfood pair. Confirmed.
* The 39-artifact manifest checksum set and the byte-identity contract in
  `tests/test_circuit_breaker_policy_contract.py`. Confirmed.

No additional carrier surface was found that discusses fix-cycle scope and was
omitted. `templates/agents/review/scope-boundary-auditor.agent.md.tmpl` matched
a "scope expansion" grep but governs *review persona* scope auditing of a diff,
not in-cycle authoring authority; correctly excluded.

### Decomposition quality — PASS

Eleven tasks, each a single coherent surface edit plus its atomic dogfood +
checksum unit (H3). No task combines a policy-registry edit with a CLI or schema
edit. Task 007 pairs two skill templates, which is same-family and
template-only; it stays comfortably under the 2-hour rule. The dependency graph
is a shallow tree rooted at 001 with a single join at 011 — no cycles, no
diamond hazards beyond the `_ship.agent.md` serialization that H4 makes
explicit.

### Hardening adequacy — PASS

H1/H2 are the highest-value items: they prevent the P-010 repair from becoming a
blanket authority grant and prevent it from breaking the already-shipped
post-merge source-artifact cleanup. H5's "one authoritative wording, everything
else references" rule is what keeps seven carriers from drifting. H12 catching
the symmetric scope-*contraction* failure mode is a genuine and non-obvious
addition.

### Self-consistency — PASS

The plan applies its own policy to itself: the `HARNESS_ENFORCED_SUMMARY` range
correction (task 010) is an adjacent pre-existing defect, and it is carried only
because the range must mechanically include the new ID — then disclosed
explicitly per H10. The three genuinely out-of-scope ideas (deterministic gate,
backlogit schema field, broader Orchestrator routing) are recorded in
Deliberation §Open Questions and Plan §7 rather than absorbed.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **R1** | **P1** | Plan §6 specifies `python -m unittest discover -s tests` without the `PYTHONPATH=src` prefix. `docs/compound/097-S-canonical-unittest-gate.md` records that the canonical gate is `$env:PYTHONPATH = 'src'; python -m unittest discover -s tests`, and that a repository-root `pytest` invocation wanders into vendored `references/*` and fails on unrelated collection errors. As written, task 011's verification step could be run in a non-canonical form and produce spurious failures. | **APPLIED** — Plan §6 corrected to the canonical invocation with an explicit prohibition on root `pytest`. |
| **R2** | **P1** | The plan has no `CHANGELOG.md` obligation. Every recent policy/contract change in this repository lands a `## Unreleased` entry (e.g. the F02FD596 P-013.6 entry currently at the head of the file). Adding P-021 with no changelog entry would be an incomplete, inconsistent release unit. | **APPLIED** — added as a task-001 acceptance criterion and to Plan §6. |
| **R3** | **P2** | Plan §4's dependency column writes task 011's dependencies as the range "002–010", which is prose rather than an enumerated edge set. H4 requires orderings to be load-bearing, and the backlog must carry discrete edges. | **APPLIED** — the backlog encodes each edge discretely; the plan table is annotated to say so. |
| **R4** | **P2** | Task 002's acceptance criteria say the Forbidden column "keeps triage / prioritization / … in Forbidden", but H2 then requires `remove` to stay Forbidden *except* for the manifest-derived post-merge source-stash retirement. The plan body does not restate this exception, so a reader of the plan alone could implement H1 and break post-merge Step 7. | **ACCEPTED, mitigated** — H2 states it unambiguously and is a mandatory companion artifact carried on the same task; task 011 asserts the post-merge Step 7 language survives. No plan edit needed. |
| **R5** | **P3** | The `DEFERRED SCOPE EXPANSION` marker is a free-text token, so a typo produces an entry Stage's Step 1 precedence rule (H8) will not match. | **ACCEPTED as disclosed residual risk** — the structured-field alternative is explicitly out of scope (Deliberation Q1, Plan §7). Mitigation: the token is specified as a literal greppable string in H7 item 1 and asserted by task 011, so at least the *emitting* surfaces are pinned. |
| **R6** | **P3** | P-021's `Applies To` set will name `ship`, `pr-lifecycle`, `fix-ci`, `stage`, `orchestrator` — broader than any existing single policy. There is a modest risk the policy reads as diffuse. | **ACCEPTED** — the breadth is inherent to the operator direction (it binds both the producer and the consumer of a deferred entry). The clause→carrier matrix in H11 gives it precise structure. |

## Gate assessment

* **P-003 decomposition chain integrity** — every task has a parent feature and
  an explicit dependency set; no orphans. PASS.
* **2-hour rule** — largest task (004, Ship fix-cycle procedure + Stop
  Conditions + dogfood + checksum) is bounded; no task requires original design
  work beyond quoting clauses authored in 001. PASS.
* **Width isolation** — no task spans template + CLI + schema. PASS.
* **P-006 hardening** — required, performed, 13 items, all folded into
  acceptance criteria. PASS.
* **P-010 role boundary** — the plan itself is Stage-authored planning output;
  no source, template, or config file is mutated by Stage. PASS.

## Verdict

**PASS.** Two P1 findings (R1, R2) were applied to the plan in this cycle. R4 is
mitigated by a mandatory companion artifact; R5 and R6 are accepted and
disclosed. The plan, as amended, is approved for harvest.
