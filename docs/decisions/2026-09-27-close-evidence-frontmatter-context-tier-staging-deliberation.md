---
title: "Stage deliberation: CASCADE close-evidence capture, agent/skill frontmatter conformity, and context_tier routing"
description: "Triage, grouping, sequencing, and per-entry decisions for stash entries 008F3BCF (automatic fail-closed CASCADE close evidence), EF96B695 (agent/skill frontmatter conformity), and 6EC29DD6 (context_tier on model_routing plus a new generic Ship default, with a binding dogfood Ship pin)."
doc_type: deliberation
status: decided
created: 2026-09-27
decided: 2026-09-27
operator_rulings: "2026-09-27T22:50-07:00 - items 1-4 confirmed; item 5 overrides (Ship context_tier long_context, Ship template max_subagent_tier 3)"
source_stash:
  - 008F3BCF
  - EF96B695
  - 6EC29DD6
produced_plans:
  - docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md
  - docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md
  - docs/plans/2026-09-27-context-tier-model-routing-plan.md
prior_learnings:
  - docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md
  - docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md
  - docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md
  - docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md
  - docs/compound/p013-orchestrator-model-routing.md
---

# Stage deliberation: close evidence, frontmatter conformity, context_tier

## Session context

* Stage session 2026-09-27 (`stage next`, Orchestrator depth 1, autopilot, not dark mode).
  Operator not present. Every open-question decision below is a **Stage recommendation,
  pending operator confirmation**. None is decided silently.
* Tool gate: `TOOL_OK: backlogit` (MCP), `INDEX_SYNC_OK` (1520 indexed),
  `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`. Discovery used
  file search over the repository at `deb0564b`.
* Crash-resumption: 67 `stage` checkpoints enumerated with no filter, 0 anomalies,
  0 active candidates. Normal start.
* None of the three entries carries the `DEFERRED SCOPE EXPANSION` marker, so the
  P-021 C6 forced-deliberate precedence and the C5 duplicate/reconciliation duties do
  not apply. A duplicate scan of the active stash for `shipment ship`, `returned_ids`,
  `model:`, `frontmatter`, and `context_tier` found no duplicate of any of the three.

## Triage

| Stash | Kind | Priority | One-line summary | Route |
|---|---|---|---|---|
| `008F3BCF` | bug | high | CASCADE close evidence is agent-discretionary prose; 175-S lost its raw close output, its classifier re-check, and its out-of-manifest snapshot | deliberate → plan → harden → review |
| `EF96B695` | bug | medium | Frontmatter is not conformant across agents and skills; bare `model:` keys went unflagged by tune in the backlogit workspace | deliberate → plan → harden → review |
| `6EC29DD6` | feature | medium | Add `context_tier` to every model_routing route and to agent frontmatter; new generic Ship default; binding dogfood Ship pin | deliberate → plan → harden → review |

## Findings from read-only investigation

### 008F3BCF

* F-A1. The CASCADE path in `.github/skills/shipment-reconcile/SKILL.md` (Cascade
  Close Sub-Procedure, lines 677-998) makes the agent re-run the classifier,
  fingerprint descendants, call `backlogit_ship_shipment`, and then write a report.
  Every capture step is prose. Nothing deterministic writes the evidence, and
  nothing refuses a closure when the evidence is missing. This is the root cause the
  stash entry names.
* F-A2. `backlogit shipment ship` has no JSON output flag. Its only structured
  channel is the global `--jsonrpc` envelope. There is no evidence-emission option.
* F-A3. The `closure-evidence` gate (`src/autoharness/cli.py` about lines 1681-1918,
  contract in `src/autoharness/gates/closure_contract.py`) validates the closure
  artifact's name and its `closure_status` / `compaction_status` frontmatter. It
  does not know which close path ran.
* F-A4. The safe operation primitives (fixed-argv exec, bounded reader, atomic
  write) are planned in 179-F / 185-S. 185-S is **unclaimable by construction**:
  it is blocked by the withheld, archived 184-S. A dependency on it would park this
  high-priority bug indefinitely.
* F-A5. The circuit-breaker instruction already fixes log bounds (capture up to
  1 MiB or 10,000 lines; inspect at most the final 64 KiB or 500 lines; persist only
  redacted summaries). The evidence file reuses those numbers rather than inventing
  new ones.
