# Ship dark-factory continuation session — shipment 134-S (feature 125-F)

**Date**: 2026-08-15
**Mode**: `DARK_MODE_ACTIVE` bounded dark-factory continuation, ordered scope
`[134-S, 135-S, 136-S]`, this invocation covering `134-S` only. `133-S`
explicitly excluded from scope and never touched, edited, claimed, or shipped
(confirmed at closure: `archived_status: queued`, unchanged).

## Outcome

Shipment `134-S` / feature `125-F` ("Tune target-workspace startup scripts to
the current thin-shim contract") fully shipped end-to-end:

- PR **#340** (`feat/tune-startup-script-contract-migration` → `main`),
  merge commit `afde69344d827d2b883f86f91ad5c842aab72885` (verified 2-parent
  merge commit, P-009 merge-commit-only strategy; `allow_squash_merge`/
  `allow_rebase_merge` both `false` at repo level).
- Reviewed-HEAD progression: `f97380be` (initial) → `dd92a8b2` (Copilot round
  1, 2 findings) → `a4e8273b` (Copilot round 2, 1 finding) → `4bab0d0f`
  (Copilot round 3, 1 finding — final, `SATISFIED`, 0 unresolved threads).
  Used exactly 3 of the 3-cycle Copilot-fix budget for this PR, ending clean.
- Closed via the **P-015 verified fully-covered-root cascade path**
  (`classify_shipment_close_path` confirmed `125-F` is a root feature with
  exactly 3 children, all in the manifest): `backlogit shipment ship`
  returned `returned_ids=[]`, `archived_ids` matched exactly
  `[125.001-T, 125.002-T, 125.003-T, 125-F, 134-S]`, and `parent_id: 125-F`
  was verified preserved on all 3 archived tasks against the pre-close
  snapshot.
- Post-merge closure work committed to `post-merge/tune-startup-script-contract-migration`
  (never directly to `main`), awaiting its own PR + operator approval per the
  Post-Merge Branch Protocol.

## Notable findings fixed during the PR lifecycle (all via Copilot review)

1. Raw substring current-marker matching misclassified disabled/commented
   marker text as `current`.
2. `known-legacy` classification never extracted/preserved a legacy script's
   custom-section tail, risking silent loss of operator customizations on
   refresh.
3. Manifest checksum-drift state wasn't consulted by the classifier, so an
   unattributed core-content edit on a `known-legacy`/`current` script could
   still auto-refresh; fixed by failing closed to `ambiguous`. This
   correctly surfaced this repo's own `start.sh`/`start.ps1` as `ambiguous`
   (pre-existing, intentionally customized dogfood scripts — see compound
   learning `2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`).
4. The custom-section tail (operator-controlled content, may include
   secrets) was carried raw into classification/proposal dicts that get
   `json.dumps()`'d into on-disk verification reports; fixed by replacing it
   with a non-sensitive hash/size summary (see compound learning
   `2026-08-15-never-serialize-raw-operator-content-into-json-reports.md`).

## Process notes for future dark-factory continuations

- The audited `PREDECESSOR_NOT_SHIPPED`/`133-S` topology-gate override token
  had to be re-forced at every phase re-invocation (pre_claim, post_claim,
  every `lifecycle` re-run after each push, and the closure-phase
  re-invocation) — it is never "sticky" across gate calls. No other token was
  ever overridden.
- The `pipeline-topology (ambient)` CI check reproduces the same audited
  token as an advisory (`continue-on-error`) failure and never blocks `ci
  gate`/merge in this repo (no branch protection on `main`, repo variable
  `PIPELINE_TOPOLOGY_GATE_REQUIRED` unset) — expected, not a defect.
- Copilot auto-re-reviews a fresh push within roughly 2–5 minutes once
  already engaged as a PR reviewer, without any explicit re-request call;
  polling per the §1.2 backoff table was sufficient every round this
  session.
- `git checkout <branch>` with an uncommitted dirty closure state (backlog
  archival mutations) requires a `git stash push -u` / branch switch /
  `git stash pop` cycle when the destination branch's tracked version of
  those same files differs from the source branch's working-tree state —
  expected, not an error condition, for the Post-Merge Branch Protocol.

## P-020 compaction status

`compaction_status: degraded` — no installed/executable `compact-context`
tool exists in this environment (only the repository's own authored template
at `templates/skills/compact-context/SKILL.md.tmpl`; this self-hosting repo
does not resolve `.github/skills/compact-context/SKILL.md`), consistent with
the `130-S`/`121-F` closure precedent. This session's own consolidation
(these compound-learning and memory notes) constitutes the manual
lower-bound equivalent of Phase 1–3 of that skill; invocation is recorded as
attempted-and-degraded, non-blocking, per P-020.
