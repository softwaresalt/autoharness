---
type: circuit-breaker
timestamp: 2026-07-28T05:23:00Z
agent: Ship
skill: pr-lifecycle/copilot-review
breaker_type: review-fix-cycle-limit
operation: Copilot P-018 review-fix-push loop for PR #238
attempts: 3
---

# Circuit Breaker — Copilot P-018 review-fix loop (PR #238)

## Failure Chain

### Cycle 1
Copilot review for HEAD `03742c505cc6f89a55fae97f4cc190b50db83736` returned 4 unresolved threads. Fixed schema compatibility, verify-harness domain mapping, adversarial reviewer-count mapping, updated checksum, pushed `8cb5acd`, replied, and resolved threads.

### Cycle 2
Copilot review for HEAD `8cb5acd612ab34de819e0a5f7c50544021ae5466` returned 2 unresolved threads. Fixed anchor reasoning-effort dispatch and PR checksum evidence, pushed `eafdd40`, replied, and resolved threads.

### Cycle 3
Copilot review for HEAD `eafdd40dec8e0de09dbeb0a35986045b64b10f0f` returned 1 unresolved thread. Fixed same-model-declared-degradation marker handling, pushed `7b810c8`, replied, and resolved the thread.

### Post-limit Gate
Copilot review for current HEAD `7b810c8b20420c0b0deb1348df01b7a271e15136` returned 2 new unresolved threads:
- `PRRT_kwDORzpWpM6USCTO`: `.github/skills/verify-harness/SKILL.md` absent-route default probing concern.
- `PRRT_kwDORzpWpM6USCTk`: `templates/agents/adversarial-review.agent.md.tmpl` even-count confidence-tier gap.

## Context
- PR: https://github.com/softwaresalt/autoharness/pull/238
- CI: green on current HEAD.
- Local tests: `python -m pytest -q tests\test_anchor_review_routing.py` passed; `python -m unittest discover -s tests -q` passed.
- Resolution: Review-fix-push cycle limit reached. P-018 gate remains BLOCKED; merge readiness cannot be claimed until current-head Copilot threads are addressed and the gate passes.
- Suggested next steps: Operator may authorize another review-fix cycle, create backlog follow-ups and defer merge, or take over comment resolution manually.
## Authorized Extra Cycle — 2026-07-28T04:39:00Z

Operator authorized exactly one additional bounded review-fix cycle for current-head threads `PRRT_kwDORzpWpM6USCTO` and `PRRT_kwDORzpWpM6USCTk`.

### Fix Commit
- Commit: `1d7e985cb6ad2e9266aa69ff6e8491bd7c7559e8`
- Fixed effective default anchor route probing in `.github/skills/verify-harness/SKILL.md`.
- Fixed plural non-majority confidence classification in `templates/agents/adversarial-review.agent.md.tmpl` and mirrored instruction template.
- Refreshed verify-harness manifest checksum to `e2fe06c688fdc4da43403678791673f5afb333358fce93dbf8b0c243178401ac`.
- Tests passed: `python -m pytest -q tests\test_anchor_review_routing.py`; `python -m unittest discover -s tests -q`.
- CI passed on PR #238 current head.

### Resolved Authorized Threads
- `PRRT_kwDORzpWpM6USCTO` reply id `3662765584`, resolved `true`.
- `PRRT_kwDORzpWpM6USCTk` reply id `3662765704`, resolved `true`.

### New Current-Head Threads After Authorized Cycle
P-018 remains BLOCKED. No further cycle is authorized.

1. `PRRT_kwDORzpWpM6USLqy` / comment `3662780284` (`templates/skills/plan-review/SKILL.md.tmpl`):
> These are not the installed identity paths. Non-top-level agents are installed flat under `.github/agents/subagents/` (`.github/skills/install-harness/SKILL.md:1339` and `templates/foundation/AGENTS.md.tmpl:364-365`). As written, every dispatched persona lookup targets a nonexistent `review/` or `research/` path and forces plan review into degradation/failure. Point all adapter identities at `subagents/`.

