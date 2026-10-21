---
title: "Ship session memory: 222-S / 215-F post-merge closure"
date: 2026-10-21
agent: ship
shipment: 222-S
feature: 215-F
---

# Ship session: 222-S / 215-F (engine line 1.11 verified, 1.12 only after probe), dark mode P-017

Release 1.6.0 chain 4/6.

## Decisions

* PR #550 merged as `1b5dd29aed72af8071dbb7e037010740ddc71390` (merge commit, two parents, in origin/main). Tasks 215.001-T and 215.002-T (docs, matrix rows, pin tests only).
* Reviewed HEADs: `8fa740f7` (local review clean), `c9c417d4` (final, merged). One Copilot round, 4 findings (runbook command args, fixture manifest scope, dev builds cannot qualify, revalidation halts rather than falling back), all fixed in `c9c417d4`.
* Closure via cascade (engine VERIFIED, backlogit 1.11.0); 222-S archived `shipped`.

## Failed approaches and slips

* The full unittest suite takes about 35 min on this host, and the pre-push hook runs it on every push.
* `backlogit commit` is not a CLI command, so task commit tracking was not recorded. `autoharness telemetry begin/record` was skipped.
* `gh api graphql` through PowerShell: pass thread IDs as plain strings with `-f id="$id"`.

## Learnings

* Copilot checks the runbook against CLI argument contracts and gate semantics; check the `--help` of any documented command.

## Follow-ups

* None.
