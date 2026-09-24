---
title: "Proof F run 2 (PE-1.4) - raw staged and HEAD checksum replay: findings (PASS)"
source: "docs/decisions/2026-09-24-staged-blob-checksum-proof-f-run2-spike.md"
doc_type: decision
description: "Stage-authored Proof F findings under charter PE-1.4 section 6.8, based on Ship's PE-1.4 verification-only replay in .proof-scratch/F-20260924-131854/. Ship ran its section 6.1 index refresh first, and the refresh succeeded. The raw staged-blob digest, captured in binary by a Python subprocess, equals the post-commit HEAD-blob digest. The combined Stage and Ship time is within the 30-minute bound, so Proof F is PASS. This proves only that the checksum procedure replays. It proves no production lifecycle code. The PE-1.1 PASS artifact stays in the record as history."
docline:
  type: spike
  date: 2026-09-24
  time_box: "30m"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "checksum"
    - "staged-blob"
    - "crlf"
    - "proof-entry"
    - "ship-lifecycle"
proof: F
proof_run: 2
proof_verdict: PASS
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
matrix_rows: [PE-DATA-04]
prior_run: "docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md (PE-1.1 PASS at 3df0509f; historical, unchanged, not re-labelled)"
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 52c985cb
activation_comparator: 4acba14a
scratch_path: ".proof-scratch/F-20260924-131854/"
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
---

# Proof F run 2 (PE-1.4) findings - raw staged and HEAD checksum replay

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS`** (Stage's explicit decision under charter section 6.8, PE-1.4) |
| Confidence | **High** for the section 6.8 pass criterion. Stage checked it independently where it could, read-only (see Independent Verification) |
| Pass criterion | The staged digest equals the post-commit HEAD digest. **Met**: both are `54ad053a036e5c9f25164302db6c2498ce5d67609e16dc924e8d11ba03a71468`, 16 bytes |
| Time bound (sections 6.1, 6.2) | 30m, covering Stage and Ship together. **Met** (see Time and File Bounds) |
| File bound (section 6.2) | 1 script and 1 disposable repository. **Met** |
| Negative control | Run and recorded. It is informational only and cannot fail the proof (section 6.8) |
| Matrix row | `PE-DATA-04`, evidenced by this run under PE-1.4. This is not a proof-exit audit |
| What this proves | Only that the compound section 1 raw staged-blob checksum procedure replays exactly on this Windows host. It proves no production lifecycle code, no activation and no claim readiness (`PE-ACTIVATE-03`) |
| Prior run | The PE-1.1 `PASS` (`docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md`) stays in the record as written. Under section 3.3 it does not satisfy PE-1.4 proof exit because it has no refresh evidence. This artifact is the new PE-1.4 run |

## Goal

Confirm that the established raw staged-blob checksum procedure replays
exactly under PE-1.4, so the terminal activation task cannot improvise it.
Section 6.8 says this proof has no open question. It replays
`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
section 1.

## Success Criteria

* **Pass**: the raw staged digest equals the post-commit HEAD digest, and the
  combined time is at most 30 minutes. The staged digest comes from
  `git cat-file -p :<path>`, captured in binary by a Python subprocess and
  hashed with SHA-256. The HEAD digest comes from `git cat-file -p HEAD:<path>`
  with the same capture.
* **Fail**: the raw staged digest differs from the HEAD digest after the
  commit, or a time or file bound is exceeded.
* **Blocked**: Ship's index refresh failed or could not be verified, a
  checkpoint anomaly or an active `ship` checkpoint was present, a
  per-invocation gate rejected the run, a `PE-ACTIVATE-01` path at `HEAD` had
  an unexpected blob or an uncommitted change, or the run wrote to a tracked or
  non-ignored path (section 6.1).

## Scope Constraints

* Stage did read-only analysis only. It ran no fixture, fixture command,
  build, test suite or linter. It did not run the index refresh or any backlog
  CLI mutation (P-010; section 6.1).
* The only tracked change is this findings artifact. It changes no source,
  template, config, manifest, agent, backlog item, shipment, stash entry,
  plan, review or charter.
* No claim, pull request, push, amend, plan revision 13 or review attempt 12.
  No other proof is advanced.
* No additional worktree. The P-016 Stage spike worktree exception was not
  used. The fixture repository is an independent `git init` repository inside
  scratch. It is not a worktree of this repository.

## Session and Tool State (PE-EVIDENCE-05)

