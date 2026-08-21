---
title: "115-S / 109-F: git-blob checksum computation, post-merge branch topology gap, and backlog bookkeeping hygiene"
shipment: 115-S
feature: 109-F
pr: 300
merge_commit: 04cdea11036119522a3c50c37ed5d8787420b4e0
source: docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md
doc_type: learning
---

# Compound Learning: 115-S / 109-F (Pipeline-Topology Gate B — hooks + install adapters)

## 1. PowerShell CRLF-remangling breaks manifest checksum computation

**Symptom**: `tests/test_telemetry_ship_lifecycle.py::test_manifest_tracks_dogfood_ship_agent_checksum`
(and equivalent manifest-checksum tests) failed intermittently after editing
`.github/agents/_ship.agent.md`, `install-harness/SKILL.md`, and
`tune-harness/SKILL.md`, even though the files "looked" unchanged in the
editor.

**Root cause**: PowerShell's native pipe/redirect machinery (`Out-File`,
`>`, and even direct console capture of `git cat-file -p <path>` output)
RE-MANGLES line endings to CRLF on Windows — even when the underlying git
blob is LF. A checksum computed by reading the working-tree file directly
(if the working tree itself was checked out with CRLF, e.g. no
`.gitattributes eol=lf` pin, or `core.autocrlf` conversion) will not match a
checksum computed from the actual LF git-blob bytes that get committed and
that CI (Linux runners) will see.

**Reliable pattern** (either works; both were used this session):

* **(a) Direct subprocess capture** — never pipe through a PowerShell
  redirect operator:
  ```python
  import subprocess, hashlib
  result = subprocess.run(["git", "cat-file", "-p", f"HEAD:{path}"], capture_output=True)
  digest = hashlib.sha256(result.stdout).hexdigest()
  ```
  Hash `.stdout` directly — never re-decode/re-encode/re-print through a
  shell redirect first.
* **(b) Renormalize + stage read** — apply `.gitattributes` rules to the
  index, then read the staged (not working-tree) bytes. **Correction**: an
  earlier draft of this note suggested `git cat-file -p :<path> > $tmp`
  (PowerShell `>` redirect) to capture the staged blob before hashing —
  this repeats the EXACT failure mode described above: PowerShell's `>`
  handles native subprocess stdout as text on affected versions/encodings,
  so `$tmp` can itself end up with remangled line endings, producing the
  wrong digest. There is no safe redirect-based variant of this pattern.
  Always capture the staged blob as raw bytes through a subprocess call,
  exactly like variant (a), just with a colon-prefixed (`:<path>`, index/
  stage-0) ref instead of `HEAD:<path>`:
  ```python
  import subprocess, hashlib
  subprocess.run(["git", "add", "--renormalize", path], check=True)
  result = subprocess.run(["git", "cat-file", "-p", f":{path}"], capture_output=True)
  digest = hashlib.sha256(result.stdout).hexdigest()
  ```
  This captures what will actually be committed, which matters when a
  `.gitattributes eol=lf` pin was *just* added in the same change
  (renormalize is what actually rewrites the index entry to LF).

**Rule going forward**: any manifest-checksummed file edited on a Windows
dev box MUST have its checksum computed via (a) or (b) above — both of
which route through a subprocess capture of raw `.stdout` bytes, never a
shell redirect (`>`, `Out-File`, or piping through a PowerShell console) at
any stage of the pipeline. Add an `eol=lf` `.gitattributes` pin for any
text file whose checksum is tracked in
`.autoharness/harness-manifest.yaml`, to make future edits on Windows
checkouts immune to this class of drift entirely.

## 2. Post-merge closure branches are feature-scoped, not shipment-scoped — topology gate's branch-ownership check didn't know that

