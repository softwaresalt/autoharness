---
title: "Agent and skill frontmatter conformity contract"
description: "Codify one canonical frontmatter contract for agents and skills (skills carry no model-routing keys; agents carry tier-routed keys and never a bare model key). Enforce it fail-closed on autoharness-managed artifacts and advisory on workspace-authored ones, add tune migration proposals for legacy bare model keys, and remediate the nonconformities found by a repository-wide audit."
doc_type: plan
status: reviewed
review_record: docs/reviews/2026-09-27-agent-skill-frontmatter-conformity-plan-review.md
created: 2026-09-27
source_stash: EF96B695
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
requires_plan_hardening: "yes"
---

# Agent and skill frontmatter conformity contract

## Problem Frame

The backlogit workspace reported that after auto-tune, `sqlite-reviewer` and
`go-mcp-expert` still declared a bare `model:` key outside tier routing (P-013,
P-013.4, P-013.5). The read-only audit behind deliberation F-B1 through F-B4 found
four things.

* Those two agents come from no autoharness template. They are workspace-authored.
  Tune correctly preserved them, but it had no detector, so it neither flagged nor
  proposed anything.
* No autoharness template or mirror has a bare `model:` key, and no skill has any
  model-routing key.
* autoharness itself does have nonconformities:
  * `templates/community/agents/adr-generator.agent.md.tmpl` has no routing keys;
  * `.github/agents/auto-tune.agent.md` and `.github/agents/auto-mergeinstall.agent.md`
    have no routing keys;
  * 18 skill templates and 13 installed skills have no `name:`.
* `src/autoharness/verify_workspace.py` checks routing frontmatter on the three
  pipeline agents only (`_add_frontmatter_model_routing_check`). No contract module
  exists.

## Requirements Trace

| # | Requirement (stash `EF96B695` open questions / D-B*) | Unit(s) |
|---|---|---|
| R1 | Canonical contract for agents vs skills (Q2, D-B1) | B1 |
| R2 | Verify fails closed on managed artifacts and warns on workspace-authored ones (Q3, D-B2) | B2a |
| R3 | Tune proposes migration of legacy `model:`, respecting preservation (Q4, D-B3) | B2b, B5 |
| R4 | Repository-wide audit as a permanent test, plus remediation (Q5, D-B4) | B3, B4 |
| R5 | Answer Q1 (template origin) durably | B6 (docs), deliberation F-B1 |
| R6 | Plugin-distributed agents conform without vendor leakage, and P-013.4 stays unambiguous (hardening H-B1, review AS-F4 / AN-F6) | B1, B3, B7 |

## Implementation Units

### B1 — Frontmatter contract module

* **Files:** `src/autoharness/frontmatter_contract.py` (new), and
  `tests/test_frontmatter_contract.py` (new).
* **Changes:**
  * Key sets (H-B5; concretized from the audit of 21 agent templates, 18 installed
    agents, 42 skill templates, and 19 installed skills):
    * The routing keys are split into two shared constants (AS-F6, AN-F5):
      * `TIER_KEYS = {max_subagent_tier, subagent_depth}`;
      * `ROUTE_VALUE_KEYS = {model_family, model_provider, reasoning_effort}`, plus
        the review-route keys matching
        `^(anchor|alt)_review_(family|provider|reasoning_effort)$`;
      * `ROUTING_KEYS = TIER_KEYS ∪ ROUTE_VALUE_KEYS`.
      * Plan C adds `context_tier` to `ROUTE_VALUE_KEYS` only. That single edit makes
        it optional on `tier-routed` agents, forbidden on `plugin-global` agents, and
        forbidden on skills.
    * Agent profile `tier-routed` (every agent except plugin-global ones):
      `AGENT_REQUIRED = {name, description, max_subagent_tier, subagent_depth,
      model_family, model_provider, reasoning_effort}`. `AGENT_OPTIONAL` is `{id,
      maturity, tools, argument-hint, handoffs, target}`, plus the rest of
      `ROUTE_VALUE_KEYS`.
    * Agent profile `plugin-global` (H-B1, AN-F6):
      * `{name, description, max_subagent_tier, subagent_depth}` are required;
      * every key in `ROUTE_VALUE_KEYS` is **forbidden** (`FM_FORBIDDEN_KEY`), and
        that includes the review-route keys and, after Plan C, `context_tier`;
      * `AGENT_OPTIONAL` minus `ROUTE_VALUE_KEYS` is allowed.
      * No automatic route resolution is claimed for these agents. Their invocation
        mechanism is covered in B3.
    * `AGENT_FORBIDDEN = {"model"}` applies to both profiles.
    * `SKILL_REQUIRED = {name, description}`. `SKILL_OPTIONAL = {argument-hint,
      input, license, compatibility, metadata, allowed-tools}`.
      `SKILL_FORBIDDEN = ROUTING_KEYS ∪ {model}`.
    * Skill `name` must be a string, equal the parent directory name, and match
      `^[a-z0-9]+(-[a-z0-9]+)*$` with at most 64 characters. All 46 current skill
      directories conform.
    * The profile sets are **not** stored module-level literals. They are computed
      at call time by `agent_key_sets(profile)` and `skill_key_sets()` from the
      constants, so Plan C extends the contract only by adding a member to
      `ROUTE_VALUE_KEYS` (AS-F6, cycle 2). There is no separate `AGENT_OPTIONAL`
      edit. The B→C extension test monkeypatches an extra key into
      `ROUTE_VALUE_KEYS`, calls the functions, and asserts three results:
      optional on `tier-routed`, `FM_FORBIDDEN_KEY` on `plugin-global`, and
      `FM_FORBIDDEN_KEY` on skills.
  * `parse_frontmatter(text, mode)` is deterministic (H-B6):
    * it strips a UTF-8 BOM and normalizes CRLF;
    * the first line must be exactly `---`, and the closing delimiter is the first
      later line that is exactly `---` (trailing whitespace allowed). A substring
      match such as `\n---` is not enough, because it would also match `----`;
    * leading and interleaved `#` comment lines are tolerated, because YAML allows
      them and the community README requires attribution comments;
    * it uses a duplicate-key-rejecting safe loader, a `yaml.SafeLoader` subclass
      whose mapping constructor raises on a repeated key (PY-F1). The audit found
      0 duplicate keys across the 100 in-scope files;
    * missing, unclosed, invalid, duplicate-key, non-mapping, and undecodable
      frontmatter all give `FM_PARSE_ERROR`, with a sub-reason. It never raises.
  * Placeholder semantics (H-B6):
    * *template mode*: before parsing, each `{{NAME}}` token is replaced with an
      inert sentinel string, and the keys that carry a placeholder are recorded.
      Presence is still enforced for those keys, but their type validators are
      skipped;
    * *installed mode*: any `{{...}}` in any frontmatter value gives
      `FM_UNRESOLVED_PLACEHOLDER`. The walk is recursive, so nested values such as a
      skill's `input:` mapping are included (PY-F1).
  * `check_agent(fm, profile, mode)` and `check_skill(fm, directory_name, mode)`
    return a list of `Finding(code, key, message, informational: bool)`. `Finding` is
    a frozen dataclass, and the list is sorted by `(code, key)` (PY-F4).
  * The parser catches only `OSError`, `UnicodeDecodeError`, and `yaml.YAMLError`.
    Any other exception is a programming error and propagates to B2a's per-file
    guard (PY-F2).
  * Finding codes:
    * `FM_PARSE_ERROR`, `FM_MISSING_REQUIRED`, `FM_FORBIDDEN_KEY`, `FM_BARE_MODEL`,
      `FM_TYPE_INVALID`, `FM_UNRESOLVED_PLACEHOLDER`, and `FM_PATH_ESCAPE` (emitted
      only by B2a) are non-informational;
    * `FM_UNKNOWN_KEY` is informational only (INV-B4).
    * A `model` key on any artifact gives exactly one `FM_BARE_MODEL`. It never also
      gives `FM_FORBIDDEN_KEY`, so each key gets exactly one code.
  * Agent routing types, for parity with `_add_frontmatter_model_routing_check`
    (INV-B3):
    * `max_subagent_tier` is an int from 1 to 3;
    * `subagent_depth` is a non-negative int;
    * `bool` is rejected for both, because Python's `bool` subclasses `int`;
    * `model_family` is a non-empty string;
    * `model_provider` and `reasoning_effort` are strings that may be empty;
    * `name` and `description` are non-empty strings. A YAML 1.1 coercion such as
      `name: yes` gives `FM_TYPE_INVALID`.
  * Per-key validators live in a registry (`VALIDATORS: dict[str, Callable]`), so
    Plan C can add the `context_tier` enum validator without restructuring.
  * Template sources (`*.tmpl`) are checked in template mode, and installed files
    are checked in installed mode.
  * `agent_profile_for(path, plugin_agents)` returns `plugin-global` when the path is
    in the root `plugin.json` `agents[]`, and `tier-routed` otherwise. verify (B2a)
    and the conformity test (B3) share this one selector.
  * The module is read-only and imports no verify or tune code. The existing verify
    frontmatter helpers are **not** refactored in this plan (INV-B3, scope).
