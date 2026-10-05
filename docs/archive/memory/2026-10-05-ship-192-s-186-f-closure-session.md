# Ship session — 192-S / 186-F (ship lifecycle Unit A) execution and closure

* Date: 2026-10-05 (UTC 06:30–08:30)
* Agent: Ship, invoked by the Orchestrator at depth 1 under P-013.5
  (claude-opus-5.5 / anthropic / high / long_context) in dark-factory mode
  (P-017). Scope item: 192-S only.
* Outcome: implementation PR #494 merged as `bf43cc0b` (merge commit, two
  parents). Cascade close `CLOSED`. Closure PR follows on
  `post-merge/186-f-ship-lifecycle-unit-a`.

## IM-14 harvest-commit audit (recorded before the claim)

The plan's Non-Claim Audit Inventory requires an audit before the first Ship
claim or closure after a harvest commit lands. For each non-merge harvest
commit, Ship audited the commit's own diff with the plan's detector, applied
to normalized added lines and to adjacent-line joins. The audit ran at
2026-10-05T06:33Z, before the 192-S claim at 06:35Z. The rows below give the
added-line count and hit count per commit; "IM-14 line" means the line "no
added/edited text claims race, TOCTOU or hardlink-alias resistance".

| Commit | Harvest | Added lines | Hits | Disposition |
|---|---|---|---|---|
| `2b678b4d` | S(A): 186-F, 186.001-T, 186.002-T, 192-S | 164 | 9 | All non-claim: the requirements-trace line restating IM-14 / PE-SAFETY-06, and the IM-14 line |
| `45c85206` | S(C): 187-F, 187.001–005-T, 193-S | 334 | 26 | All non-claim (see the list after this table) |
| `e5334864` | S(B-core): 188-F, 188.001–003-T, 194-S | 225 | 9 | All non-claim: IM-14 lines |
| `90f23361` | S(B-entry): 189-F, 189.001–003-T, 195-S | 231 | 9 | All non-claim: IM-14 lines |
| `c70e72d0` | S(D): 191-F, 191.001–004-T, 197-S | 278 | 12 | All non-claim: IM-14 lines |
| `7ca13f66` | S(IM-10): 190-F, 190.001–002-T, 196-S | 168 | 9 | All non-claim: IM-14 / IM-15 acceptance lines |

The 26 hits in `45c85206` are:

* the IM-14 lines;
* the required non-claim sentence: "This reader makes no race, TOCTOU or
  hardlink-alias resistance claim.";
* "This is ordinary input rejection, not a race defense (FI-10)";
* the retired revision-12 code name `RACE`;
* the audit-test controls list.

No harvest commit claims race, TOCTOU or hardlink-alias resistance.

## Execution facts

* **Startup.** The backlogit MCP was not exposed, so Ship used the CLI
  fallback. Intercom, engram and graphtor were not exposed and ran degraded.
  The checkpoint scan covered 98 records unfiltered: 0 anomalies and 0
  active `ship` candidates.
* **Topology.** `pre_claim` passed from `main`, then again from
  `feat/192-s-s-ship-lifecycle-unit-a-evidence-contract-conformance`
  (`declared_root`, `forced: false`). `post_claim` exited 0.
* **A1** (`ab4137c5`): P-002/P-004 roster wording and history row `1.32.0`.
  The full suite passed, 3154 tests.
* **A2 plus local-review fixes** (`294c30ac`), then the delta P3s
  (`7c051fe9`). The full suite passed, 3170 tests, `OK (skipped=54)`.
* **IM-12.** Before each refresh, the recorded checksum equaled
  `SHA-256(HEAD:path)`. Each refreshed checksum came from the raw staged
  blob, captured with a Python subprocess. The disposable script lived at
  `.proof-scratch/192-S-im12/refresh.py`; it is Git-ignored and was cleaned
  up after closure.
* **Copilot.** One round on `7c051fe9`, with 2 threads. Both were out of
  scope under P-021 C1. Each was declined with its deferred ID cited
  (`21CDBC0A`, `EC980E56`) and resolved. P-018 returned `SATISFIED` with
  `--enforcement required`.

## Lessons for future sessions

1. **Use the repo CLI for closure commands.** The global `autoharness`
   (`C:\Python\Python314` site-packages 1.5.0) predates the `shipment`
   command. Run `autoharness shipment cascade-close` and
   `autoharness gate closure-evidence` through the repo `.venv` CLI
   (`.venv/Scripts/autoharness.exe`, an editable install of `src/`). The
   older global CLI exited 1 on `shipment` and mutated nothing. `uv run`
   fails here because the TLS handshake to PyPI fails.
2. **Done tasks move to the archive immediately.** `backlogit move <task>
   --status done` relocates the task to `.backlogit/archive/` with
   `status: done`. Pre-mode then classifies it `pre-archived`. That is
   expected.
3. **The closure-evidence gate checks conditions.** For
   `closure_status: READY_WITH_CONDITIONS` it requires every `conditions`
   entry to carry `satisfied: true` plus evidence. Put only conditions that
   gate closure there. A forward-looking release hold belongs in the record
   as a tracked condition, satisfied by recording and tracking it, with the
   hold itself carried by stash follow-ups.
4. **Template portability needs plan-level deliberation.** AGENTS.md Core
   Rule 2 (technology-agnostic templates) conflicts with plan text that
   writes runner-specific RED vocabulary into product templates. Copilot
   cited the rule, and three local personas rated it P1. It was deferred
   (`EC980E56`) because fixing it means new cross-runner semantics.
5. **Watch for plan preflight drift.** Plan D3 preflight (1), which compares
   against the FI-12 blobs, is already unsatisfiable at HEAD (`808BAB5E`).
   Stage should re-baseline it before S(D).

## Follow-ups (stash)

| ID | Priority | Subject |
|---|---|---|
| `EC980E56` | high | Template portability of the RED vocabulary |
| `21CDBC0A` | high | Template Ship batch caller vs the single-task actor |
| `E0136957` | medium | `harness-surface:none` and the `harness-ready` gate |
| `8BE38096` | low | Step 4 per-test marker stubs |
| `4D600C75` | low | P-004 evidence-record hardening |
| `808BAB5E` | medium | D3 preflight FI-12 drift |