| Item | State |
|---|---|
| Stage route | Configured in `.autoharness/config.yaml` as `claude-opus-5.5` / `anthropic` / `high`, which matches the requested route. The runtime cannot attest which model or reasoning effort it actually used, so this is recorded as **`ROUTING_DEGRADED`** (not verifiable) |
| Backlogit | MCP `TOOL_OK`: read-only `get_version` returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Stage index sync (Stage Step 0.1) | **Not run, on purpose.** Section 6.1 says "Stage never runs the refresh". Stage's backlog reads come after Ship's refresh and are only a read-only cross-check |
| Stage checkpoints | 67 `stage`-owned, all `resolved`. No quarantined records, none needing quarantine, 0 active. This is a normal zero-candidate startup |
| Engram | No engram tools in this runtime. `ENGRAM_DEGRADED`; files were read directly |
| Intercom | No intercom tools in this runtime. `INTERCOM_DEGRADED` |
| Graphtor-docs | No graphtor tools in this runtime. `GRAPHTOR_UNAVAILABLE`; `docs/` was read directly |
| Worktree at Stage start | One worktree. `git status --porcelain` empty. HEAD `52c985cb` |

## Investigation Approach

1. Read compound section 1 first, verbatim
   (`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`).
2. Read the charter: section 3.3 (the PE-1.4 change record and the
   carried-forward F status), section 4.3, section 6.1 (execution rules,
   refresh, gates, evidence handoff), section 6.2 (the F bound), section 6.8,
   and rows `PE-DATA-04` and `PE-ACTIVATE-01`.
3. Checked Ship's reported evidence read-only against the scratch directory,
   the host repository and backlogit. No fixture command was run.
4. Compared the replay script with the compound procedure and the section 6.8
   setup, then recorded the verdict.

## Findings

### What Was Discovered

#### Normative procedure (compound section 1)

> any manifest-checksummed file edited on a Windows dev box MUST have its
> checksum computed via (a) or (b) above — both of which route through a
> subprocess capture of raw `.stdout` bytes, never a shell redirect (`>`,
> `Out-File`, or piping through a PowerShell console) at any stage of the
> pipeline.

Variant (b) reads the staged blob as raw bytes through a subprocess, using the
colon-prefixed stage-0 ref `:<path>`.

#### Ship evidence (verification-only, section 6.1; reported by Ship)

| Gate / fact | Ship-reported result |
|---|---|
| Index refresh (transport, native result) | CLI `backlogit --no-update-check --log-level error sync`. Exit 0. Stdout is 23 bytes, `Indexed 1472 artifacts\n`, SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. Stderr empty |
| Checkpoint scan (unfiltered, after refresh) | 71 total: 70 resolved, 1 abandoned, 0 active. No validation or quarantine anomalies |
| Targeted checkpoint read | Official `checkpoint get checkpoint-20260914-210050.json` returned `valid: true`, status `abandoned`, `schema_version` 1, agent `ship` |
| P-001 (after refresh) | 0 active shipments, tasks, features and chores |
| Prior release unit | `173-S` archived. Closure PR #451 merged. `docs/closure/173-S-165-F-post-merge-closure.md` has `closure_status: READY` and `compaction_status: done` |
| P-011 / P-016 | Branch `chore/stage-176-s-workflow-defects`. HEAD `52c985cb` at fixture start. One worktree. `git status` clean before and after |
| `PE-ACTIVATE-01` pre-write check | All three blob IDs at `HEAD` match `4acba14a` |
| Host | Windows 11, NTFS, Python 3.12.10, PowerShell 7.6.6, Git 2.55.0.windows.5 |
| Scratch | `.proof-scratch/F-20260924-131854/`. Git-ignored. One script, `replay.py`, and one LF file in the independent disposable `repo/` |
| Final run | Exit 0. 13 subprocess `git` calls, each exit 0 |
| Safety | No change to host tracked files, backlog items, the shipment or the branch |

#### Replay result

| Step | Capture | Bytes | CRLF | SHA-256 |
|---|---|---|---|---|
| Initial HEAD blob (`HEAD^:checksum-fixture.txt`, `initial LF line\n`) | Python `subprocess.run(..., stdout=PIPE, text=False)` | 16 | 0 | `381b1618e74666a476c44ba3664b0ced772d792a5b197ed7f71af574ad4ae293` |
| Staged blob `:checksum-fixture.txt` after `git add` of the LF change | Same binary capture | 16 | 0 | `54ad053a036e5c9f25164302db6c2498ce5d67609e16dc924e8d11ba03a71468` |
| HEAD blob `HEAD:checksum-fixture.txt` after the commit | Same binary capture | 16 | 0 | `54ad053a036e5c9f25164302db6c2498ce5d67609e16dc924e8d11ba03a71468` |
| Negative control: PowerShell text capture | PowerShell text pipeline | 17 | 1 | Not an admissible digest. It differs from the raw blob, which fits LF being rewritten to CRLF |

The staged digest equals the HEAD digest. The script compares the two byte
strings (`staged == head_blob`) and exits non-zero if they differ.