* **Tests:**
  * a bare `model:` gives `FM_BARE_MODEL`, and so does a list-valued `model:`;
  * a skill with `model_family` gives `FM_FORBIDDEN_KEY`, and so does a skill with
    `anchor_review_family`;
  * a missing skill `name` gives `FM_MISSING_REQUIRED`, and a skill `name` that
    differs from its directory gives `FM_TYPE_INVALID`;
  * a template placeholder is allowed in template mode and rejected in installed
    mode. This includes an unquoted leading placeholder, which would otherwise parse
    as a YAML flow mapping;
  * a `plugin-global` agent with `model_family` gives `FM_FORBIDDEN_KEY`;
  * `max_subagent_tier: true` gives `FM_TYPE_INVALID`;
  * a duplicate key, a closing `----` delimiter, BOM or CRLF input, and
    non-mapping YAML each give the expected `FM_PARSE_ERROR`, or parse cleanly
    where valid;
  * a parity table runs the fixtures `model_family: false/42/[]/{}`,
    `model_provider: 42`, and an unresolved placeholder through both B1 and
    `_add_frontmatter_model_routing_check`, and asserts the same pass/fail verdict.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### B2a — verify_workspace integration: classification and managed fail-closed / workspace-authored advisory

Split from the original B2 by the 2-hour rule (H-B10). The migration proposals move
to B2b.

* **Files:** `src/autoharness/verify_workspace.py` (one new check function, its
  single registration call site, and a two-line `info:` branch in
  `_write_markdown_report`), and `tests/test_verify_workspace_frontmatter_conformity.py`
  (new).