2. `PRRT_kwDORzpWpM6USLrL` / comment `3662780313` (`.github/skills/install-harness/SKILL.md`):
> These mappings contradict this same skill's canonical install-path table at line 1339, which installs all non-top-level agents into `.github/agents/subagents/`. Following the new per-persona mappings would recreate the retired categorized layout and make generated skill references disagree with actual output. Use the flat `subagents/` destination consistently.

3. `PRRT_kwDORzpWpM6USLrT` / comment `3662780321` (`tests/test_anchor_review_routing.py`):
> This regression test encodes the retired `review/` and `research/` output layout, so it passes while the generated adapter points to nonexistent installed identities. The canonical output is `.github/agents/subagents/` (`.github/skills/install-harness/SKILL.md:1339`); assert those paths instead so the test catches this routing break.
>
> This issue also appears on line 188 of the same file.

### Current Stop State
- Branch: `feat/091-F-multi-model-review-routing`
- HEAD: `1d7e985cb6ad2e9266aa69ff6e8491bd7c7559e8`
- PR: https://github.com/softwaresalt/autoharness/pull/238
- CI: green
- Copilot P-018 gate: `UNRESOLVED_THREADS`, 3 unresolved threads
- Merge: not attempted; P-014 approval still required and P-018 blocks readiness.

## Final Authorized Cycle — 2026-07-28T04:52:00Z

Operator authorized one last review-fix cycle for the persona install-path cluster.

### Fix Commit
- Commit: `313ea3e5e2c98a19b4f50161d58e04b29628328a`
- Normalized PR-introduced persona identity paths from `.github/agents/review/` and `.github/agents/research/` to canonical `.github/agents/subagents/` in plan-review, install-harness, and regression tests.
- Refreshed install-harness manifest checksum to `4164cccb41d39a948d5f3c7316b393d80e156c513dd703f2fcaf4e0be4218b7c`.
- Tests passed: `python -m pytest -q tests\test_anchor_review_routing.py`; `python -m unittest discover -s tests -q`.
- CI passed on PR #238 current head.

### Resolved Authorized Threads
- `PRRT_kwDORzpWpM6USLqy` reply id `3662815557`, resolved `true`.
- `PRRT_kwDORzpWpM6USLrL` reply id `3662815658`, resolved `true`.
- `PRRT_kwDORzpWpM6USLrT` reply id `3662815759`, resolved `true`.

### New Current-Head Thread After Final Authorized Cycle
P-018 remains BLOCKED. No further cycle is authorized.

1. `PRRT_kwDORzpWpM6USTY4` / comment `3662825511` (`.autoharness/harness-manifest.yaml`):
> The current PR description claims the install-harness checksum is `5be541ba...` and that a raw-byte re-check matched, but the manifest records `4164cccb...`. This reintroduces an inconsistent drift/readiness claim after the earlier checksum correction. Recompute the current file hash and update whichever value is stale before relying on the `unchanged` evidence.

### Current Stop State
- Branch: `feat/091-F-multi-model-review-routing`
- HEAD: `313ea3e5e2c98a19b4f50161d58e04b29628328a`
- PR: https://github.com/softwaresalt/autoharness/pull/238
- CI: green
- Copilot P-018 gate: `UNRESOLVED_THREADS`, 1 unresolved thread
- Merge: not attempted; P-014 approval still required and P-018 blocks readiness.


## Post-Merge Resolution — 2026-07-28T06:32:00Z

PR #238 was merged at 2026-07-28T06:22:42Z with merge commit `42a5d6b9ae6649b997e60efb56f30ea3aae9f4af` using a merge commit. The review-cycle circuit breaker is resolved for shipment 096-S: the final checksum/readiness feedback was addressed before merge, P-018 was satisfied by the time PR #238 merged, and post-merge closure archived the backlog artifacts. Merge approval did not bypass the fail-closed Copilot-review gate. Durable learnings were graduated to `docs/compound/096-S-template-vs-global-skill-placeholders.md` and `docs/compound/096-S-canonical-subagent-install-path.md`.