#### Independent verification by Stage (read-only; no fixture command)

| Check | Stage observation | Agrees with Ship |
|---|---|---|
| Scratch directory exists and is Git-ignored | Exists. `git check-ignore -v` resolves it to `.gitignore:10:.proof-scratch/` | Yes |
| Scratch contents | `replay.py`, `repo/.git/` and `repo/checksum-fixture.txt`. Nothing else outside `repo/.git/` | Yes |
| `replay.py` size and SHA-256 | 3100 bytes, `080d69a341655689ce043470d4f1dfabffa33e76dde2a32f5d75e3246981cd3c` | Yes |
| Fixture file bytes | 16 bytes, 1 LF, 0 CR. SHA-256 `54ad053a...a71468`, read directly from the file with `core.autocrlf false`, so it is byte-identical to the blob | Yes |
| Literal content hashes | SHA-256 of `initial LF line\n` is `381b1618...4ae293`. SHA-256 of `changed LF line\n` is `54ad053a...a71468`. Both computed in memory | Yes |
| Script call count | Counted statically: `init`, three `config`, `add`, `commit`, `rev-parse`, `add`, `cat-file :path`, `commit`, `cat-file HEAD:path`, `rev-parse`, `cat-file HEAD^:path`. That is 13, under the script's own cap of 14 | Yes |
| Script conformance | Binary `stdout=PIPE, text=False`. Hashes `.stdout` directly. Stage-0 `:` ref. `core.autocrlf false`. Refuses to reuse a non-empty `repo/`. 60 s deadline | Conforms to compound (a) and (b) and section 6.8 setup |
| Unfiltered checkpoint list (MCP, read-only) | Totals: `total: 71`, `quarantined: 0`, `needs_quarantine: 0`. 67 `stage`/resolved, 3 `ship`/resolved, 1 `ship`/abandoned. No records with an empty agent or status | Yes |
| Targeted checkpoint read (MCP `get_checkpoint`) | `checkpoint-20260914-210050.json` returned **`valid: true`**, `schema_version: 1`, `agent: ship`, `status: abandoned`. Disposition reason: superseded by `checkpoint-20260914-224530.json` after PR #451 merged. It is **not** an anomaly and **not** an active `ship` recovery candidate | Yes |
| Active shipments and items (MCP, read-only) | `list_shipments status=active` returned `[]`. `list_items status=active` returned `[]` | Yes |
| `PE-ACTIVATE-01` at `HEAD` `52c985cb` | Template `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, mirror `e22916b62f36f1c25c421882a05f4049f1862c02`, manifest `251f46e8c95703ed65e421210d3b08682d79d8bc`, all identical to `4acba14a`. `git diff 4acba14a HEAD` for the three paths is empty. `git status --porcelain` for them is empty | Yes |
| Host tracked state | `git status --porcelain` empty. One worktree. Branch as reported | Yes |
| `.backlogit` ignored paths (Stage observation afterwards) | Only Git-ignored, tool-managed paths: `backlogit.db`, `-shm`, `-wal`, `.locks/` and `*.lock`, `hooks_queue.jsonl`, `logs/*.jsonl` and `runtime/`. No tracked or non-ignored change under `.backlogit` | Consistent. The before and after delta itself was not in the handoff (see Remaining Unknowns) |
| Closure record | `docs/closure/173-S-165-F-post-merge-closure.md` has `closure_status: READY` and `compaction_status: done` | Yes |

**False-positive guard.** A preflight that reads only `status != resolved`
from the checkpoint list would flag `checkpoint-20260914-210050.json` as a
problem. The official targeted read settles it. The record is schema-valid
(`valid: true`), it is `abandoned` rather than `active`, and it has a recorded
disposition. So it does not trigger the section 6.1 anomaly or active-`ship`
BLOCKED rule. Later preflights should use the same targeted
`get_checkpoint` validation. A non-`resolved` status on its own is not an
anomaly.

#### Static conformance with compound section 1

| Compound requirement | Replay | Conforms |
|---|---|---|
| Raw `.stdout` bytes from a subprocess, never a shell redirect or a PowerShell pipe | Yes | Yes |
| The staged read uses the stage-0 `:<path>` ref | `:checksum-fixture.txt` | Yes |
| The HEAD read uses `HEAD:<path>` with the same capture | Yes, after the commit | Yes |
| `git add --renormalize` when an `eol=lf` pin is added in the same change | The script uses a plain `git add`. The fixture has no `.gitattributes` and has `core.autocrlf false`, so renormalizing would not change the index entry. Section 6.8 does not require it | Not relevant to this replay |

### What Was Tried and Failed

* **First script invocation, exit 1.** The subprocess argument list left out
  the `git` executable. The first call failed before `git init` finished.
  The only thing left behind was an empty `repo/` directory. There was no
  digest and no proof evidence. Ship corrected the one script in place, in
  the same scratch directory, so the file count stays at one script. The
  script refuses to reuse a non-empty `repo/`, and the empty directory
  passed that check. The corrected run exited 0.
* **Stage adjudication.** This was a harness defect before any evidence
  existed. It is not an evaluation of the proof question. It is therefore not
  a `FAIL`, and the corrected run is not a `PE-FLOW-04` re-run of a failed
  question. It happened inside the same Ship invocation and time bound, which
  also matches the PE-1.1 precedent for fixing an ephemeral command before
  evidence.
* **Negative control.** The PowerShell text capture produced 17 bytes with one
  CRLF, where the raw blob is 16 bytes of LF. This fits the documented hazard.
  It is informational only.

### Time and File Bounds

| Component | Elapsed |
|---|---|
| Ship (reported, from start) | 7m08s |
| Stage analysis and authoring (host clock, 13:23:31 to the pre-commit check at 13:27:56 local time) | 4m25s |
| **Combined** | **11m33s**, within the 30m bound |

This is a conservative sum. Any overlap between the Stage and Ship windows is
counted twice. File bound: one script (`replay.py`, corrected in place) and
one disposable repository holding one LF file. The bound is met.

### Matrix Row Status (Proof F only; not a proof-exit audit)

| Row | Criterion | Evidence | Status |
|---|---|---|---|
| `PE-DATA-04` | Proof F staged digest equals HEAD digest | Replay Result: both `54ad053a...a71468`, from Ship's run and checked by Stage | Satisfied by this PE-1.4 run |
| `PE-ACTIVATE-01` | The three paths match the `4acba14a` blobs, with no uncommitted change | Stage check at `52c985cb` | Holds at this commit. It is formally checked at proof exit |

### Remaining Unknowns

These are for the proof-exit audit (`PE-AUTH-02`, `PE-EVIDENCE-01`). None of
them bears on the section 6.8 criterion, and none meets a section 6.1
BLOCKED trigger. The refresh was verified (CLI exit 0 with bounded output),
and Stage saw no tracked or non-ignored change.

1. The handoff Stage received names the CLI transport. It does not say
   whether the MCP `backlogit_sync_index` was tried first or what it returned.
2. The handoff gives no before and after comparison of
   `git status --porcelain --ignored -- .backlogit`, and does not name any
   non-cache ignored paths the refresh wrote. Stage's check afterwards shows
   only tool-managed ignored paths.
3. The handoff summary does not itemize the P-010 self-check or the P-002
   result (not applicable, since there was no claim).

If Ship's full transcript has these fields, the proof-exit report should cite
them. If it does not, the proof-exit audit must decide whether this run is
admissible for `PE-AUTH-02` and `PE-EVIDENCE-01`. The Proof F verdict stands
either way.

Linux is not part of Proof F. The digests are over raw blob bytes. No Linux
claim is made.

## Recommendation

**Conclusion**: proceed
**Confidence**: high

Record Proof F as `PASS` under PE-1.4. The terminal activation task must
compute manifest checksums from raw staged-blob bytes, exactly as compound
section 1 prescribes:

* use a Python subprocess with binary capture;
* read the stage-0 `:<path>` ref;
* take the SHA-256 of `.stdout`;
* run `git add --renormalize` first when an `eol=lf` pin is added in the same
  change.

No redirect and no PowerShell text capture is allowed at any stage. This
verdict proves the procedure only. It proves no production lifecycle code,
authorizes no activation (`PE-ACTIVATE-02`) and confers no claim authority
(`PE-ACTIVATE-03`).

## Next Steps

* Cite this artifact as Proof F's PE-1.4 verdict in the section 8 proof-exit
  report. Keep the PE-1.1 artifact as history.
* At proof exit, settle the three handoff-completeness items above from Ship's
  full transcript.
* Ship may remove `.proof-scratch/F-20260924-131854/` only under the section
  6.1 cleanup rule. Stage does not remove it.
* This session stops at Proof F.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections 3.3,
  4.3, 6.1, 6.2, 6.8, 7.7 row `PE-DATA-04`, 7.10 row `PE-ACTIVATE-01`, 8)
* `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
  (section 1)
* `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md` (PE-1.1
  run, historical)
* `docs/closure/173-S-165-F-post-merge-closure.md`
* `.proof-scratch/F-20260924-131854/replay.py` (Git-ignored, disposable, never
  committed)
* `.github/skills/spike/SKILL.md`
* `.github/agents/_stage.agent.md`
* `.github/agents/_ship.agent.md`
* `.github/instructions/role-enforcement.instructions.md`