* **Changes:**
  * `_add_frontmatter_conformity_check(report, workspace_path, autoharness_home,
    manifest, profile)` is registered once, **after** the existing artifact
    checksum and staging-render loop, so the staged render candidates that B2b
    validates already exist (AN-F10). It scans two sets of files (H-B7):
    * `*.agent.md` under every directory returned by the existing
      `_resolve_agent_scan_dirs(workspace_path, profile)`. That is
      `.github/agents/**`, plus the configured `distribution.local_agents_dir`
      (default `.github/local-agents`) for a global tool, with that helper's
      existing workspace-relative and no-`..` guard reused (AN-F9);
    * `.github/skills/*/SKILL.md`, the skill roots only. A `SKILL.md` nested inside
      a skill's own resources is not scanned.
  * Scan rules (H-B7):
    * the order is sorted and deterministic;
    * each path is resolved, and containment is checked before the new check reads
      the file (AS-F5, cycles 1 and 2):
      * an escaping path that is *managed* gives the non-informational finding
        `FM_PATH_ESCAPE` and fails closed (`ok: false`). It is never skipped;
      * an escaping *untracked* path is skipped with a `warnings[]` entry;
      * in both cases the new check never reads the escaping target's bytes.
      * This guarantee covers the new check only. The pre-existing manifest and
        community checksum scans already read manifest-tracked bytes before this
        check runs. That pre-existing containment gap is not introduced by this
        plan, and fixing it would change the checksum scan, which is outside stash
        EF96B695. It is recorded as a P-021 C1 out-of-scope residual, with a
        follow-up stash entry carried to harvest;
    * a missing directory gives zero files, and that is not a failure;
    * the check writes nothing;
    * any exception is caught per file and becomes `FM_PARSE_ERROR`, so a bad file
      can never crash verification. The per-file guard catches `Exception`, never
      `BaseException`, and records the exception type name. The file still fails
      closed if it is managed (PY-F2).
  * If `plugin.json` is present but unreadable or invalid, the check adds one
    `warnings[]` entry and treats the plugin-agent set as empty. This is fail-safe,
    because plugin agents are then held to the stricter `tier-routed` profile
    (PY-F5).
  * Artifact class, derived from the manifest (H-B2):
    * *managed-rendered*: an `artifacts[].path` whose `template` resolves via
      `_resolve_source_template` to mode `template` or `copy`, **and** whose
      resolved source file exists inside `autoharness_home/templates/`. A label that
      is merely suffix-shaped (for example an arbitrary `*.md` label) without an
      existing contained source is not ownership evidence, so it becomes
      unknown-provenance (AN-F4, cycle 2). Its `checksum_status` is the existing
      artifact status;
    * *managed-community*: a `community_templates[].installed_path`. Its
      `checksum_status` is computed from `installed_checksum`, giving `unchanged`,
      `user-modified`, or `checksum-untracked`, and its source is
      `template_path` (AS-F7);
    * *managed-source*: an `artifacts[].path` whose `template` label is in the
      positive allowlist `AUTOHARNESS_SOURCE_LABELS = {"global agent definition",
      "global skill definition"}`. These are autoharness's own source-controlled
      artifacts (AN-F4);
    * *workspace-authored*: an untracked path, or a template label in
      `WORKSPACE_SOURCE_TEMPLATES`;
    * *unknown-provenance*: any other tracked path whose `template` label neither
      resolves nor is in either set, such as `workspace-discovery output` or a
      label that a target workspace added itself. It is treated like
      workspace-authored (advisory, never fail-closed), but under its own
      `status: nonconformant-unknown`, so the operator can review it. Ownership is
      never assumed (AN-F4);
    * paths are compared as normalized POSIX workspace-relative strings.
  * Agent profile (H-B1, AN-F8): `plugin-global` applies only to a confirmed
    autoharness-distributed plugin agent. Three conditions must all hold:
    * the workspace manifest has `install_mode: "self-install"`, which means
      autoharness is verifying itself. The manifest field is used rather than a
      path-equality test, because `autoharness_home` may be passed as an installed
      package location;
    * the workspace-root `plugin.json` has `name: "autoharness"`;
    * the path is listed in its `agents[]`.
    Any other `plugin.json`, such as one belonging to an unrelated plugin project,
    is ignored, and every agent there uses `tier-routed`.
  * Result shape, which reuses the existing report channels (H-B4; verify has no
    `advisories[]` key):
    * `targeted_checks["frontmatter_conformity"] = {ok, errors[], files: {path:
      {class, profile, checksum_status, findings[]}}}`;
    * `ok` is `false` when any *managed* file (rendered, community, or source) has
      a non-informational finding, whatever its checksum status (`unchanged`,
      `user-modified`, or `checksum-untracked`; H-B3). `errors[]` lists
      `path: CODE key`;
    * a *workspace-authored* or *unknown-provenance* file with a non-informational
      finding produces one `report["warnings"]` entry per file, `{kind:
      frontmatter-conformity, path, class, codes[], message}`. It never changes `ok`;
    * `FM_UNKNOWN_KEY` appears only in the per-file `findings[]`. It never goes into
      `warnings[]` or `errors[]` (INV-B4).
    * Markdown parity (AN-F2):
      * the existing renderer already prints every `errors[]` string, and dumps
        unrecognized warning kinds as JSON;
      * the check entry also carries `info[]` (`path: FM_UNKNOWN_KEY key`). B2a adds
        a two-line branch to `_write_markdown_report` that prints `info:` for any
        targeted check that has it (cycle 2);
      * a test asserts that every JSON `errors[]`, `info[]`, and frontmatter-
        conformity warning entry appears in `verify-workspace-report.md`.
  * The new check's classes apply to the new check only (AS-F1, INV-B3):
    * the existing pipeline-agent checks (`*_model_routing_fields`, which run only
      when the file exists, and `orchestrator_tier_fields`, which is unconditional)
      are left intact, keep their keys, and are not reclassified;
    * a workspace without the pipeline agents can therefore still fail overall
      verify because of those legacy checks. The runtime proofs assert on
      `targeted_checks.frontmatter_conformity`, not on the overall exit code.
* **Tests (all use manifest fixtures):**
  * a managed skill with a routing key fails;
  * a managed, `user-modified` agent with `model:` fails (H-B3);
  * a managed-source (`global skill definition`) skill without `name` fails;
  * a workspace-authored agent with `model: gpt-x` passes, with exactly one warning;
  * a tracked agent labelled `workspace-discovery output`, with an unknown label,
    or with a suffix-shaped label whose source does not exist under
    `autoharness_home/templates/`, is `unknown-provenance`. It gives a warning, and
    never `ok: false` (AN-F4);
  * a `plugin.json` with a different `name`, or in a workspace whose manifest is not
    `install_mode: self-install`, does not select `plugin-global` (AN-F8);
  * the JSON `errors[]`, `info[]`, and frontmatter-conformity warnings appear in
    the Markdown report (AN-F2);
  * an agent with only an unknown key passes, with no warning (INV-B4);
  * a symlink that escapes the workspace is skipped with a warning when untracked,
    and gives `FM_PATH_ESCAPE` with `ok: false` when managed (AS-F5). The test is
    `skipif` when the platform cannot create symlinks, for example Windows without
    developer mode (PY-F3);
  * a file that cannot be decoded gives `FM_PARSE_ERROR` without crashing the check;
  * a workspace without `.github/agents` gives `frontmatter_conformity.ok == true`
    with zero files. Overall verify may still fail on the legacy
    `orchestrator_tier_fields` check, and the test asserts at check level (AS-F1);
  * a managed nonconformant agent in a configured `local_agents_dir` of a
    global-tool profile fails the check (AN-F9);
  * a `plugin-global` fixture (a `plugin.json` listing the agent) passes with
    `max_subagent_tier` and fails with `model_family`;
  * the three existing `*_model_routing_fields` results are byte-identical before
    and after the new check is registered (INV-B3);
  * the dogfood integration pin: `verify_workspace` on this repository gives
    `targeted_checks.frontmatter_conformity.ok == true`. It lands in this unit,
    which runs after B3 and B4 (H-B10).