* F-A6. Closure discovery reads regular entries of `docs/closure/` only (175-S
  lesson 2). A subdirectory is not a closure candidate.

### EF96B695

* F-B1. Neither `sqlite-reviewer` nor `go-mcp-expert` is produced by any autoharness
  template. No template, mirror, or installer row names them. The only generated
  technology reviewer is `{{PRIMARY_LANGUAGE_LOWER}}-reviewer`, which renders to
  `go-reviewer` for a Go workspace. Both agents are therefore workspace-authored or
  externally sourced. Tune left them alone, which the override-preservation rule
  requires. The defect is that tune neither flagged nor proposed anything for them.
  This answers open question (1).
* F-B2. No file under `templates/` or `.github/` carries a bare `model:` frontmatter
  key. No skill (template or mirror) carries any model-routing key.
* F-B3. Real nonconformities that autoharness owns:
  * `templates/community/agents/adr-generator.agent.md.tmpl` has no
    `model_family` / `model_provider` / `reasoning_effort` / `max_subagent_tier` /
    `subagent_depth`. Its frontmatter also begins with `#` comment lines ahead of
    `name:`.
  * `.github/agents/auto-tune.agent.md` and `.github/agents/auto-mergeinstall.agent.md`
    (manifest-tracked) have no routing keys.
  * 18 skill templates and 13 installed skills have no `name:` key.
  * `templates/agents/_ship.agent.md.tmpl` renders its frontmatter from
    `{{TIER_2_*}}` and `_stage.agent.md.tmpl` from `{{TIER_3_*}}`, not from the P-013.5
    role variables (`{{SHIP_*}}` / `{{STAGE_*}}`). The installed dogfood
    `_ship.agent.md` says `claude-opus-5.5` / `anthropic` and `max_subagent_tier: 3`,
    so it is a hand-maintained divergence from its own template. A clean re-render
    would produce `claude-sonnet-5` (tier2) and `max_subagent_tier: 2`.
* F-B4. `verify_workspace` checks `model_family` / `model_provider` on the three
  pipeline agents only (`_add_frontmatter_model_routing_check`). It checks no other
  agent, no skill, and no bare `model:` key.

### 6EC29DD6

* F-C1. Every route object in `schemas/harness-config.schema.json` has
  `additionalProperties: false`. A config that declares `context_tier` today fails
  schema validation. `schema_version` is `const: "1.1.0"`. F02FD596 added the nested
  escalation routes without bumping it.
* F-C2. `templates/harness-config.yaml.tmpl` carries only placeholders. Its defaults
  live in the install-harness variable table. Today `{{SHIP_FAMILY}}` defaults to
  `claude-sonnet-5` via the tier2 fallback, and `{{SHIP_PROVIDER}}` and
  `{{SHIP_REASONING_EFFORT}}` default to empty. Core Rule 3 and the P-013.5
  guardrail (compound 2026-08-01) forbid hardcoding provider or family strings in
  `.tmpl` files.
* F-C3. The ESCALATION_DEGRADED same-route guard compares the resolved tuple
  `(model_family, model_provider, reasoning_effort)`. The both-present ambiguity rule
  (`definitions/nonEmptyRouteFields`) fires when both the flat and the nested
  escalation declare any non-empty routing field.
* F-C4. `tests/test_template_variable_derivation_contract.py` pins installer-table
  row numbers (for example "SKILL.md row 434") and the `claude-sonnet-5` Ship default.
* F-C5. Per F-B3, re-installing this repository would silently move the installed
  Ship agent off `claude-opus-5.5`. The operator's binding clarification therefore
  needs a code change, not only a config value.

## Grouping analysis (Step 1.5)

| Option | Covering features | Tasks (est.) | Coherence | Risk | Disposition |
|---|---|---|---|---|---|
| **G1** | Three features, three shipments, sequenced A → B → C | 7 + 6 + 7 | Each feature is one contract surface: close-path evidence; frontmatter contract; routing schema. B defines the contract that C extends. | medium per unit | **Selected (Stage-recommended)** |
| G2 | A alone; B and C merged | 7 + 13 | B and C share agent frontmatter | high: one PR mixes a bug fix with schema evolution; about 26 hours of task budget | Rejected |
| G3 | All three in one feature | 20 | Weak: A shares no surface with B or C | high | Rejected |

