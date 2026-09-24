---
title: "Proof G (PE-1.4) - ordinary resolved-path containment with bounded reads: findings (PENDING-LINUX)"
source: "docs/decisions/2026-09-24-ordinary-path-containment-proof-g-spike.md"
doc_type: decision
description: "Stage's Proof G findings under charter PE-1.4 section 6.9. Ship ran the Windows half on native Windows 11 (build 26200, NTFS, Python 3.14.3) in .proof-scratch/G-20260924-134101/. Stage checked the fixture read-only. It supports all 49 Windows case variants (22 lexical, 17 resolved, non-regular or missing, 10 bounded), the mandatory junctions, all optional symlinks, the cap+1 reads at the helper's read call, the pre-open count cap, both trust roots and the fact that the sentinel was never exposed. Windows is PASS. No qualifying Linux host was used, so Linux is PENDING, never PASS. The verdict is PENDING-LINUX. Actual Linux-native execution is a non-waivable, not-deferrable execution and release gate for the later implementation. The run proves static containment only. It claims no race, TOCTOU or hardlink-alias resistance, and it is no production lifecycle code."
docline:
  type: spike
  date: 2026-09-24
  time_box: "90m"
  conclusion: "proceed"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "path-containment"
    - "bounded-reads"
    - "windows-ntfs"
    - "proof-entry"
    - "ship-lifecycle"
proof: G
proof_run: 1
proof_verdict: PENDING-LINUX
host_verdicts: {windows: PASS, linux: PENDING}
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
matrix_rows: [PE-SAFETY-01, PE-SAFETY-02, PE-SAFETY-03, PE-SAFETY-04, PE-SAFETY-05, PE-SAFETY-06, PE-SAFETY-07, PE-EVIDENCE-02, PE-INTERFACE-01]
linux_gate: "not-deferrable execution and release gate (linux-execution-gate, section 6.9); non-waivable; no Windows substitution"
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 8b39a08b
activation_comparator: 4acba14a
scratch_path: ".proof-scratch/G-20260924-134101/"
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
---

# Proof G (PE-1.4) findings - ordinary resolved-path containment, Windows half

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PENDING-LINUX`** (Stage decision under section 6.9). This is **not** `PASS` and may never be reported as `PASS` |
| Windows (native NTFS) | **`PASS`**: every accept case returned the exact bytes, every reject case returned its closed code, and the sentinel's bytes appear in no result (see the evidence notes) |
| Linux | **`PENDING`**: not executed, not inferred from Windows, not simulated |
| Linux gate | A `not-deferrable`, **non-waivable execution and release gate**. The full Linux case set must run in CI on a Linux runner with a Linux-native filesystem. No lifecycle release unit that depends on this containment ships without it. Windows evidence never satisfies it (`PE-EVIDENCE-02`) |
| Confidence | **Medium**. The case count, fixture state, digests and control flow were verified by Stage. The per-case PASS rows come from Ship's report and are corroborated only indirectly (evidence note 1). There are three open proof-exit items (see Remaining Unknowns) |
| What this proves | That this disposable helper's static resolved-path containment and bounded reads behave as specified on one native Windows host. It is no production lifecycle implementation. It confers no claim, publication or activation readiness (`PE-ACTIVATE-03`) |
| Non-claims (`PE-SAFETY-06`) | No race, TOCTOU or hardlink-alias resistance is claimed. The optional hardlink observation was not run |

## Goal

Charter section 6.9: does ordinary resolved-path containment with bounded
reads satisfy every SAFETY row on actual Windows and actual Linux? This
artifact records the Windows half and carries the Linux half forward.

## Success Criteria

* **Pass (per host)**: every accept case returns the correct bytes, every
  reject case returns its specified closed code, and the sentinel's bytes
  never appear in any result.
* **Fail**: any escape, silent truncation or unexplained platform divergence
  on an executed host, or an exceeded time or file bound.
* **Verdict rule**: `PASS` only when both hosts pass. `PENDING-LINUX` when
  Windows passes and Linux is `PENDING`. `BLOCKED` when Windows could not be
  executed.

## Scope Constraints

* Stage worked read-only. It ran no fixture, build, test or lint, did no index
  refresh, and made no backlog mutation. It did not read the sentinel file's
  contents or hash it.
* The only tracked change is this new findings artifact. No plan, charter,
  shipment, stash or backlog change. No amend, push or PR. No other worktree.

## Session and Tool State (PE-EVIDENCE-05)

| Item | State |
|---|---|
| Stage route | `.autoharness/config.yaml` sets `stage` to `claude-opus-5.5` / `anthropic` / `high`, as requested. The runtime cannot attest the model actually used, so this is `ROUTING_DEGRADED` (not verifiable) |
| Backlogit (Stage) | MCP `TOOL_OK`: read-only `get_version` returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Stage index sync | **Not run, on purpose** (section 6.1 and the operator directive). Only Ship refreshes |
| Stage checkpoints | Unfiltered `consumer_id: stage` enumeration: 67 records, all `stage`/`resolved`, 0 anomalies, 0 active. Normal zero-candidate startup |
| Engram, intercom, graphtor-docs | No tools in this runtime: `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`. Files were read directly |
| Worktree | One worktree. `git status --porcelain` empty. HEAD `8b39a08b` |
| `PE-ACTIVATE-01` (Stage check) | The three HEAD blobs equal those at `4acba14a` (`4ccd7fdc…`, `e22916b6…`, `251f46e8…`). `git diff 4acba14a HEAD` for the paths is empty, and the paths show no status |

### Ship invocation record (as reported by Ship)

* Backlogit ran in P-012 CLI fallback. The same-invocation `backlogit sync`
  exited 0. Stdout was 23 bytes, SHA-256
  `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. Only
  the ignored `.backlogit/backlogit.db` and its `-wal` changed. No tracked
  path changed.