* **Posture:** test-first. **Size:** M. **Complexity:** medium.
* **Harvest note (2-hour rule):** harvest decomposes B2a into two ordered subtasks:
  1. the classification, profile-selection, and containment helpers, with their
     unit tests;
  2. the check integration, the result shape, the Markdown `info:` branch, the
     INV-B3 byte-identity test, and the dogfood pin.

### B2b — verify_workspace migration proposals and release note

* **Files:** `src/autoharness/verify_workspace.py` (one proposal-builder function
  called from the B2a check), `tests/test_verify_workspace_frontmatter_proposals.py`
  (new), and `CHANGELOG.md` (the release note, H-B11).
* **Changes:**
  * Migration proposals go into `report["migration_proposals"]`. Each proposal
    carries the complete payload (AN-F1):
    * `contract: frontmatter-conformity`, `path`, `from_version: null`, and
      `to_version: "fc-1"`;
    * `status`: `nonconformant-managed`, `nonconformant-workspace`, or
      `nonconformant-unknown`, according to the artifact class;
    * `severity`: `P1` for a managed file (verify fails closed, and tune treats it as
      **Breaking**), and `P2` for workspace-authored or unknown-provenance files
      (tune treats these as **Degrading**);
    * `changed_fields`, `action`, `manual_review`, `evidence` (the finding codes and
      the P-013.x citation), `code`, `from_key`, `to_keys`, and `value`. `value` is
      `null` whenever it cannot be inferred deterministically;
    * `summary`: `"<path>: <action> <from_key> -> <to_keys> [manual review]"`. The
      existing Markdown renderer prints `summary`, which gives operator parity
      without a renderer change (AN-F2).
  * Action rules, one per finding code (AS-F2, AS-F3, AN-F3). They are evaluated in
    this order, and the first rule that matches wins:
    1. Source regeneration is offered only when it would actually fix the file
       (AS-F8, AN-F10). The **rendered candidate** is validated with B1 in
       *installed* mode. Template-mode validation alone is not enough, because it
       skips the type checks on placeholder-bearing values:
       * for an `artifacts[]` file, the candidate is the staged render that verify
         already writes under the staging directory, via `_render_template` with
         `_compose_artifact_variables`;
       * for a community file, the candidate is an in-memory render of
         `template_path` using the same variables. Nothing is written. Before that
         read, `autoharness_home / template_path` is resolved, and it must exist
         inside `autoharness_home/templates/`. That uses the same relative-path and
         no-escape rule as the existing community scan, and it applies even when
         `source_checksum` is empty. A path that fails containment is never read,
         and gives `source-repair` with `manual_review: true` and the containment
         failure in `evidence`. The file still fails closed in B2a (AS-F9);
       * an `artifacts[]` managed-rendered file with `checksum_status: unchanged`,
         whose rendered candidate passes, gets `rerender` with
         `manual_review: false`;
       * a managed-community file with `checksum_status: unchanged`, whose
         rendered candidate passes, gets `reinstall-community` with
         `manual_review: false`. Tune executes this through its existing
         community-template reinstall path (AS-F7);
       * if the rendered candidate fails B1, or cannot be produced, the action is
         `source-repair`, with `manual_review: true`, `value: null`, and the
         template path and the candidate's findings in `evidence`. A re-render would
         only reproduce the defect;
       * in each case, no operator edit exists to discard (H-B3).
    2. `FM_BARE_MODEL` on a `tier-routed` agent:
       * a string value with no `model_family` gets `migrate-key`, with
         `to_keys: [model_family]` and the value copied;
       * a string value equal to an existing `model_family` gets `remove-key`;
       * a list value, or a value that differs from an existing `model_family`, gets
         `migrate-key` with `value: null`;
       * `model_provider` is **never** inferred (H-B6).
    3. `FM_BARE_MODEL` on a skill or a `plugin-global` agent gets `remove-key`. No
       migration is offered, because the target keys are themselves forbidden
       there (AS-F2).
    4. `FM_FORBIDDEN_KEY` gets `remove-key`. For a skill, the evidence cites the
       P-013.5 leaf-executor rule.
    5. `FM_MISSING_REQUIRED` gets `add-key`. The value is deterministic only for a
       skill's `name` (the directory name). Otherwise it is `null` (AS-F3).
    6. `FM_TYPE_INVALID` gets `replace-value`. The value is deterministic only for a
       skill `name` that does not match its directory. Otherwise it is `null`.
    7. `FM_UNRESOLVED_PLACEHOLDER` gets `replace-value` with `value: null`.
    8. `FM_PARSE_ERROR` and `FM_PATH_ESCAPE` get `manual-fix` with `value: null`.
  * Every action other than `rerender` and `reinstall-community` has
    `manual_review: true`, so tune never applies it without per-proposal operator
    approval (INV-B1).
  * `CHANGELOG.md` gains the release note: verify now fails closed on managed agent
    and skill frontmatter nonconformity, and the remediation is a re-render or the
    emitted proposal. It also states that the edited templates cause expected
    template drift in target workspaces (H-B8).
* **Tests:**
  * a table-driven case for each rule from 1 to 8, across the classes
    managed-rendered (`unchanged` and `user-modified`), managed-community
    (`unchanged` and `user-modified`), managed-source, workspace-authored, and
    unknown-provenance (AN-F3, AS-F7);
  * an unchanged managed file whose rendered candidate fails B1 in installed mode
    gets `source-repair`, never `rerender` or `reinstall-community`. This includes
    a template that passes template mode but renders an invalid value, such as a
    `max_subagent_tier` placeholder that resolves to a non-int (AS-F8, AN-F10);
  * a community `template_path` that escapes `autoharness_home/templates/` is never
    read, and gives `source-repair`. That holds even when `source_checksum` is empty
    (AS-F9);
  * idempotence (AS-F7): a community fixture after reinstall produces no
    frontmatter-conformity proposal, with a conformant installed file and both
    `installed_checksum` and `source_checksum` refreshed. The check is `ok`, and the
    existing community scan reports no drift;
  * a skill with `model:` and a `plugin-global` agent with `model:` each get
    `remove-key`, never `migrate-key` (AS-F2);
  * a managed-source skill without `name` gets `add-key` with `value: <dir>` and
    `manual_review: true` (AS-F3);
  * a workspace-authored `model: gpt-x` gets `migrate-key` with
    `to_keys: [model_family]`, `value: gpt-x`, and no provider;
  * `status`, `severity`, and `summary` are exact for each class;
  * every proposal carries the complete payload field set;
  * each proposal's `summary` appears in the Markdown report (AN-F2);
  * verify performs no file writes outside the staging directory.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### B3 — Agent template and dogfood agent remediation, plus the template conformity test

