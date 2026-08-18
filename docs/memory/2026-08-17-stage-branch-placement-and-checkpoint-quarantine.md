# Stage — 138-S branch placement correction and malformed checkpoint quarantine

Date: 2026-08-17
Agent: Stage
Route: claude-opus-5 / anthropic / high
Mode: normal sequential (not P-017 dark mode)
Scope: narrow, operator-directed corrective action. No migration executed, no
shipment claimed, no source/config edited, no build, no PR.

## Why this session existed

Two operator-identified defects from the prior BED0DDED staging session:

1. The three Stage commits for 129-F / 138-S were left on local `main` instead
   of a dedicated branch, contrary to standard protocol.
2. The mandatory unfiltered checkpoint scan surfaced a malformed Stage
   checkpoint, `checkpoint-20260817-234318.json`, that failed CheckpointV1
   validation and carried a stale pre-remediation `resume_hint`.

## 1. Branch placement correction (lossless, ref-only)

Pre-state: exactly one worktree; clean tree; `main` = `22dc3154`, three commits
ahead of `origin/main` = `6fc2861f`.

Actions:

* `git checkout -b chore/stage-138-S` at `22dc3154` (no collision; neither a
  local nor remote branch of that name existed).
* `git branch -f main origin/main` while checked out on the staging branch.

Deliberately NOT used: `git reset --hard`, file discards, new worktrees. The
correction was purely a ref move, so no working-tree content was touched.

Post-state (verified):

* `chore/stage-138-S` HEAD = `22dc3154b34d6914f2cc9860d58bad322d7cfe9c`
* local `main` = `origin/main` = `6fc2861f34f77855c59e69a413bcfa6cb7058c39` (exact match)
* `rev-list --left-right --count origin/main...chore/stage-138-S` = `0 3`
* `merge-base --is-ancestor` confirms `f801bc6c`, `b33c7e4d`, `22dc3154` all
  remain reachable from the staging branch
* working tree clean, still exactly one worktree

## 2. Malformed checkpoint — quarantine

Target: `.backlogit/checkpoints/checkpoint-20260817-234318.json` (1939 bytes),
`agent=stage`, `phase=complete`, `status=resolved`, `feature_id=129-F`,
`shipment_id=138-S`.

`checkpoint get` failed with three validation errors:

* `CheckpointV1.SchemaVersion` failed the `eq` tag (field absent)
* `CheckpointV1.CreatedAt` failed the `required` tag
* `CheckpointV1.UpdatedAt` failed the `required` tag

Fixed through the supported lifecycle verb only — no JSON hand-editing, no
deletion:

```
backlogit checkpoint quarantine checkpoint-20260817-234318.json --reason "<bounded reason>"
```

`quarantine` is the correct verb by design: it operates ONLY on malformed /
schema-invalid checkpoints and refuses cleanly-validating files (those route to
`abandon`). It moves the bytes verbatim into the workspace archive.

Evidence preserved:

* `.backlogit/archive/checkpoints/checkpoint-20260817-234318.json` — 1939 bytes,
  byte-identical to the original
* `.backlogit/archive/checkpoints/checkpoint-20260817-234318.json.disposition.json`
  — disposition, reason, operator, `disposition_at=2026-08-18T00:21:08Z`
* `.backlogit/logs/checkpoint-disposition-audit.jsonl` — appended
  `checkpoint_disposition` event with `verb: quarantine`

## 3. Post-fix verification (unfiltered, no status filter)

| Measure | Before | After |
|---|---|---|
| Listed checkpoints | 33 | 32 |
| Active | 0 | 0 |
| Resolved | 31 | 30 |
| Abandoned | 2 | 2 |
| Validation/quarantine anomalies | 1 | **0** |

The quarantine cleared the anomaly and produced no new malformed record, so the
circuit breaker was not triggered and no hand-editing was needed. Zero active
checkpoints means there is no recovery candidate outstanding.

(Two additional on-disk files, `checkpoint-20260725-233536.json` and
`checkpoint-20260726-005804.json`, are not returned by `list`; both carry
`schema_version: 1` and valid timestamps, so neither is an anomaly.)

## 4. Cause assessment

**The malformed record is a single occurrence; the causal gap behind it is
latent and reproducible.**

Evidence, all pre-existing — nothing invented:

* 34 of 35 on-disk checkpoints declare `schema_version: 1` with valid
  `created_at` / `updated_at`. Exactly one lacked all three.
* A well-formed peer (`checkpoint-20260815-224227.json`, same Stage agent) has
  keys `schema_version, agent, session_id, phase, status, created_at,
  updated_at, context, resume_hint` — domain data nested under `context`.
* The malformed record has keys `agent, session_id, phase, status, feature_id,
  shipment_id, stash_source, mode, route, resume_hint, artifacts` — no
  `schema_version`, and domain fields hoisted to top level.
* `backlogit checkpoint create --help`: "When the dump declares
  `schema_version=1`, it is validated as a V1 checkpoint and missing
  `created_at`, `updated_at`, and `status` fields are auto-populated."
  Auto-population is therefore **conditional on `schema_version`**; a dump
  omitting it bypasses V1 validation and is written through unvalidated.
* `templates/agents/_stage.agent.md.tmpl:773` (and the identical
  `templates/agents/_ship.agent.md.tmpl:956`) tell the agent to persist a
  "phase-tagged structured checkpoint" and enumerate exactly: phase, stash or
  feature IDs, created artifact IDs, next step, `resume_hint`. They never
  require `schema_version: 1` and never direct nesting under `context`.

The malformed record's shape matches that template enumeration precisely. So
this was not a backlogit checkpoint-generator defect — the supported path
produced 34 valid records — but an instruction gap that lets a conforming agent
emit a schema-invalid checkpoint.

Because a repository template defect **is** evidenced, it was recorded as a
bounded Stage-owned stash bug rather than fixed in place: **stash `E0B80A6C`**
(kind `bug`, priority `medium`). No source, template, or config file was edited
in this session.

## 5. Replacement checkpoint — deliberately not created

Not warranted, on two independent grounds:

* Audit continuity is already materially preserved by the byte-identical
  quarantined record plus its disposition sidecar and the append-only audit log.
* The underlying work is complete (`phase=complete`). `checkpoint create`
  auto-populates status, and manufacturing a checkpoint for finished work risks
  presenting an active recovery candidate — explicitly forbidden.

Quarantine is therefore the canonical fix here.

## 6. State at session end

* Shipment **138-S**: `queued`, unclaimed, untouched — 10 items (129-F plus
  129.001-T..129.009-T), 7×S + 2×XS, 0 unsized, priority high, covering feature
  129-F. Ship still owns execution.
* Staging branch `chore/stage-138-S` holds all four Stage commits; `main`
  matches `origin/main` exactly.
* Branch is **not published**; no PR opened. Ship owns the staging-artifact
  publication gate.

## Next steps for Ship

1. Publish `chore/stage-138-S` and open the PR for 129-F / 138-S.
2. Honour the handoff constraints in
   `docs/plans/2026-08-17-backlogit-self-migration-hardening.md` (H1–H16),
   noting H4/H16 were corrected by `22dc3154` — the backup is contained inside
   the working directory, and rollback is preserve → evidence → HALT →
   operator approval.
3. Treat the now-quarantined checkpoint as non-resumable; recovery state for
   this work is this memory file, not a checkpoint.