* Unfiltered checkpoint list: 71 records (70 `resolved`, 1 `abandoned` that
  is valid on official get, 0 active, 0 anomalies). Active-filtered
  shipment, task, feature and chore reads returned 0 (P-001). There was one
  worktree, and the current branch was clean at HEAD `8b39a08b` (P-016).
* Host: Windows 11 Enterprise build 26200, NTFS, Python 3.14.3. Final native
  fixture exit 0 in 0.226 s. No tracked host mutation. No cleanup was done,
  as instructed.
* Two setup failures happened before any case ran: `cmd` quoting for
  `mklink`, then a non-idempotent `mkdir`. Both were fixed in place without
  changing expectations. The final script keeps the second fix
  (`exist_ok=True`), plus a junction reuse that checks the exact target.

## Investigation Approach

1. Checked the prior Stage compound learnings (`docs/compound/`). None covers
   path containment. The process precedents are the PE-1.4 Proof B, C, E and
   F findings artifacts.
2. Read charter section 6.9, sections 6.1 and 6.2, and rows `PE-SAFETY-01` to
   `07`, `PE-EVIDENCE-01` and `02`, `PE-INTERFACE-01` and `PE-SCOPE-07`.
3. Read the fixture script in full and statically traced each case through
   `resolve_and_read`.
4. Read-only checks: script SHA-256, reparse-point listing, per-file SHA-256
   (excluding the sentinel), a recomputation of the case-data digest in
   PowerShell, and the Git-ignore status.

## Findings

### What Was Discovered

#### Fixture identity and state (Stage-verified)

* Script: `proof_g_windows_ntfs.py`, 14165 bytes, SHA-256
  `1da8001bf608c59112eb78b432d36c76a12d239fcd4f663bb117485e302d86e9`. This
  matches Ship's value.
* Case-data digest: Stage recomputed it with the script's algorithm (sorted
  relative path, NUL, 8-byte big-endian length, bytes) over the 12
  non-sentinel data files. The result,
  `11e1e902103d28011d4a93e7eb0dbadc0d13238fdfdb89b507b63d63c2d0203d`,
  matches Ship's value.