* **Files:** `templates/community/agents/adr-generator.agent.md.tmpl`,
  `.github/agents/auto-tune.agent.md`, `.github/agents/auto-mergeinstall.agent.md`,
  `.autoharness/harness-manifest.yaml` (only those two entries' checksums and notes),
  and `tests/test_template_frontmatter_conformity.py` (new; the agents half).
* **Changes:**
  * `adr-generator` gains the tier-routed keys. The values mirror the quoting of the
    existing agent templates:
    * `max_subagent_tier: 2` and `subagent_depth: 0`;
    * `reasoning_effort: "{{TIER_2_REASONING_EFFORT}}"`, `model_provider:
      "{{TIER_2_PROVIDER}}"`, and `model_family: "{{TIER_2_FAMILY}}"`. These are
      variables from the install-harness variable table, and the template gains no
      literal family or provider (INV-B2);
    * `templates/community/README.md` § Source attribution requires the attribution
      comments to stay *inside* the YAML frontmatter, so they remain as the leading
      comment lines. B1 tolerates them (H-B9).
  * The two dogfood agents are the plugin-distributed global agents in
    `plugin.json` `agents[]`. Every plugin user installs them verbatim, so they take
    the `plugin-global` profile (H-B1):
    * they gain `max_subagent_tier: 2` and keep their existing `subagent_depth: 2`.
      This is Stage-recommended, pending operator confirmation (AS-F4);
      * both agent bodies already declare "This agent operates at **Tier 2
        (Standard)**" in their Model Routing section (auto-tune line 160,
        auto-mergeinstall line 220). That supersedes the earlier recommendation of
        Tier 3 for auto-tune;
      * `max_subagent_tier` is the subagent-dispatch ceiling that P-013.4 requires.
        It is **not** the agent's own tier, and this plan does not use it to select
        the agent's own model;
    * they must **not** gain any key in `ROUTE_VALUE_KEYS`. Resolving this
      repository's config values into them (`claude-opus-5.5` / `anthropic`) would
      ship one workspace's vendor route to every plugin user, which breaks the
      no-hardcoded-provider guardrail of
      `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` in
      spirit;
    * **Invocation mechanism (AN-F6, AS-F4):** the earlier claim that "their route
      resolves from the invoking workspace's config" is withdrawn, because nothing
      implements it:
      * `plugin.json` only lists files;
      * these agents are operator-invoked entry points, never
        Orchestrator-dispatched, so they run on the host session's operator-selected
        model;
      * their base tier is the body's Model Routing declaration. B3's test asserts
        that each plugin-global agent body contains exactly one `operates at
        **Tier N` statement with `N` from 1 to 3. The test does **not** relate `N` to
        `max_subagent_tier`, which is the independent subagent-dispatch ceiling of
        P-013.2 (AS-F4, cycle 2);
      * automatic route resolution for plugin agents is not in scope. If it is ever
        wanted, it is a separate stash entry.
  * The new test runs B1 in template mode over every `templates/**/*.agent.md.tmpl`
    (which includes `templates/community/agents/`), and in installed mode over
    `.github/agents/**/*.agent.md`. It selects the profile from the root
    `plugin.json` `agents[]`, via B1's `agent_profile_for(path, plugin_agents)`.
  * The test adds a render assertion: `adr-generator` is rendered through
    `verify_workspace._render_template`, using the variables from
    `_derive_template_variables` for a fixture workspace and config. The result must
    have no unresolved `{{...}}` placeholders and must pass B1 in installed mode
    (H-B9).
    * Verify only checksum-compares community templates and never renders them, so
      this test is the guard that the `TIER_2_*` variables resolve for a community
      agent.
    * If the install-harness community render path is found to lack `TIER_2_*`
      variables, B3 halts and the gap is reported. It is not patched in this plan.
* **Tests:** the new conformity test is RED before the edit and GREEN after. The RED
  list is recorded: 1 template and 2 installed agents.
* **Posture:** characterization-first (record the RED list). **Size:** S.
  **Complexity:** low.

### B4 — Skill `name:` remediation, plus the skills half of the conformity test

* **Files:**
  * the 18 `templates/skills/*/SKILL.md.tmpl` files that lack `name:`. All 13
    community skill templates already have it;
  * the 13 installed `.github/skills/*/SKILL.md` files that lack `name:`. Nine are
    template-rendered, and four are `global skill definition` sources:
    install-harness, tune-harness, verify-harness, and workspace-discovery;
  * the matching 13 `artifacts[]` checksums in `.autoharness/harness-manifest.yaml`.
    Templates are not manifest entries (H-B8);
  * `tests/test_template_frontmatter_conformity.py` (the skills half).
* **Changes:**
  * Add `name: <directory-name>` as the first frontmatter key of each file, after
    any leading YAML comment lines. The change is mechanical.
  * For each of the nine template-rendered installed skills, the installed edit is
    byte-identical to the template edit, so render parity is preserved (H-B8).
    Byte-identity is judged on the LF-normalized staged blob. In the working tree,
    65 of the 100 in-scope files are checked out with CRLF (CR-F1).
  * The skills half of the test asserts `name` equals the directory name, and that no
    forbidden routing key is present.
  * Checksums are refreshed from the raw staged blob (IM-12).
* **Tests:**
  * the conformity test (skills half) is RED before and GREEN after. The RED list is
    recorded: 18 templates and 13 installed skills;
  * the existing mirror-parity tests stay green;
  * a manifest-checksum assertion confirms that the 13 refreshed entries match their
    staged blobs.
* **Posture:** characterization-first.
* **Size:** M (many files, one mechanical change, no logic). The volume exceeds the
  "fewer than 3 files" heuristic, but the change is a single, trivially verifiable
  edit repeated per file, and the test enumerates completion.
* **Complexity:** trivial.

### B5 — tune-harness and verify-harness skill guidance for frontmatter drift

* **Files:** `.github/skills/tune-harness/SKILL.md`, `.github/skills/verify-harness/SKILL.md`,
  and their two `artifacts[]` checksums in `.autoharness/harness-manifest.yaml`. Both
  are `global skill definition` entries (H-B8). Also `tests/test_frontmatter_conformity_guidance.py`
  (new). This unit owns its own test file, to avoid a three-way edit of the B3/B4
  test.