## Decisions

Each decision is **Stage-recommended, pending operator confirmation** unless it is
marked as a binding operator ruling.

> **Update (2026-09-27T22:50-07:00):** the operator has confirmed every decision below,
> with two overrides (5a and 5b). See
> [Operator rulings](#operator-rulings-2026-09-27t2250-0700).

### Portfolio

* **D-P1 — Grouping G1.** Three covering features, one shipment each. Rationale:
  the table above. Width isolation holds and each PR stays reviewable.
* **D-P2 — Order A → B → C.**
  * A (`008F3BCF`) is a `dag-root`. It has no technical predecessor (F-A4 rules out
    185-S). Every later shipment's closure runs through the P-015 path, so fixing
    it first pays off on every subsequent closure. The operator also asked for it
    first.
  * B blocks-on A. This is an ordering edge (operator priority and one-at-a-time Ship
    execution), not a technical dependency. It is recorded as such, so a later Stage
    may relax it if A stalls.
  * C blocks-on B. This is a technical edge. C adds `context_tier` to the frontmatter
    contract that B codifies, and C's re-render proofs use B's conformity checker.
* **D-P3 — No edges to or from existing queued shipments, and none are modified.**
  Known merge-conflict (not logical) overlaps: C and 164-S both touch the
  install-harness variable table and its row-pinned test. C, 196-S, and 197-S all
  touch agent templates and manifest checksums. Ship rebases and re-derives row
  references and checksums at claim time. Blocking C on 164-S would park it behind a
  six-shipment chain for a conflict that a rebase resolves.

### 008F3BCF — automatic, fail-closed CASCADE close evidence

* **D-A1 — The wrapper lives in autoharness (open question: autoharness vs upstream).**
  Add a new mutating CLI command group, `autoharness shipment cascade-close`. It runs
  the fresh classifier revalidation, the out-of-manifest and linked-deliberation
  snapshot, and the baseline fingerprints. It writes the pre-close evidence
  atomically **before** it invokes anything. It then invokes backlogit through a fixed
  argv with `shell=False` and a timeout, captures stdout, stderr, and the exit code
  within bounds, writes the post-close evidence, and evaluates the deterministic
  postconditions. Those are `returned_ids == []`, the two-set
  `allowed_ids` / `required_ids` gate, `parent_id` preservation, and descendant
  baseline invariance. The command is not under `gate`, because gates are read-only
  (the `closure-evidence` help text says so). The upstream half is a portable
  backlogit feature request (native `--json` result plus a pre-close state
  snapshot / `--evidence-out` on `shipment ship`). Ship writes it as a docs-only task.
  It **does not block** this feature, and the wrapper parses the existing
  `--jsonrpc` envelope in the meantime.
* **D-A2 — Retention and location (open question: how long, and where).** The
  evidence is one JSON record per closure at
  `docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json` (renamed
  from the pre-review `-cascade-close-evidence.json` by plan review, because the
  record now serves both close paths; the plan is authoritative).
  It is committed with the closure artifact and kept for the same lifetime,
  permanently and version-controlled. That is the 175-S lesson: the record must
  outlive the session. The directory sits under `docs/closure/`, so the 167-F closure
  discovery never classifies it (F-A6), and a regression test pins that. The
  persisted content is bounded per F-A5:
  * stdout and stderr are each captured up to 1 MiB or 10,000 lines;
  * the persisted excerpt is the final 64 KiB or 500 lines, with a truncation flag,
    the total byte count, and a SHA-256 of the full capture;
  * any value that matches the redaction set (tokens, `Authorization`, `password=`,
    and similar) is replaced before writing.
  The raw capture beyond the excerpt is never persisted.
* **D-A3 — SAFE_CLOSE (open question: does it need the same capture).** It gets
  partial parity. The same command's `--classify-only` mode records the fresh
  classifier verdict and the out-of-manifest snapshot for SAFE_CLOSE, and exits
  without mutating. SAFE_CLOSE's per-item `move` / `archive` sequence is **not**
  wrapped in this feature, for two reasons: each of its steps can be re-verified
  after the fact, and it is many commands rather than one non-reproducible cascade.
  The `closure-evidence` gate therefore **fails closed** for CASCADE without a valid
  evidence record, and, as amended by plan review cycle 1 (AN-F01, Stage-recommended,
  pending operator confirmation), **also fails closed** for SAFE_CLOSE without a
  valid verdict record; the pre-review draft only warned for SAFE_CLOSE. Wrapping
  SAFE_CLOSE's per-command outputs is a follow-up (`AE33E3E3`) and is not staged here.
* **D-A4 — The gate needs a machine-readable close path.** New closure artifacts
  must declare `close_path: cascade | safe_close`, plus `close_evidence: <path>`
  for either path (renamed from the pre-review `cascade_evidence`, which covered
  CASCADE only). The write-time `closure-evidence` gate fails closed
  when:
  * `close_path` is missing on a new artifact;
  * a CASCADE evidence record is missing, malformed, or for a different
    shipment or feature;
  * the record has no post-close section;
  * the record's own postcondition verdict is not `pass`.
  The only exception is a finalized `BLOCKED` record, where the existing tolerance
  still applies (175-S lesson 4). Already-committed closure artifacts are never
  re-gated. The pipeline-topology consumer that reads closure artifacts is **not
  changed**.
* **D-A5 — The skill becomes a pointer to the command.** On the CASCADE path,
  `shipment-reconcile` must invoke `autoharness shipment cascade-close`, and a
  direct `backlogit_ship_shipment` MCP or CLI call becomes a P-005 deviation. The
  skill keeps the HALT vocabulary and maps each wrapper exit code to it.
* **D-A6 — The contract stays in code.** The evidence contract is a Python module
  with a validator, following the 167-F precedent (the 2026-09-17 OQ-2 deferred
  moving the closure frontmatter into `schemas/`). Adding a `schemas/` file would
  add schema-evolution blast radius for no consumer outside autoharness.

### EF96B695 — agent/skill frontmatter conformity

* **D-B1 — The canonical contract (open question 2).** One code module defines it.
  * **Agents** (`*.agent.md`):
    * Required: `name`, `description`, `max_subagent_tier` (int 1-3),
      `subagent_depth` (int), `model_family` (non-empty string),
      `model_provider` (string, may be empty), `reasoning_effort` (string, may be
      empty).
    * Optional: `id`, `maturity`, `tools`, the anchor / alt review keys (on
      designated reviewer agents only), and `context_tier` (added by C).
    * Forbidden: bare `model`.
  * **Plugin-global agents** (amended by plan review, D-B5, Stage-recommended,
    pending operator confirmation): `auto-tune` and `auto-mergeinstall`, which the
    self-install `plugin.json` `agents[]` ships verbatim to every plugin user, require
    `name`, `description`, `max_subagent_tier` (2 for both), and `subagent_depth`,
    and **forbid** the route-value keys (`model_family`, `model_provider`,
    `reasoning_effort`, `context_tier`) as well as bare `model`. The route-value
    requirement above applies to tier-routed agents only.
  * **Skills** (`SKILL.md`):
    * Required: `name`, `description`.
    * Optional: `argument-hint`, `input`.
    * Forbidden: `model`, `model_family`, `model_provider`, `reasoning_effort`,
      `context_tier`, `max_subagent_tier`, `subagent_depth`. Skills are P-013.5 leaf
      executors that inherit their route.
  * Unknown keys are reported, not rejected. That keeps the contract from breaking
    on harmless metadata.
* **D-B2 — Fail-closed vs warn (open question 3).** Fail closed on
  **autoharness-managed** artifacts, meaning files tracked in
  `.autoharness/harness-manifest.yaml` (and templates in this repository's own
  tests). Warn with an advisory finding and a `migration_proposals[]` entry on
  **workspace-authored** artifacts that the manifest does not track. autoharness
  owns what it generates. Failing verification on files it does not own would
  contradict override preservation.
* **D-B3 — Tune migration posture (open question 4).** Tune proposes and never
  auto-applies. For a workspace-authored agent with a bare `model:` key, tune emits a
  migration proposal: map it to `model_family`, infer `model_provider` only when the
  value is unambiguous, and otherwise leave it empty and let the tier/role route
  resolve it. The proposal needs operator approval, and tune never rewrites the file
  without it. Managed artifacts are fixed by re-render. This answers why the backlogit
  auto-tune run changed nothing and said nothing: no detector existed.
* **D-B4 — Audit remediation scope (open question 5).** This feature fixes:
  * the community `adr-generator` template, which gains tier-routed placeholders
    (Tier 2, the documented default for authoring agents);
  * the two routing-less dogfood agents (`auto-tune`, `auto-mergeinstall`), which
    are managed;
  * the 31 skills without a `name:`.
  The Ship/Stage template role-variable binding (F-B3, last bullet) is handed to C
  (D-C6), because it only becomes load-bearing with the new Ship default. The dogfood
  Ship `max_subagent_tier: 3` vs template `2` divergence is recorded as a finding and
  **not changed** here. That is an operator-tuned behavior value. A low-priority
  follow-up is stashed to decide it.
  * **Resolved by operator ruling 5b (2026-09-27T22:50-07:00).** The operator chose
    stash option (b): `templates/agents/_ship.agent.md.tmpl` changes its literal
    `max_subagent_tier: 2` to `3`, matching the installed mirror. The change is folded
    into 194-F (C4a, task `194.005-T`), which already rewrites the Ship template
    frontmatter. This feature (193-F) still does not change it. Stash `F9F40F94` is
    archived as consumed.

### 6EC29DD6 — context_tier routing

* **D-C1 — Allowed values (open question a).** A closed, provider-agnostic enum:
  `""` (unset → fallback), `default`, `long_context`. The labels name a context
  capacity class, not a vendor product, so Core Rule 3 holds. A runtime that cannot
  honor `long_context` records `ROUTING_DEGRADED` (P-013.5) and proceeds at the
  default context. That never halts. New values are a later additive schema change.
* **D-C2 — Fallback semantics (open question b).** Per field, matching P-013.5 and
  P-013.6:
  * a role route resolves role → its fallback tier (stage → tier3, ship → tier2) →
    `default`;
  * a nested per-role escalation resolves `<role>.escalation` → tier3 → `default`,
    never the legacy flat route (F02FD596);
  * the legacy flat escalation resolves flat → tier3 → `default`;
  * a tier resolves tier → `default`.
* **D-C3 — The same-route guard does not compare context_tier (open question c).**
  P-013.6 escalation is a reasoning escalation. The same family, provider, and effort
  with a larger context window is not a genuine escalation, so it must still read as
  ESCALATION_DEGRADED. By the same reasoning, `context_tier` does **not** join
  `definitions/nonEmptyRouteFields`. Otherwise the rendered default in both escalation
  blocks would make every install schema-ambiguous. Escalation blocks render
  `context_tier: ""` (inherit).
* **D-C4 — The new Ship default applies to new installs only (the part of open
  question d still open for other workspaces).** The install-harness variable-table
  defaults become `SHIP_PROVIDER=openai`, `SHIP_FAMILY=gpt-6-luna`,
  `SHIP_REASONING_EFFORT=xhigh`, `SHIP_CONTEXT_TIER=long_context`. The template keeps
  its placeholders. For existing installs, tune never auto-migrates. It emits an
  informational, opt-in proposal **only** when the workspace's `model_routing.ship`
  route declares no explicit `model_family`, that is, when Ship is still riding the
  tier2 fallback. An explicitly declared Ship route is an operator choice, and tune
  never proposes replacing it.
* **D-C5 — Schema version and compatibility (open question e).** No
  `schema_version` bump. The field is optional and additive. Configs without it stay
  valid and resolve to `default`. F02FD596 is the precedent, and bumping a `const`
  would invalidate every existing config.
* **D-C6 — BINDING operator ruling (2026-09-27T13:18:02-07:00), implemented durably.**
  This repository's Ship route stays `claude-opus-5.5` / `anthropic`. Here is how it
  survives re-install and tune.
  1. `_ship.agent.md.tmpl` and `_stage.agent.md.tmpl` frontmatter bind to the role
     variables (`{{SHIP_*}}`, `{{STAGE_*}}`, plus `*_CONTEXT_TIER`). Their per-field
     fallback to tier2/tier3 preserves today's output for any workspace without a
     role route. A re-render of this repository then yields `claude-opus-5.5` from
     `config.model_routing.ship`, instead of `claude-sonnet-5` from tier2 (F-C5).
  2. `.autoharness/config.yaml` keeps its explicit `model_routing.ship`
     (`claude-opus-5.5` / `anthropic` / `high`) and gains `context_tier: "default"`.
     The explicit route **is** the override record, and D-C4 already exempts it from
     tune proposals.
     **Amended by operator ruling 5a (2026-09-27T22:50-07:00):** the Ship
     `context_tier` value is `"long_context"`, not `"default"`. The installed
     `.github/agents/_ship.agent.md` gains `context_tier: "long_context"`, and the
     point-3 regression test pins `long_context` for Ship. Stage, the tiers, and the
     orchestrator keep `"default"`.
  3. A dogfood regression test pins four things: the config Ship route, the installed
     `_ship.agent.md` frontmatter, the render of the Ship template under this
     repository's config, and the absence of any tune or verify drift finding for the
     divergence from the template default.
  4. `overrides:` is **not** used. It is a template-variable map, and a second source
     of truth would invite conflicts.
  The Ship `context_tier` value here is `default`, because the operator did not
  decide it (per the clarification). *Superseded by operator ruling 5a
  (2026-09-27T22:50-07:00): the operator has now decided it, and the value is
  `long_context`. See the Operator rulings section.*
* **D-C7 — Reviewer routes are deferred.** `anchor_review`, `alt_review`, and
  `alt_doc_review` do not gain `context_tier` in this feature. They resolve into
  reviewer dispatch, not into role-agent frontmatter, and the stash scope lists
  tier / role / escalation routes only.

## Hygiene item (in scope)

Two older Stage documents cite the untracked, now git-ignored
`docs/scratch/2026-09-24-workflow-defects-session-pickup.md`. This session edits only
those two sentences to say the note was a local, untracked handoff that is not
preserved in the repository. The documents' findings are unchanged.

The same defect exists elsewhere and is **listed, not edited**, because those are
reviewed, hash-referenced planning artifacts:

* `docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md`
  lines 38 and 257, citing `docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`;
* `docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md` lines 32, 78, and
  750, citing the same file.

Neither file exists or is tracked.
`docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`
already qualifies its scratch path correctly.

## Residual open questions (for the operator)

> **All four are resolved by the operator rulings of 2026-09-27T22:50-07:00** (see the
> next section). The original questions are kept below as asked.

1. Confirm or override D-P1, D-P2, D-A1 through D-A6 (including the review-cycle-1
   D-A3 amendment: SAFE_CLOSE fails closed), D-B1 through D-B6 (including the
   plugin-global profile and `max_subagent_tier: 2` for both plugin agents), D-C1
   through D-C5, and D-C7. Where a decision above and its reviewed plan differ, the
   plan is authoritative.
   **Resolved:** confirmed (rulings 2, 3, 4).
2. The dogfood Ship `context_tier` stays `default` until the operator chooses.
   **Resolved:** the operator chose `long_context` (ruling 5a).
3. The dogfood Ship `max_subagent_tier: 3` vs template `2` divergence is stashed as a
   low-priority follow-up.
   **Resolved:** the Ship template changes to `max_subagent_tier: 3` (ruling 5b);
   stash `F9F40F94` is archived as consumed.
4. **D-P2 dag-root ruling (pending operator confirmation):** apply `dag-root` to
   198-S and drop the ordering-only 198-S ← 189-S edge? At assembly, 198-S was
   recorded as blocked by 189-S as an ordering placeholder only. D-P2 (and F-A4)
   classify A (`008F3BCF`) as having no technical predecessor. Stage recommends:
   apply `dag-root` and drop the edge. Until the operator rules, the placeholder
   edge stays.
   **Resolved:** confirmed (ruling 1). Stage applied `dag-root` to 198-S and removed
   the 198-S ← 189-S edge.

## Operator rulings (2026-09-27T22:50-07:00)

The operator ruled on the numbered items the Orchestrator presented. Verbatim:

> "Confirm 1-4. 5. Set Ship's context_tier to long_context in the template. Set Ship's max_subagent_tier to 3 in its template."

| Item | Ruling | Decision IDs | Backlog effect |
|---|---|---|---|
| 1 | Confirmed | D-P2 dag-root (Residual open question 4) | 198-S carries `dag-root`; the ordering-only dependency 198-S ← 189-S is removed. 199-S ← 198-S and 200-S ← 199-S are unchanged. |
| 2 | Confirmed | D-A1 to D-A6, including the review-cycle-1 D-A3 amendment (SAFE_CLOSE also fails closed) | 192-F: decisions operator-confirmed; the D-A3 decline fallback is moot. |
| 3 | Confirmed | D-B1 to D-B6, including the plugin-global profile (D-B5) and `max_subagent_tier: 2` for `auto-tune` and `auto-mergeinstall` | 193-F: decisions operator-confirmed; scope unchanged. |
| 4 | Confirmed | D-C1 to D-C5, D-C7, D-C6 (dogfood Ship stays `claude-opus-5.5` / `anthropic`; the Ship and Stage templates bind to the role variables), and D-P1, D-P2, D-P3 | 194-F: decisions operator-confirmed. |
| 5a | Override | D-C6 point 2 (Ship `context_tier` value); Residual open question 2 | Dogfood Ship `context_tier` is `long_context`. 194-F tasks `194.005-T` (C4a) and `194.012-T` (C7) amended. |
| 5b | Override | D-B4 / F-B3 divergence finding; Residual open question 3; stash `F9F40F94` | Ship template `max_subagent_tier` changes from `2` to `3`, folded into `194.005-T` (C4a). `F9F40F94` archived as consumed. |

**Stated assumption for 5a (Orchestrator interpretation, recorded by Stage).** "In the
template" is read with placeholder discipline (Core Rule 3). It does not mean a literal
value in the template.

* `templates/agents/_ship.agent.md.tmpl` keeps the variable binding
  `context_tier: "{{SHIP_CONTEXT_TIER}}"`.
* A fresh install already renders `long_context` for Ship through the D-C4 new-install
  default (the C3b fresh-install seed). Workspaces with a Ship route but no Ship
  `context_tier` still fall back per field under D-C2.
* This repository's `.autoharness/config.yaml` `model_routing.ship.context_tier`
  becomes `"long_context"`, not `"default"`, and the installed mirror
  `.github/agents/_ship.agent.md` gains `context_tier: "long_context"`.
* Stage, tier1-3, and the orchestrator keep `"default"`. The D-C4 new-install defaults
  are unchanged. The D-C6 dogfood regression test pins `long_context` for Ship.

If the operator meant a literal `long_context` in the `.tmpl`, that would break the
role-variable binding D-C6 depends on. Stage did not stage it that way.

**5b.** Line 7 of `templates/agents/_ship.agent.md.tmpl` changes from the literal
`max_subagent_tier: 2` to `max_subagent_tier: 3`. This matches the installed mirror,
which is already `3`, and removes the F-B3 / D-B4 divergence. The frontmatter
contract in 193-F already accepts an int from 1 to 3. The change is generic: every
newly rendered Ship gets `3`, and the 194-F release notes say so.

**Plan amendment.** `docs/plans/2026-09-27-context-tier-model-routing-plan.md` records
5a and 5b as a post-review operator amendment. These are operator rulings, not new
design, so the plan's PASS review is not reopened. One sequencing consequence is
recorded there: the one-line Ship `context_tier: "long_context"` config edit moves
from C7 into C4a, so the installed Ship mirror matches its render under this
repository's config from C4a onward.

## Post-review follow-up stash captures

* `4DA3BCE6`: SBA-F04, the trusted backlogit binary pin in the registry (cascade
  review).
* `4F7B8BA7`: R-1 / HC-3, symlink containment in verify's checksum scan
  (frontmatter review).
* `692727D7`: SB-F1 / HC-2, plugin-distributed `.github/skills/` carrying this
  repository's rendered variables (frontmatter review).
* `BAF15C62` (existing entry, reconciled in place): SB-F1, the tier-1 subagent
  `gpt-5.6-luna` mirror staleness (context-tier review). This is a duplicate of the
  PR #457 capture, so no new entry was created.