* Scratch is Git-ignored (`.gitignore:10: .proof-scratch/`).
* There are two disposable roots under `tree/`: the workspace root `ws` (the
  autoharness root `ws/.autoharness` sits inside it) and the outside sibling
  `ws-outside`, which holds `sentinel.txt` (52 bytes by metadata; not read or
  hashed by Stage).
* All eight reparse points exist with the expected targets:

| Link | Type | Target (under the scratch `tree/`) | Case |
|---|---|---|---|
| `ws/j-out` | Junction (mandatory) | `ws-outside` | G15, G21b |
| `ws/j-in` | Junction (mandatory) | `ws/docs` | G16, G30b |
| `ws/.autoharness/up` | Junction (mandatory) | `ws/docs` (outside root A) | G23 |
| `ws/s-f-out` | File symlink | `ws-outside/sentinel.txt` | G17 |
| `ws/s-d-out` | Directory symlink | `ws-outside` | G18 |
| `ws/s-f-in` | File symlink | `ws/docs/in.txt` | G19 |
| `ws/dl-in` | Dangling symlink | `ws/docs/absent.txt` | G20a |
| `ws/dl-out` | Dangling symlink | `ws-outside/absent.txt` | G20b |

Per-file fixture SHA-256 (non-sentinel):

| File | Bytes | SHA-256 |
|---|---|---|
| `ws/.autoharness/m.yaml` | 9 | `038a833092668c8cfa31da7ab9a0ad42dee954d4982aadf4067a351db32fe9e4` |
| `ws/b/big.bin` | 4096 | `b23f99e1f653e62fa5bc14cc528a9ec3b6d11be482b2ee51b519d1d6ad8c5466` |
| `ws/b/cap.bin` | 64 | `d53eda7a637c99cc7fb566d96e9fa109bf15c478410a3f5eb4d4c4e26cd081f6` |
| `ws/b/cap1.bin` | 65 | `3db14a3b436f09c012eaf07ed03300ef30f349936a414abe4d3946d3ae578170` |
| `ws/docs/in.txt` | 9 | `91752262c2ee7b491e8451d5700e19c76a180d047cf96bd8875db26697abf4d0` |
| `ws/n/c1.txt` | 6 | `fc74a830ae386759cdb2b33bb30bf533dbdac1ea430d05e592f15fc504f9fe39` |
| `ws/n/c2.txt` | 6 | `f4cae61eca33153ecba91538aea7135d8c3dc4241975958e8929582422865ffd` |
| `ws/n/c3.txt` | 6 | `f7a81c601fa168166d3b158c67db45e97549dcaeb634ffcfd0d4773e49746458` |
| `ws/n/c4.txt` | 6 | `b94af45199d970b41a76fba2eeda3f4f75be86d4d7036a9c98230b51220b716d` |
| `ws/t/t1.bin` | 64 | `96ca1e8d176b8f0fb41dc5a66bdd553ba480489369abc337a7c5b397d3c8279d` |
| `ws/t/t2.bin` | 64 | `b7c30af04cbc5be8a5c7120c3f15e25c6823404a1da36b9baf30591679cb4736` |
| `ws/t/t3.bin` | 1 | `f67ab10ad4e4c53121b6a5fe4da9c10ddee905b978d3788d2723d7bfacbe28a9` |

#### Case matrix coverage (Stage static count of the `cases` list)

There are 32 rows (G01 to G32). G31, the FIFO case, is Linux-only and
recorded `NOT_APPLICABLE_ON_WINDOWS`. The 31 Windows rows expand to **49
variants**, which supports Ship's count:

| Class | Variants | IDs | Count |
|---|---|---|---|
| Lexical (`LEXICAL_INVALID`) | Empty, NUL, absolute drive path, rooted `/` and `\`, `..`, interior `a/../../x`, `C:x`, UNC, `\\?\` and `//?/`, `\\.\` and `\\.\NUL`, ADS `:s` and `::$DATA`, `CON`, `con`, `docs/NUL`, `COM1`, trailing dot, trailing space, `../` from root A | G01-G13 (21), G24 | **22** |
| Resolved, non-regular, missing | In-root accept; junction out and in; file and directory symlink out; in-root symlink; dangling in (`PATH_NOT_FOUND`) and out (`OUTSIDE_TRUST_ROOT`); upper-case root accept and escape; root A and `.autoharness/` via root W accept; root A junction escape; directory and junction directory (`NOT_REGULAR_FILE`); missing file and missing parent (`PATH_NOT_FOUND`) | G14-G23 (13), G30a-b, G32a-b | **17** |
| Bounded | Exact 64-byte accept; 65-byte and 4096-byte `FILE_SIZE_LIMIT`; total 64+64 accept then `TOTAL_SIZE_LIMIT`; count 3 accepts then `FILE_COUNT_LIMIT` | G25-G29 | **10** |

Every section 6.9 case is present. That covers every lexical form, the
mandatory outside junction and the in-root junction, the file and directory
symlinks, the dangling symlinks, a case-variant root, cap+1, total, count,
non-regular and missing. No accept case skips a byte-equality check.

#### Per-criterion trace (Stage static trace; results as reported by Ship)

* **Lexical before resolve (`PE-SAFETY-01`, `07`).** `lexical_invalid`
  returns before the root lookup and before `Path.resolve`. Ship reports
  that all 22 variants gave `LEXICAL_INVALID` with 0 candidate resolves.
* **Both roots (`PE-SAFETY-02`, `03`).** Root W accepts in-root paths and
  rejects `j-out`, `s-f-out`, `s-d-out` and `dl-out` as `OUTSIDE_TRUST_ROOT`.
  Root A accepts `m.yaml` and rejects `up/in.txt`, a junction to a sibling
  inside W but outside A. Containment uses `os.path.commonpath` over
  `normcase` paths, with no string prefix. It is checked before existence, so
  the dangling outside link is `OUTSIDE_TRUST_ROOT`.
* **Bounds (`PE-SAFETY-04`, `05`).** The read request is
  `min(MAX_FILE+1, remaining+1)`. G26 and G27 read at most 65 bytes and
  return none. G28c reads 1 byte with 0 remaining and returns none. G29d is
  rejected before `open`, with the real `OPEN_CALLS` counter at 0. G25 and
  G28a-b accept exactly 64 bytes. There is no truncated success.
* **Sentinel.** No case opens the sentinel. Every outside path is rejected
  before `open`. The random per-run token is checked against every returned
  `data` and the serialized result rows, and the fixture prints no inputs,
  contents or sentinel hash.
* **`PE-INTERFACE-01`.** `resolve_and_read(root_id, relative, budget)` takes
  no traversal-adapter parameter. The roots come from a private module map.

#### Evidence-strength notes (honest limits)

1. **Per-case rows are Ship-reported only.** Ship reported the per-case
   stdout in its session only. The handoff has no raw fixture output or its
   SHA-256. Two things corroborate PASS. First, the script exits 0 only when
   `pass_all` is true (no FAIL row, no leak, and every probe holds). Second,
   there were zero skips: all five symlinks exist on disk, and a leftover
   link from an earlier attempt would have raised a non-1314 error and
   exited 2.
2. **The candidate-resolve count comes from control flow.** It is a constant
   in each return path, not an intercepted call counter. Stage accepts it
   because the source shows the lexical return comes before any resolve.
3. **"Read at most cap+1" is proven at the helper's `stream.read` call, not at
   the OS layer.** The file is opened with default buffering, so CPython's
   reader may fill its internal buffer, larger than 65 bytes, from the OS.
   For G27 (4096 bytes) the whole file may have been transferred into process
   memory and never returned. This is not an escape or a truncation, and the
   sentinel is never opened. But it is a limit on what the evidence shows.
4. **The case-variant root is canonicalized.** `W_UPPER` is resolved with
   `strict=True`, which on Windows may restore the on-disk case before the
   comparison. The run shows that an upper-case root spelling gives correct
   accept and reject results. The case-insensitive comparison itself rests
   on `normcase` in `contained()`, confirmed statically.

