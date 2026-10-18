# Upstream autoharness issue request: rendered-template defects found in intercom-go

* **Prepared:** 2026-10-15, from the intercom-go workspace (Orchestrator and Stage session).
* **Carry to:** the autoharness workspace. Stash it there, or file it as an issue against the autoharness repository.
* **Source stash entry in intercom-go:** `40BCCD69`, plus the originals listed per item.
* **Why upstream:** each defect is in a file rendered by `autoharness install` or `tune`: `.github/agents/_ship.agent.md`, `.github/skills/*`, `AGENTS.md`, or the harness manifest. A hand edit in intercom-go is overwritten on the next render and never reaches other workspaces. The fix belongs in the templates (`_ship.agent.md.tmpl`, the skill templates, `AGENTS.md.tmpl`), followed by a re-render here.
* **Priority order:** items 1 and 2 first. Item 1 describes an unsafe step ordering in a destructive close path. Item 2 describes merge-gate wording that understates policy.

## Item 1 (high): shipment-reconcile cascade and safe-close text (stash `F2759510`)

**Files:** `.github/skills/shipment-reconcile/SKILL.md` (template: shipment-reconcile skill) and `_ship.agent.md` (Step 6).

Five wording or contract fixes:

1. **Post-mode HALT ordering (unsafe gap).** Order the steps as: restore, re-run mode `post`, and commit only on `PROCEED`. The current text does not fix this order.
2. **INV-6 predicate.** The cascade sub-procedure "pre-archived" paragraph and the safe-close Step 0(c) parenthetical say "full coverage". P-015 INV-6 states an engine-inertness containment predicate over the `parent_id` descendant set. Align the wording to INV-6.
3. **Canonical key name.** The engine emits `selected_close_path`. The evidence record mirrors it as `pre_close.close_path_selection`. State the mapping once. Use the engine name in prose, and use the record path only when naming the record.
4. **INV-12 and D6 anchors.** Define or correct where these are cited. Part of this finding may be about which text cites them, so check the upstream template before assuming the anchors are missing.
5. **Duplicated step-3 prose.** Remove it.

## Item 2 (high): Ship dark-mode approval text (stash `8E1E2D80`, related `724FA2FB`)

**File:** `_ship.agent.md` (Steps 7b, 14, and 6.1.b.3) and the Orchestrator autonomy text.

P-018 already says the Copilot review gate applies once Copilot is engaged and is "preserved in full" in dark factory mode. The agent text under-states this. These are wording fixes only. They do not change the approval contract.

1. **Steps 7b and 14:** the P-018 Copilot review block applies once Copilot is engaged. The shadow-review timeout is advisory only when Copilot is not engaged.
2. **Step 14:** the dark-mode approval list must include the P-018 PASS requirement.
3. **Orchestrator autonomy text:** per-closure destructive approval is never a routine coordination decision.
4. **Step 6.1.b.3 (`724FA2FB`):** state that a P-014 merge approval, including a "merge approved" message, cannot satisfy the per-closure destructive cascade-close approval. This mirrors the existing closure-PR non-transfer rule. The closure step should ask for the cascade approval explicitly.

## Item 3: NOT an upstream defect (stash `A744E584`): removed from this request

Review of git history showed the upstream template already used the space-separated form (`--message <text>` and `--author <name>`). The `=` form was hand-edited into intercom-go's `_ship.agent.md` and `shipment-reconcile/SKILL.md` during 043-S (commits `2749d5d` and `b5abe5f`). `autoharness shipment cascade-close` rejects it with exit 2. This is a local regression and is being reverted in intercom-go. Nothing to do upstream.

## Item 4 (low): Ship Step 6 item 1.a versus pre-archived members (stash `9B7E94E9`)

Ship Step 6 item 1.a says manifest items must be present in the queue with status `done`. backlogit archives a task when it moves to `done`, so done members are always pre-archived. The shipment-reconcile pre-mode classifies them as pre-archived, and that is valid for `expected_status: done`. Align the Ship text with the skill.

## Item 5 (low): leaked `{{id}}` placeholder (stash `D5D103A1`)

`shipment-reconcile/SKILL.md` line 549 renders the literal `{{id}}` inside the CLI fallback for `backlogit archive`. Use the resolved placeholder convention used elsewhere in the skill. Check the upstream template for the same leak.

## Item 6 (low): wrong field name in operational-closure (stash `0606E72F`)

`operational-closure/SKILL.md` line 25 says that when the closure artifact carries `merge_commit` it must equal the record's `merge_commit_sha`. The canonical closure frontmatter key is `merge_commit_sha`, so the documented equality check may never apply to normal closure artifacts. Have the procedure compare the artifact's `merge_commit_sha` to the evidence record's `merge_commit_sha`.

## Item 7 (low): dead links in `AGENTS.md` (stash `92708A06`)

`AGENTS.md` lines 323, 325, 326 and 327 point to `docs/ARCHITECTURE.md`, `docs/product-specs/`, `docs/QUALITY_SCORE.md` and `docs/references/`. None of these exist in this workspace. Either render the links only when the files exist, or create the files at install time.

## Item 8 (medium): assorted render defects (stash `8134B7B7`)

1. `_ship` agent frontmatter `model_family` and `reasoning_effort` differ from `config.model_routing.ship`.
2. The `_ship` footer names `ship.agent.md.tmpl`, but the upstream file is `_ship.agent.md.tmpl`.
3. `copilot-instructions` and the `_ship` agent cite `scripts/search.ps1`, `search.sh`, `acquire_lock` and `release_lock`, which are not in `scripts/`.
4. intercom references render even though the `agent-intercom` pack is not installed.
5. The `learned-closure-frontmatter-seed` instruction uses an `applyTo` double-star while it is still a proposal. Operator promotion decision pending.
6. The harness-manifest `alt_doc_review` route variables are empty while the config sets a route. The manifest schema predates `context_tier`.
7. The policy row `1.26.0` may collide with an upstream `1.26.0` row on the next sync.

## Related, local only (not part of the upstream request)

* `9C6C2078`: the intercom-go design doc `docs/design-docs/2026-10-11-closure-contract-surface-matrix.md` already shows the correct space form. The entry asks for the `=` form, which is wrong (the engine rejects it), so it is archived as a refuted premise.

## Interim guidance for intercom-go until the re-render lands

Treat every `cascade-close` as needing its own explicit per-closure approval. A dark-mode merge approval is not sufficient for it.
