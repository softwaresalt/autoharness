---
title: "Stage session — attempt-01 remediation for 188-S and 187-S"
date: "2026-09-20"
agent: stage
---

# Stage session — attempt-01 remediation for 188-S and 187-S

Date: 2026-09-20
Branch: `chore/stage-176-s-workflow-defects`
Base HEAD at session start: `018d3020`
Mode: remediation only (not review). Engram circuit-open (not retried); intercom
unavailable/local-only.

## Scope

Clear all attempt-01 plan-review findings for two units, rewrite mutable
artifacts coherently, advance both mutable verdict manifests to manifest
revision 2 awaiting independent attempt 02, and commit without pushing.

* `188-S` harness-architect bootstrap plan — findings B1 (P1), B2 (P2), B3 (P3)
* `187-S` Ship pre-task harness lifecycle plan — findings S1–S3 (P1), S4–S6 (P2)

Stage closed nothing. Every finding is recorded as
`ADDRESSED-PENDING-REVIEW`; the verdict field on both manifests is `null`.

## What each fix actually was

**B1 — the claim deadlock.** The four existing one-time bounds (Scope, Count,
Time, Authority) all governed *executing* the harness-architect procedure. They
never reached P-002, whose Precondition and Enforcement filter Ship's ready
queue to tasks carrying `harness-ready` — a label whose only declared producer
is the actor `188-S` installs. So the bootstrap deadlock reproduced one level
down, at claim time. Fix: a **fifth, separately stated Claim bound** naming
exactly `182.001-T` and `182.002-T`, admission-only, non-inheritable, expiring
with the other four on `182.004-T`'s `HARNESS_ARCHITECT_INSTALLED` token.
`182.003-T` and `182.004-T` are explicitly excluded — they receive the ordinary
label from `182.002-T`'s Step 6. Deliberately kept separate from the Count axis:
Count governs *running the procedure once*; Claim governs *being admitted to the
queue*. Framed as not-a-waiver because neither carved-out task implements
anything, so P-002's Statement is not relaxed for any implementing task. No
bootstrap grant, no `--force`, no undocumented waiver, no policy-text edit.

**B2 — `UNIMPLEMENTED_MARKER`.** It is absent from `.autoharness/` entirely; the
attempt-01 finding was right that the plan pointed at an imaginary direct config
field. Authoritative derivation:
`.github/skills/install-harness/SKILL.md:335` defines it as derived from
`languages.primary`, read from `.autoharness/workspace-profile.yaml`
(`python` here → `raise NotImplementedError`). The other four variables are
genuinely stored in `.autoharness/harness-manifest.yaml` under `variables_used`.
Added an explicit fail-closed rule covering missing profile, absent/empty
`languages.primary`, and no derivation row for the language.

**B3 — placeholder coverage.** Decisive evidence found during the sweep:
`{SUFFIX_FEATURE}` / `{SUFFIX_TASK}` are **not** retained exemplars of the
`{YYYY-MM-DD}` kind. They are defined, bound harness variables
(`install-harness/SKILL.md:262,264`, from `config.backlog.suffix_map`, here
`F`/`T`), and every other carrier in the repo spells them double-brace. Only
`templates/skills/harness-architect/SKILL.md.tmpl:4` uses single-brace. That
reframed B3 from "justify retention" to "the assertion must cover them". So
`182.001-T`'s assertion gained an explicit fifth limb for the single-brace
tokens (stated separately, because a `{{...}}` check cannot match them), and
`182.003-T` binds both from `suffix_map` at generation time. **Deliberately did
not** edit the template — that would have been a product-surface change outside
`188-S`'s one-file deliverable, and the halt-by-construction risk (asserting
absence of a token the renderer never rewrites) is avoided by binding rather
than by template edit. Template-side cleanup carried to the stash as
`01191E1B`. Because the fix is mechanical, closure is left pending independent
review.

**S1 — `187-S` no longer touches the actor.** Rollout, Blast radius, Rollback
and hardening H1 rewritten. VERIFY (`181.004-T`) now exercises the resolver
against a **fixture template in a scratch root** and never writes under
`.github/skills/`. ACTIVATE limited to two Ship surfaces. Rollback carries an
explicit "must not touch `.github/skills/harness-architect/SKILL.md`" clause
(new hardening H7). New H8 covers propagation.

**S2 — `181.002-T`** rewritten as the harness-surface requirement resolver
assigned by the revised plan; states outright that it generates no skill and
installs no skill, and consumes `188-S`'s actor read-only.

**S3 — forbidden P-004 policy edit removed** from `181.005-T` (title and body);
ACTIVATE may change only the two authorized Ship integration surfaces; the stale
actor-existence sentence replaced with "the actor already exists when this task
runs".

**S4/S5/S6** — four stale titles corrected, decision citations moved to
revision 3 / D9, both manifests given `manifest_revision: 2`, `verdict: null`
and `disposition: REMEDIATED-PENDING-REVIEW` (disposition field, never the
verdict field), `awaiting_attempt: 2`.

## Judgement calls the operator should confirm

1. **"Advance both mutable manifests to revision 2"** read as the *manifest's
   own* revision — added an explicit `manifest_revision: 2` to both — while
   `plan_revision` follows each unit's review-authorized numbering (`188-S` → 2
   per `authorized-for-revision-2`; `187-S` → 3 per `authorized-for-revision-3`).
2. **Decision bumped to revision 3** to carry the claim bound. Records cite the
   decision revision that created their content, so no mass re-citation was
   needed; archived `181-S` / `184-S` keep "revision 2, D9" and were deliberately
   not touched, preserving their conditional withholding.
3. **Finding counts set to `null`, not `0`** on both manifests. Counts are
   reviewer observations and no reviewer has seen the new revisions;
   attempt-01's real counts remain in the roster. Avoids any appearance of Stage
   decrementing its own findings.
4. **Three coherence fixes beyond the finding list**, all consequences of S1/B1:
   "Four edges' worth of ordering" → "Three edges" in the `188-S` plan; `181-F`'s
   opening mission sentence rewritten off the actor-install framing; the
   lifecycle plan's "this unit supplies the actor that runs it" and
   "`HARNESS_READY` is reachable today … has a complete template" sentences
   rewritten to point at `188-S` as the installer.

## Verification performed

`git diff --check` clean; YAML frontmatter parses on all 15 changed markdown
files; frontmatter diff confirms **only** the four S4 title lines changed — all
sizing (`custom_fields.size` / `complexity`), labels, `parent_id`, `priority`,
`status`, `items` and `dependencies` byte-identical to HEAD; both shipment item
lists unchanged; `188-S` still `dag-root` with zero dependencies; exactly seven
D9 edges (`184-S`, `185-S`, `186-S`, `187-S`, `176-S`, `178-S`, `180-S`) intact;
claim carve-out present and consistent on all six required surfaces with names,
expiry token, non-inheritance and the two exclusions; no append-log headings; no
unresolved `{{...}}` leakage (12 occurrences, all code-quoted subject matter);
all cross-references resolve except `.github/skills/harness-architect/SKILL.md`,
which is intentionally absent — it is the RED precondition and `188-S`'s
deliverable; immutable attempt-01 reviews and all protected
`.github/` / `templates/` / `src/` / `schemas/` files unmodified.

## Next step

Independent plan-review attempt 02 of both units. Stage must not run it.