### What Was Tried and Failed

Ship's two setup attempts failed before any case ran (`mklink` quoting, then
`mkdir` without `exist_ok`). They were fixed in place. No case expectation
changed.

### Time and File Bounds

* **Time (90m, Stage and Ship together).** Stage's preparation started after
  the `8b39a08b` commit (13:28:12 -07:00). Ship's scratch is stamped 13:41,
  Ship handed off at 13:46, and Stage adjudicated from 13:47. The commit
  timestamp of this artifact is the authoritative end. That is well under
  90m, including both setup failures. **Met.**
* **File (2 disposable).** Ship authored 1 script. It generates 2 disposable
  roots (`ws`, `ws-outside`) holding 13 regular files and 8 reparse points.
  Stage counts the generated tree by root, as the Proof F precedent does
  ("1 script and 1 disposable repository"). Section 6.9's own mandatory setup
  (outside sibling, sentinel, junctions, cap files) cannot fit in two literal
  files. **Met under that interpretation**, which the operator must ratify at
  proof exit. Stage does not assert an overrun. If the operator adopts a
  literal per-file count instead, `PE-SCOPE-07` makes this run `FAIL`.

### Matrix Row Status (Proof G only; not a proof-exit audit)

| Row | Windows | Linux |
|---|---|---|
| `PE-SAFETY-01` to `05`, `07` | PASS | PENDING (`linux-execution-gate`) |
| `PE-SAFETY-02` symlink sub-case | Executed (privileged). No deferral needed | PENDING |
| `PE-SAFETY-06` | The fixture and this artifact make non-claims only | Applies to future artifacts |
| `PE-EVIDENCE-02` | `Windows` on NTFS, from Ship's host record | PENDING. The gate is carried as `not-deferrable` |
| `PE-INTERFACE-01` | No adapter parameter | Carried into the implementation matrix draft |

### Remaining Unknowns

1. **`PE-EVIDENCE-01`**: the exact invocation line and the raw fixture stdout
   (or its SHA-256) are missing from the handoff. They are open until Ship
   supplies them or a Windows re-run records them.
2. **`PE-AUTH-02`**: Ship reported P-001 and P-016 results. P-002 and P-011
   were not itemized.
3. **File-bound interpretation**: needs operator ratification (see Time and
   File Bounds).
4. **Linux**: every Linux behavior, including G31 (FIFO), is unknown until an
   actual Linux-native run.

## Recommendation

**Conclusion**: proceed
**Confidence**: medium

Record Proof G as `PENDING-LINUX`, with Windows `PASS` and Linux `PENDING`.
Carry the Linux half into the implementation matrix draft as a
`not-deferrable`, non-waivable execution and release gate. Treat Remaining
Unknowns 1 to 3 as proof-exit preconditions, not as met. The implementation
should also define the byte bound at the OS read layer (unbuffered, or an
explicit raw-read loop) and measure it the same way on both hosts.

## Next Steps

1. The operator decides how to close Remaining Unknowns 1 to 3 (supplied
   evidence or a bounded Windows re-run) before the proof-exit report.
2. The proof-exit report lists Proof G as `PENDING-LINUX`, never `PASS`,
   runs the `PE-SAFETY-06` text audit, and carries the Linux gate forward.
3. Implementation CI runs the full Linux case set on a Linux runner with a
   Linux-native filesystem, including G31. Until then, nothing that depends
   on this containment is released.
4. Ship owns cleanup of the scratch directory when the operator directs it.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` sections 6.1,
  6.2 and 6.9, and 7.6 to 7.10
* `.proof-scratch/G-20260924-134101/proof_g_windows_ntfs.py` (Git-ignored,
  not committed)
* `docs/decisions/2026-09-24-staged-blob-checksum-proof-f-run2-spike.md`
  (the file-bound precedent)
* `.github/skills/spike/SKILL.md` (artifact template)