**Symptom**: 8 of 10 Copilot review threads on PR #300 converged on the same
root cause: `_branch_ownership_check` in `src/autoharness/gates/topology.py`
only recognized the default branch or an exact `feat/{slug}`/`chore/{slug}`
alias of the **shipment id or title**. But the mandatory post-merge closure
branch (Ship's own Post-Merge Branch Protocol) is named
`post-merge/{feature_slug}` — after the **covering feature**, since a single
feature can span multiple serial shipments (114-S/115-S/116-S all share
`109-F`) and the closure branch is conceptually "closing out this feature's
latest merged slice," not scoped to one shipment id. This would have
deterministically blocked: Ship's own `TOPOLOGY_GATE: lifecycle` call during
closure, any ambient pre-commit/pre-push hook running during closure work,
and the Orchestrator's `pre_claim` eligibility check for the next shipment
in the chain.

**Why this wasn't caught by the deterministic core's own tests**: the
`ShipmentState` model has no feature-level field (no `parent_id` or feature
reference) at the gate's abstraction level, so exact alias matching for a
feature-derived branch name isn't mechanically computable from a
`shipment_id` alone — the gap was structural, not a simple oversight in an
existing check.

**Fix**: added a `_POST_MERGE_BRANCH_PREFIX = "post-merge/"` constant and a
new branch-ownership case (checked right after the default-branch pass,
before exact-alias matching) that treats **any** `post-merge/*` current
branch as ownership-eligible, returning a new token
`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`. This is deliberately coarse (any
post-merge branch passes for any target shipment) rather than trying to
derive and match the exact feature slug, because:

* Branch ownership was only ever a secondary belt-and-suspenders check.
  The **primary** invariant — exactly one active shipment matching the
  target (`post_claim`/`lifecycle`) or zero active
  (`pre_claim`) — is a separate, still-fully-enforced check that this fix
  does not touch or weaken.
* The gate has no reliable, already-available feature-slug string to
  compare against inside `_branch_ownership_check`'s current signature.

**Generalization**: any topology/ownership check keyed on a naming
convention derived from a DIFFERENT id than the check's own primary key
(shipment-keyed check, feature-keyed branch) is a latent gap. When adding a
new lifecycle phase or closure convention, explicitly ask "what id is this
branch/artifact actually named after, and does every consuming check know
that?"

## 3. A task's code can be fully merged while its backlogit record is still `active` — always verify actual status, not just "work landed"

**Symptom**: during this shipment's own safe-close pre-flight, task
`109.013-T` was found still `status: active` in `.backlogit/queue/`, even
though its full implementation (`adc24c9`,
"feat(install): opt-in pipeline-topology hook install/tune wiring +
verify_workspace assertion (109.013-T)") was already merged to `main` days
earlier in this same session's commit history, and a later bookkeeping
commit (`ce53172`, "chore(backlogit): sync task/shipment state through
109.013-T") had moved several *other* sibling tasks from `queued`→`active`
in the same pass but never advanced `109.013-T` itself past `active` to
`done`.

**Root cause**: a backlog-bookkeeping commit's own message ("sync ... through
109.013-T") described its *scope* but did not guarantee every named task
was carried all the way to a terminal state — it's easy to assume "the sync
commit for X" means "X is done" when it may only mean "X's claim/status was
touched in this pass."

**Rule going forward**: before any shipment safe-close, verify EVERY
manifest task's live status directly (`backlogit get {task_id}` or a queue/
archive presence check) — never infer completeness from a commit message,
a prior session's summary, or the presence of the task's implementation
diff in `git log`. This safe-close caught and fixed the gap
(`backlogit move 109.013-T --status done`) before archiving the shipment
record, preventing an inconsistent "shipped but one member never
completed" backlog state. The completion-gate's own `pre_task_completion_gate_passed`
log event correctly stamped `head_sha: 04cdea1...` (the merge commit,
i.e. current `HEAD` at completion time) rather than the original feature
commit — this is expected and correct: the gate records the SHA at which
the task was *administratively* completed, not necessarily the SHA that
introduced its code.

## 4. `CLAIM_NOT_OBSERVED` read-only contract (109.021/022/023-T) closes a three-times-flagged defect class

109.021-T replaced an illusory post-claim self-retry with a read-only,
honestly-uncertain `CLAIM_NOT_OBSERVED` result (a stateless detector cannot
distinguish "claim is merely delayed" from "claim failed"); 109.017-T then
owns the ONE bounded double-claim-guarded retry-and-reverify response to
that signal, escalating to terminal `CLAIM_VERIFY_FAILED` only on a second
`CLAIM_NOT_OBSERVED`. 109.022-T fixed `cli.py`'s telemetry outcome mapping
to record any non-zero/non-blocked/non-forced result (including the new
`CLAIM_NOT_OBSERVED` exit code) as `failed`, not silently `success`.
109.023-T made `closure_complete()` itself validate `closure_status`
/releasability — not `compaction_status` alone — closing a defect Copilot's
PR #297 review had already flagged twice as suppressed, never-promoted
comments before this shipment finally fixed it. This closure document's own
frontmatter is a live instance of that fix: it only registers
`closure_complete() == True` because its `closure_status` is `READY`
(no conditions block needed — see the closure doc itself).
