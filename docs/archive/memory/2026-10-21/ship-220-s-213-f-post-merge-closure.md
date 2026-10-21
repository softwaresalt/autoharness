# Ship session memory: 220-S / 213-F post-merge closure

Date: 2026-10-21 (dark mode, P-017). Release 1.6.0 chain 2/6.

## Outcome

* Shipment 220-S (feature 213-F; tasks 213.001-T, 213.002-T, 213.003-T) merged via PR #546, merge commit `6f89df2a57ab86f48720fb8cac1c0806e3d89a2b` (two parents).
* Reviewed HEADs: `566ad578` (first), `d1b78ca86e5dc3a4e049ad2ca3573183917740f4` (final, merged).
* Close path: cascade (engine VERIFIED); 220-S archived `shipped`.

## Learnings

* The pre-push hook runs `python -m unittest discover -s tests`; new tests must be unittest `TestCase`s. A pytest-only file errors in the hook with `No module named 'pytest'` even though `uv run pytest` passes.
* The hook takes ~25 min and has two Windows-timing flakes (`test_shipment_close_poll` exit_9 and `test_gate_bootstrap_grant` replay tmp rename). Retries with different failures are not identical-attempt circuit-breaker hits.
* Copilot P-018 review caught an unconditional backlogit ordering pair (`backlogit_claim_shipment` in `pipeline_topology_gate_ship_agent_wiring`); fixed by moving only the backlogit-specific pairs to `PACK_ASSERTIONS['backlogit']`.
* Dogfood `.github/copilot-instructions.md` has no Remote Operator section; the install-harness pack-scope prune rule applies to rendered output only.

## Follow-ups

* Stash `4FA490F7`: bootstrap-grant replay flake and dogfood Remote Operator section gap.
* Existing stash covers the exit_9 flake.