* **Changes:**
  * Tune gains a "Step 1.5c: Frontmatter Conformity Migration" section, modelled on
    Step 1.5b (agent identity), plus the matching mapping line in Step 2.2:
    * it promotes each `contract: frontmatter-conformity` proposal from verify, and
      preserves the **complete** B2b payload. That is the Step 0b.2 field set plus
      `path`, `code`, `from_key`, `to_keys`, `value`, `manual_review`, and `summary`
      (AN-F1);
    * `severity: P1` / `status: nonconformant-managed` maps to **Breaking**, and
      `P2` (workspace-authored or unknown provenance) maps to **Degrading**;
    * the execution semantics for each action are defined:
      * `rerender` uses the normal managed re-render path;
      * `reinstall-community` uses the existing community-template reinstall path,
        and refreshes **both** `installed_checksum` and `source_checksum` of the
        `community_templates[]` entry, so that the next verify reports neither a
        conformity finding nor community drift (AS-F7);
      * `source-repair` and `manual-fix` are report-only. `source-repair` names the
        defective autoharness template;
      * `migrate-key`, `remove-key`, `add-key`, and `replace-value` perform a
        single-key frontmatter edit that preserves the body;
      * `manual-fix` is report-only;
      * a `null` `value` requires the operator to supply one before applying;
    * `migrate-key` and `remove-key` proposals are never applied without per-proposal
      operator approval (INV-B1). This covers every `manual_review: true` proposal,
      and every workspace-authored or user-modified file;
    * a `model:` → `model_family` migration never invents `model_provider`;
    * a skill with routing keys gets a proposal to remove them, citing the P-013.5
      leaf-executor rule.
  * verify-harness documents the `frontmatter_conformity` targeted check:
    * its managed-rendered, managed-source, and workspace-authored classes;
    * the `tier-routed` and `plugin-global` profiles;
    * fail-closed regardless of checksum status (H-B3);
    * `FM_UNKNOWN_KEY` is informational.
* **Tests:**
  * a structural test asserts that the new tune section and its Step 2.2 mapping
    exist;
  * it asserts that the section names all eight actions and the complete preserved
    payload field list, includes the phrases "operator approval" and "never invents
    `model_provider`" (AN-F1), and states that `reinstall-community` refreshes both
    community checksums (AS-F7);
  * it asserts that the verify-harness check description names both classes and
    both profiles;
  * the manifest checksums match.
* **Posture:** docs/skill only. **Size:** S. **Complexity:** low.

### B6 — Contract documentation

* **Files:** `docs/tuning-guide.md` (a section on the frontmatter contract and
  migration), and `docs/ARCHITECTURE.md` (a short pointer to the contract module).
* **Changes:**
  * the agent vs skill key tables, including the shared `ROUTING_KEYS` constant and
    both agent profiles;
  * the managed-rendered, managed-source, and workspace-authored semantics;
  * the F-B1 answer: workspace-authored agents such as `sqlite-reviewer` are
    preserved and reported, not rewritten;
  * the plugin-global rule (H-B1, AN-F6): plugin-distributed agents declare only
    `max_subagent_tier` (the subagent ceiling) and their body tier statement. They
    run on the operator's session model, and no automatic route resolution is
    claimed for them.
* **Tests:** markdownlint.
* **Size:** S. **Complexity:** trivial.

### B7 — P-013.1 / P-013.4 plugin-global clarification (AS-F4, AN-F6)

