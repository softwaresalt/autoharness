# Plan Review — Checkpoint payload contract (stash E0B80A6C)

Date: 2026-08-17
Agent: Stage
Plan: `docs/plans/2026-08-17-checkpoint-payload-contract-plan.md`
Hardening: `docs/plans/2026-08-17-checkpoint-payload-contract-hardening.md`
Method: multi-persona adversarial review, six personas
Priority: reliability and safety over speed

## Verdict

**PASS — 0 P0, 0 P1 unresolved.**

Seven findings raised: three P1 and four P2. All three P1s were resolved by
amending the plan and hardening documents in place before this verdict. Two P2s
accepted with mitigation, two P2s deferred with explicit rationale.

## Persona 1 — Recovery / reliability engineer

**F1 (P1, RESOLVED) — New write guidance could flood the recovery scan.**
The dogfood mirrors currently contain no structured checkpoint-write guidance at
all. T4 introduces the capability instruction where none existed. If written
without volume constraints, both agents would begin emitting structured
checkpoints at every milestone and leaving them active, seeding multiple
candidates into the mandatory unfiltered startup scan and forcing operator
selection on every session start. That trades one rare malformed record for
chronic recovery-path noise — a net reliability regression.
*Resolution:* new hardening **H13** requires the inserted guidance to carry the
existing volume constraints (resolve active checkpoints at session end; at most
one final best-effort checkpoint; never leave an active candidate for completed
work), and requires verifying zero active checkpoints after T4.

**F2 (P1, RESOLVED) — Verification step creates a live active checkpoint.**
The plan's manual verification calls `backlogit checkpoint create` against the
live workspace. The created record is an active recovery candidate that would
pollute the pre-138-S scan and contradict the completed-work rule.
*Resolution:* hardening **H3** binds the sequence create → get → resolve →
re-scan for zero active/zero anomalies, HALTs if it cannot be resolved, and
prefers a scratch workspace via `--cwd` so the live workspace is never touched.

## Persona 2 — Template / packaging maintainer

**F3 (P1, RESOLVED) — Checksum artifact list was under-specified and mis-ordered.**
Plan T5 named exactly three artifacts to re-hash, but hardening H6 requires T6 to
also modify the manifest-tracked registry template
`backlog/registries/backlogit.registry.yaml`. With T6 declared "independent" and
T5 fixed at three files, a registry-template byte change would land with a stale
manifest checksum — a silent integrity failure of exactly the kind this shipment
exists to prevent.
*Resolution:* T5 amended to enumerate changed files and hash whatever actually
changed (minimum four candidates), and the dependency graph amended so T6 must
precede T5. T5 is now the single checksum-refresh point for the whole shipment.

**F4 (P2, ACCEPTED with mitigation) — Reinstall could revert the mirror fix.**
The agent mirrors are manifest-labeled `template: "global agent definition"`
rather than a `.tmpl` path, so a future reinstall may overwrite them from the
global definitions.
*Mitigation:* hardening **H7** requires the mirror sentences to be semantically
identical to the template sentences so a reinstall converges rather than
regresses, and requires a HALT if they cannot be reconciled.

## Persona 3 — Test engineer

**F5 (P1, RESOLVED) — Negative assertion was keyword-brittle.**
Asserting the absence of `feature_id`, `mode`, `route`, `artifacts` and similar
tokens across whole documents would produce false failures, because those words
appear legitimately throughout both agent files in unrelated prose. A test that
fails spuriously gets deleted, taking the guard with it.
*Resolution:* hardening **H8** requires the assertions to be anchored to the
contract block and the fenced example, matching instructional patterns rather
than bare substrings.

**F6 (P2, ACCEPTED) — Does the documented example actually round-trip?**
The plan asserts the example is conformant but a structural test only proves
shape, not that backlogit accepts it.
*Mitigation:* the plan's manual verification executes a real
`checkpoint create` → `checkpoint get` cycle against the documented example,
under H3's resolve-and-rescan constraint. Evidence supports the shape
independently: the well-formed peer `checkpoint-20260815-224227.json` carries
exactly `schema_version, agent, session_id, phase, status, created_at,
updated_at, context, resume_hint`, confirming `context` is a real V1 field.

## Persona 4 — Safety / policy auditor

**F7 (P2, ACCEPTED) — Evidence and prior staging artifacts must stay immutable.**
The shipment touches the same workspace that holds the quarantined evidence and
the 129-F/138-S artifacts.
*Mitigation:* hardening **H4** places the quarantined bytes, disposition sidecar,
audit log, prior commits and 129-F/138-S artifacts explicitly out of bounds.
**H10** forbids `git add -A` and `git clean -x/-X`, preserving the multi-megabyte
`.backlogit` db/wal hazard control carried over from the 138-S work.

Role boundary confirmed clean: this session produced only planning artifacts and
backlog records. No template, source, config, or test file was modified by Stage.

## Persona 5 — Ship executor (usability)

**F8 (P2, DEFERRED) — `session_id` format is unspecified.**
The contract requires `session_id` but does not constrain its format. Low risk;
existing records use a readable `role-date-topic` convention that Ship can follow.
Deferred rather than over-specified.

**Environment note accepted:** `uv run` fails here with a TLS handshake failure
fetching `hatchling`. Hardening **H11** directs verification through the installed
interpreter and forbids reporting the `uv` failure as a shipment test failure.

## Persona 6 — Adversarial / chaos

**F9 (P2, DEFERRED) — No detection for already-malformed checkpoints.**
This shipment is purely preventive; a workspace that already contains a malformed
record still depends on a human noticing it during the startup scan.
*Rationale for deferral:* the mandatory unfiltered scan already fails closed on
malformed records, and `checkpoint quarantine` provides a clean, evidence-
preserving remediation — both were exercised successfully today. A
`harness-doctor` scan is a genuine improvement but is detection-after-the-fact and
would widen this shipment's blast radius. Recorded as a follow-up, not scope.

**F10 (P1 → downgraded P2, RESOLVED) — Blocking edge could strand 138-S.**
If this predecessor is later abandoned, 138-S becomes permanently unshippable.
*Resolution:* hardening **H14** allows removal of the dependency only by explicit,
recorded operator decision and forbids Ship from removing it unilaterally to
unblock itself.

## Duplication-budget check

The operator required the fix not duplicate logic. Confirmed: the full normative
rules 1-5 and the fenced example appear exactly **once**, in the backlogit overlay
instruction (plus its rendered mirror, which is a required parity copy, not a
second source). The four agent-template write sites and the two mirror insertions
carry only a one-line non-negotiable minimum plus a pointer to the canonical
section. That minimum is the deliberate duplication budget — it exists so each
write site is actionable in isolation and so the tests can assert per-site
coverage, which is what makes the anti-regression guard meaningful.

## Residual risk

Low. All changes are additive documentation, config and test edits with no runtime
component. Rollback is a `git revert` plus a checksum recompute. The highest
residual risk is F4 (reinstall convergence), mitigated by H7 and bounded by the
fact that the templates — the reinstall source of truth — are themselves corrected
in T2/T3.
