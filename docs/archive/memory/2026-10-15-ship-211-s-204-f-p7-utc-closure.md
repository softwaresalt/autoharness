# Session memory: 211-S / 204-F P7 UTC closure (ship session 2026-10-14 to 2026-10-15 UTC)

Date (UTC): 2026-10-15. Shipment 211-S, feature 204-F (P7: recorded dates and times are UTC with a Z suffix). Main PR #520 merged as merge commit `8110a0cd` (parents `aac7a507`, `fc9be451`). Dark factory mode (P-017) scope was 211-S only.

## Decisions

* Restored checkpoint `checkpoint-20261015-031503.json` after the operator explicitly selected it. Resolved it after a confirmed resume (branch, HEAD `d7a1a115`, clean worktree, shipment active, member tasks done and archived). Recorded the resumed state in `checkpoint-20261015-053827.json`, including the operator-waived engram requirement and its source.
* The engram requirement was waived by the operator. No prune-on-restore ran, and no file-based prune ran. The daemon was not killed or restarted, and `engram index --direct` was not run.
* Review-fix cycle 4, operator-approved (one extension): `_is_junction` was rewritten as a fail-closed Windows reparse-point check (commit `ab42b6a2`). Link fixtures refuse to skip on CI. The junction fixture is skipped as Windows-only off Windows.
* The delta review and the final overall review reported no P0 or P1 findings. Out-of-scope observations were captured under P-021 C2, and five existing captures were reused.
* The P-018 Copilot loop closed in one round. Copilot reviewed `fc9be451` as COMMENTED with 0 open findings, 0 threads, and 0 body findings. The gate returned SATISFIED before merge.
* Merge was a merge commit only (P-009). Admin fallback was not used.
* Closure path selected by the P-015 classifier: CASCADE, engine VERIFIED (backlogit 1.11.0). Cascade-close exited 0 with `postcondition_verdict: pass`.

## Learnings

* A PowerShell multi-line argument can silently split into an empty argument for a native CLI, which gave an exit-2 input refusal with `mutation_possible: no`. Pass single-line values (for example `%s`, not `%B`) to native CLIs.
* Do not redact a one-time capability token from your own output. Once it is lost, a lock can only be released by the operator with `-Force`.
* `uv build --offline` works from the warm cache when PyPI is unreachable. The online build failed on a TLS handshake.
* The Copilot review requested through REST `requested_reviewers` with `copilot-pull-request-reviewer[bot]` engaged the P-018 gate. The MCP request tool was not exposed in this session.

## Failed approaches

* First cascade-close attempt passed `--message` with a multi-line commit body. It was refused before any mutation.
* The first REST call to read a single review body used the wrong path. The correct path is `pulls/{n}/reviews/{id}`.

## Outcome

* PR #520 merged at `8110a0cd` with CI green (`ci gate`, `test`, `pipeline-topology`), no Copilot threads, and a Copilot review that approved with 0 open findings.
* Shipment 211-S and feature 204-F are archived, with all four member tasks archived as `done`.

## Follow-ups (P-021 captures)

New: `083F1DAD` (Windows CI job for P7 junction fixtures), `E1B4E9B2` (manifest-mirror path hardening), `1A97BC9B` (junction fixture cmd quoting), `D2537F45` (`_is_junction` naming and reparse semantics), `0CD465DA` (slim the P7 test), `B7928086` (test-harness error paths and pytest subTest skips), `785D4FC5` (local-time derivation denylist), `CECA0004` (output-timestamps pointer per preset). Reused: `6A811556`, `68D55E6C`, `003312F1`, `F8BDCEAD`, `48654A2B`.

## Open operational items

* Lock `.backlogit/queue/.211-S.md.lock` is still held. The operator must release it with `-Force`.
* `docs/memory/` is over the compaction thresholds (196 files, 1405 KB). Broader compaction is an operator or Stage decision and was not performed in this closure.