* **Files:** `templates/policies/workflow-policies.md.tmpl` (§ P-013.1 and
  § P-013.4), `.github/policies/workflow-policies.md` (the installed mirror), its
  `artifacts[]` checksum, and `tests/test_frontmatter_conformity_guidance.py` (one
  assertion added to B5's file).
* **Changes:**
  * Each of P-013.1 and P-013.4 gains one clarifying sentence. Their MUST
    statements are unchanged.
  * P-013.1:
    * plugin-distributed agents are shipped verbatim and never install-rendered;
    * their tier binding is documented only in their persona prose ("operates at
      Tier N");
    * they run on the operator-selected session model;
    * the existing rule that they must not request a lower- or higher-capability
      model than that tier still applies (AS-F4, cycle 2).
  * P-013.4: the "install-resolved route values" sentence applies to installed
    (`tier-routed`) agents only. Plugin-distributed agents declare
    `max_subagent_tier` and no route-value frontmatter.
  * No other policy text changes.
* **Tests:** a structural assertion that both clarifications are present and
  identical in the template and the mirror, and that the P-013.1 and P-013.4 MUST
  sentences are byte-unchanged.
* **Posture:** docs/policy only. **Size:** XS. **Complexity:** trivial.
* **Downstream note:** Plan C's C6 edits the same file (P-013.5 / P-013.6). The two
  edits are in disjoint sections, so the only interaction is a rebase.

## Dependency Graph

B1 → B3 → B4 → B2a → B2b → B5 → B6 → B7 (H-B10).

* B2a's dogfood integration pin requires B3 and B4, so B2a follows them. This
  replaces the earlier wording ("enabled in B4's final commit"), which contradicted
  the harvest order.
* B2b depends on B2a's check.
* B5 documents B2a and B2b.
* B6 documents everything.
* B7 depends on B5, because it adds an assertion to B5's test file.

Linear harvest order: B1, B3, B4, B2a, B2b, B5, B6, B7.

## Decisions and Rationale

Deliberation D-B1 through D-B4 (Stage-recommended, pending operator confirmation).

* A single contract lives in code, so the tests, verify, and tune share one
  definition.
* Managed files fail closed and workspace-authored files are advisory, which honors
  preservation.
* Tune proposes and never applies.
* The Ship and Stage role-variable binding is handed to C (D-C6).
* `context_tier` is added to the shared `ROUTING_KEYS` constant by C, not here.
  That makes it agent-optional and skill-forbidden in one edit (H-B5).
* D-B5 (hardening H-B1, amended by review AS-F4 / AN-F6; Stage-recommended, pending
  operator confirmation): agents distributed through `plugin.json` take the
  `plugin-global` profile.
  * They declare `max_subagent_tier` (the subagent ceiling, `2` for both) and no
    route-value keys.
  * Their base tier is the body's Tier statement, and they run on the operator's
    session model.
  * The rejected alternative, literal values from this repository's config, would
    leak one workspace's vendor route to every plugin user.
* D-B6 (hardening H-B3; Stage-recommended, pending operator confirmation): managed
  findings fail closed whatever the checksum status, and only the remediation
  differs. The rejected alternative downgrades `user-modified` managed files to
  advisory. That keeps previously green installs green, but lets an operator-added
  bare `model:` in a managed agent through, and that is the defect class this plan
  exists to catch.

## Risks and Caveats

* **Verify now covers every manifest-tracked agent and skill in target workspaces,
  and a previously green install could go red.** Mitigation: the only new
  fail-closed codes are ones autoharness itself renders. A red result means a real
  defect in a managed artifact, fixed by re-render. The release note must state it.
* **Manifest checksum churn:** 13 entries in B4, 2 in B3, and 2 in B5. Templates are
  not manifest entries, so the earlier estimate of about 33 was wrong (H-B8).
  Mitigation: mechanical commits, with checksums taken from the raw staged blob.
* **Template-source drift in target workspaces:** the 18 skill templates and
  `adr-generator` change, so the next tune in each target workspace reports
  expected template drift. For community templates, that is `source_checksum`
  drift. The B2b release note states this (H-B8).
* **Plugin vendor leakage (H-B1):** closed by the `plugin-global` profile, which
  forbids route-value keys in the agents in `plugin.json`.
* **Pre-existing, out of scope:** `.github/skills/` is plugin-distributed, and its
  template-rendered skills carry this repository's rendered variables. This plan
  adds only `name:`, and no routing keys, so it does not widen that exposure. A
  follow-up stash entry is Stage-recommended.
* **Overlap with 196-S (render parity) and 164-S** (template variables). These are
  merge conflicts only, and Ship rebases.
* **The community README convention for attribution comments:** resolved (H-B9).
  The attribution comments stay inside the frontmatter, and B1 tolerates them.
  Leaf agents use `max_subagent_tier` 1-2 and `subagent_depth: 0` (16 of 20
  templates).

## Plan Hardening Signals

* Contract change — **present** (a new verification contract across all agents and
  skills).
* Security — absent.
* Migration — **present** (tune migration proposals; mass frontmatter edit).
* External integration — absent. Operator checkpoint — **present** (migration
  approval).
* Rollout risk — **present** (verify strictness in target workspaces).

Requires plan hardening: yes

## Runtime Verification and Closure

* B2a and B2b change the `autoharness verify-workspace` runtime surface.
* Environment precheck: `autoharness --version` resolves to the working-tree
  install. Each scratch workspace is created under the OS temp directory with a
  minimal `harness-manifest.yaml`, and is removed afterwards.
* Runtime proof (H-B11). Each scenario asserts on
  `targeted_checks.frontmatter_conformity`, `warnings[]`, and
  `migration_proposals[]`, **not** on the overall exit code. Scratch workspaces lack
  the pipeline agents, so the legacy `orchestrator_tier_fields` check fails there
  independently (AS-F1). The exit code is recorded for information only:
  1. run `autoharness verify-workspace --json` on this repository. It must give
     `frontmatter_conformity.ok: true`, and it must introduce no new overall
     failure compared with a pre-change baseline run that Ship captures before B2a;
  2. run it on a scratch workspace containing a hand-written agent with
     `model: gpt-x`. The check must give `ok: true`, with one
     `frontmatter-conformity` warning and a `migrate-key` proposal that has no
     provider;
  3. run it on a scratch workspace where a manifest-tracked skill gains
     `model_family`. The check must give `ok: false`, with a `remove-key` proposal
     marked `manual_review: true`;
  4. run it on a scratch workspace with a manifest-tracked, unchanged agent that
     lacks `model_family`. The check must give `ok: false`, with a `rerender`
     proposal;
  5. run it on a scratch workspace with no `.github/agents`. The check must give
     `ok: true` with zero files.
* Blocked path: if the CLI cannot run, record `RUNTIME_VERIFICATION_BLOCKED` with
  the error, and do not close. The unit tests alone do not substitute for runtime
  proofs 1 and 3.
* Closure records all five outcomes, as command, exit code, and relevant JSON
  excerpt.

## Plan Hardening

* **Hardening required:** yes.
* **Learnings and instructions consulted:**
  * `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` (skills
    inherit their route; no hardcoded provider IDs in templates);
  * `docs/compound/p013-orchestrator-model-routing.md`;
  * `.github/skills/tune-harness/SKILL.md` (override preservation, rules 1-2);
  * `constitution.instructions.md`.
* **Protected invariants:**
  * INV-B1: tune never rewrites a workspace-authored file without operator approval.
  * INV-B2: no template gains a hardcoded provider or family string.
  * INV-B3: the existing `pipeline_agent_model_routing` checks keep their semantics.
  * INV-B4: `FM_UNKNOWN_KEY` is never fail-closed.
* **ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Mass-edit 31 skill files, plus 13 checksums | low | Plan-review PASS; mechanical, and test-enumerated |
  | New fail-closed verify check | medium | Release note (B2b); managed scope only |
  | Tune migration proposals | low | Per-proposal operator approval (unchanged tune posture) |

* **Rollback:** remove B2a's single registration call to disable the check. B2b's
  proposals disappear with it, because they are built only from B2a's results. The
  B3 and B4 edits are harmless metadata.
* **Monitoring:** the first tune run in the backlogit workspace after release must
  show `sqlite-reviewer` / `go-mcp-expert` proposals. Ship records it as a follow-up
  observation, not a gate.
* **Review-gate capability risk:** superseded by Hardening Pass 2 (H-B12).
* **Unresolved operator decisions:**
  * D-B1 through D-B4 (Stage-recommended);
  * the tier value for the two dogfood agents in B3. The Stage recommendation,
    amended by review AS-F4, is `max_subagent_tier: 2` for both, matching their
    body "Tier 2" declarations;
  * Hardening Pass 2 adds D-B5 and D-B6.

### Hardening Pass 2

Stage ran pass 2 on 2026-09-27 against `deb0564b`. It verified the plan's audit
claims against the code and repository, and all of them reproduced: 1 template and 2
installed agents lack routing keys, 18 skill templates and 13 installed skills lack
`name:`, and there are 0 bare `model:` keys. It also found the gaps below, and each
fix is cited inline by its ID.

| ID | Gap found | Fix applied |
|---|---|---|
| H-B1 | `auto-tune` and `auto-mergeinstall` are listed in `plugin.json` `agents[]` and ship verbatim to every plugin user. "Resolve values from this repository's config" would hardcode `claude-opus-5.5` / `anthropic` globally | `plugin-global` profile: tier keys only, and the route-value keys are forbidden (B1, B2a, B3, B6; D-B5) |
| H-B2 | "Tracked in the manifest" was undefined. Community agents live in `community_templates[]`, not `artifacts[]`, and 11 `artifacts[]` entries are `global … definition` labels that never render | Three classes: managed-rendered, managed-source, and workspace-authored. The rules are derived from `_resolve_source_template` and `WORKSPACE_SOURCE_TEMPLATES` (B2a). Review later extended this to five classes: managed-community (AS-F7) and unknown-provenance (AN-F4) |
| H-B3 | The effect of checksum status (`user-modified`) on fail-closed was unspecified, and "re-render" would discard operator edits | Fail closed regardless of checksum status. `rerender` only when `unchanged`; otherwise key-level `manual_review` proposals (B2a, B2b; D-B6; INV-B1 extended) |
| H-B4 | verify has no `advisories[]` key, and tune promotes proposals by `contract:`, not `source:` | Use `targeted_checks`, `warnings[]`, and `migration_proposals[]` with `contract: frontmatter-conformity`, and the tune Step 0b.2 field set (B2a, B2b) |
| H-B5 | The key sets were unnamed. The audit found `maturity`, `tools`, `id`, `argument-hint`, `input`, and the review-route keys (`anchor_/alt_review_*`) | Concrete sets, a shared `ROUTING_KEYS` constant, and the skill-name grammar (B1) |
| H-B6 | Parser edge cases: the `\n---` substring match, BOM/CRLF, duplicate keys, `bool` passing as `int`, unquoted leading placeholders, list-valued `model`, and an "unambiguous provider" rule that was not deterministic | A deterministic parser, `FM_PARSE_ERROR`, sentinel substitution, and "never infer the provider" (B1, B2b) |
| H-B7 | Scan bounds: the recursive skills glob, symlink escape, a missing directory, and crash safety | Skill roots only; containment; per-file exception capture (B2a) |
| H-B8 | The checksum churn estimate (about 33) counted templates, which are not manifest entries. B5 edits two `global skill definition` files but listed no checksums. Target-workspace template drift was unstated | 13 + 2 + 2 checksums, render parity, and the release note (B3, B4, B5, B2b) |
| H-B9 | The adr-generator attribution-comment placement was open. Verify never renders community templates, so a `TIER_2_*` resolution gap would go undetected | Keep the comments in the frontmatter (README § Source attribution); add a render assertion with a halt-and-report fallback (B3) |
| H-B10 | B2 exceeded the 2-hour rule once hardened, and the dependency text contradicted the harvest order | Split into B2a and B2b; corrected the linear graph |
| H-B11 | The runtime proof had three scenarios, no environment precheck, no blocked path, and no release-note owner | Five scenarios, a precheck, a blocked path, and `CHANGELOG.md` in B2b |
| H-B12 | "Review-gate capability risk: same as Plan A" was not self-contained | See the next list |

* **H-B12, the review-gate capability risk:**
  * plan-review must emit the literal markers `dispatch_mode:` and `decision:` in
    the plan's `## Plan Review` section;
  * this Stage runtime has no reviewer-subagent tool, so review runs under the
    declared degradation
    `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`;
  * the cross-model personas run as independent, write-denied external passes on
    the anchor route, following the precedent in
    `docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md`;
  * harvest must halt if the markers are missing, or if any selected persona is
    uncovered.
* **Protected invariants added:**
  * INV-B5: no plugin-distributed agent carries a route-value key.
  * INV-B6: the verify check never writes outside the staging directory, and never
    crashes on a malformed file.
* **INV-B1 extended:** tune also never re-renders or key-edits a `user-modified`
  managed file without per-proposal operator approval.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Review record: `docs/reviews/2026-09-27-agent-skill-frontmatter-conformity-plan-review.md`.
  It is authoritative for findings, dispositions, and persona coverage.
* Gate: **PASS** under severity rule C4, with 0 open P0 and 0 open P1. It came after
  three review-fix cycles and a bounded fix-verification pass confined to the
  cycle-3 fixes. Found: 2 P0, 17 P1, 5 P2, 6 P3. Open: 1 P2 and 1 P3, both accepted
  residuals.
* Plan hardening was required and is satisfied (the original record plus Hardening
  Pass 2).
* Persona coverage, all six selected personas:
  * inline passes: Constitution, Python, Scope Boundary, and Learnings;
  * independent anchor-route passes (`gpt-6-sol`, external Copilot CLI with
    `write` denied): Architecture Strategist and Agent-Native Parity;
  * Security Lens was not triggered: the plan has no auth, secrets, API, or
    external-integration surface;
  * declared degradation: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared
    fallback: single-agent persona pass`.
* Stage-recommended decisions pending operator confirmation:
  * D-B1 to D-B6;
  * the B3 tier value of `max_subagent_tier: 2` for both plugin agents;
  * the B7 clarifying text for P-013.1 and P-013.4.
* Downstream contract impacts on
  `docs/plans/2026-09-27-context-tier-model-routing-plan.md`. They are recorded
  here; that plan was not edited:
  1. C5 adds `context_tier` to `frontmatter_contract.ROUTE_VALUE_KEYS`, not to
     `AGENT_OPTIONAL`, which is not a stored literal. That makes it optional on
     `tier-routed` agents and forbidden on `plugin-global` agents and on skills. The
     enum validator is registered through `VALIDATORS`.
  2. C5's file list must include `templates/community/agents/adr-generator.agent.md.tmpl`,
     which is tier-routed after B3, with `{{TIER_2_CONTEXT_TIER}}`. C5's
     conformity-test extension must be scoped to the `tier-routed` profile.
  3. C5 must not add `context_tier` to `.github/agents/auto-tune.agent.md` or
     `.github/agents/auto-mergeinstall.agent.md` (`plugin-global`; INV-B5).
  4. C4 and C5 template edits must pass B2b's rendered-candidate validation
     (installed mode), not only template mode.
  5. C6 and B7 both edit `workflow-policies.md`, in disjoint sections, so they only
     need a rebase. C6's P-013.5 `context_tier` wording should exclude
     plugin-distributed agents, which run on the operator's session model.
