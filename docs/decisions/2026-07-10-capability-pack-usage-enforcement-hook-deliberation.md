---
title: "Capability-Pack Usage-Enforcement Hook (Generic, engram + graphtor-docs)"
description: "Deliberation for stash items 909F493D (enforce engram usage) and 8EB5C5D8 (similar hook for graphtor-docs). Decides a single reusable capability-pack usage-enforcement overlay: a Pre-Retrieval Routing Protocol instruction plus a deterministic verifier check, weaving through install and tune, rather than two bespoke mechanisms or an unenforceable runtime interceptor."
topic: "How should the harness deterministically enforce that agents actually USE an installed retrieval-oriented capability pack (engram for code/symbol/semantic search; graphtor-docs for documentation/domain-context lookup) instead of silently falling back to grep or web search?"
depth: "significant"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-10-capability-pack-usage-enforcement-hook-deliberation.md
source_stash_ids:
  - "909F493D"
  - "8EB5C5D8"
backlog_items:
  - "075-F"
  - "075.001-T"
  - "075.002-T"
  - "075.003-T"
  - "075.004-T"
  - "075.005-T"
  - "075.006-T"
  - "075.007-T"
linked_artifacts:
  - "templates/instructions/capability-pack-enforcement.instructions.md.tmpl"
  - ".github/instructions/capability-pack-enforcement.instructions.md"
  - "src/autoharness/verify_workspace.py"
  - "tests/test_capability_pack_enforcement.py"
  - "schemas/capability-pack-registry.schema.json"
  - "templates/packs/capability-pack-registry.yaml"
  - "tests/test_capability_pack_registry.py"
  - ".github/skills/install-harness/SKILL.md"
  - ".github/skills/tune-harness/SKILL.md"
  - ".github/instructions/agent-engram.instructions.md"
  - ".github/instructions/graphtor-docs.instructions.md"
  - "docs/capability-packs.md"
tags:
  - "capability-packs"
  - "agent-engram"
  - "graphtor-docs"
  - "enforcement"
  - "verifier"
  - "primitive-6"
---

# Capability-Pack Usage-Enforcement Hook (Generic, engram + graphtor-docs)

## Decision

Build **one reusable capability-pack usage-enforcement overlay**, not two bespoke
per-pack hooks. It combines a soft session-time surface with a hard install-time
surface, plus registry/tune weaving:

1. **Session-time — a Pre-Retrieval Routing *coordinator* instruction (soft
   discipline).** A new technology-agnostic template
   `templates/instructions/capability-pack-enforcement.instructions.md.tmpl`
   (installed mirror `.github/instructions/capability-pack-enforcement.instructions.md`)
   modeled on `role-enforcement.instructions.md`. It is a **thin coordinator**:
   it owns cross-pack query **classification**, **precedence**, **exemptions**,
   and the **deviation-record format**, and it **defers to each pack's own
   instruction** for lifecycle/tool/fallback specifics (the pack instruction
   wins on those details). It defines a routing discipline: for a retrieval
   operation, classify the query, route structural/conceptual code queries to
   engram and indexed documentation/domain/business-context queries to
   graphtor-docs, and reuse a per-phase health check rather than probing before
   every call. **Explicit exemptions** (consistent with the existing pack
   instructions) keep direct tools first-class: literal-text/regex search and
   known exact-path confirmation use grep/read directly; mixed queries may use
   both packs. **Fallback is sensitivity-aware**: on an index miss, public/
   external questions may fall back to web, but **internal business-context
   misses (SoWs, internal docs, process, data-mapping) MUST NOT go to public web**
   — they fall back to approved local/internal sources or request source
   configuration. **Ambiguous sensitivity defaults to internal/no-public-web**
   (fail-closed on exfiltration risk). The routing/exemption table renders **only the enabled**
   packs' rows (delimited by stable markers) so the instruction never points at
   an unavailable tool. Deviations are recorded as **session-output signals**
   (not audited telemetry, which is deferred).

2. **Install/CI-time — a deterministic verifier check (hard coherence).** A new
   `_check_capability_pack_enforcement` in `src/autoharness/verify_workspace.py`
   (modeled on `_check_copilot_code_review_instruction`). Expectedness is driven
   by **enabled retrieval-enforced packs, not manifest membership**: when at
   least one retrieval-enforced pack (`agent-engram`, `graphtor-docs`) is enabled,
   the check **independently requires** (a) the enforcement
   instruction file exists, (b) it is manifest-listed with a checksum that
   **matches the installed file** (the check itself **fails**, not merely warns,
   on a missing/empty checksum **or a mismatch** — the generic checksum scan only
   emits `checksum-untracked` / `user-modified` warnings, so this check enforces
   checksum integrity independently), (c) it
   represents **exactly** the enabled retrieval-pack set (verified via stable
   route-row markers, not a loose substring), and (d) it still carries the key
   **safeguard invariant markers** (pack deferral, direct-search exemptions,
   per-phase health reuse, internal-no-public-web) so a coherent-but-gutted
   instruction cannot pass. It also asserts valid YAML
   frontmatter with `applyTo: '**'` and no unresolved `{{PLACEHOLDER}}` tokens.
   When **no** retrieval-enforced pack is enabled the check is a no-op **only if
   the file and manifest entry are both absent**; if the file or a manifest entry
   is still present with no retrieval pack enabled, the check **fails as an
   orphaned overlay** (a stale globally-applied instruction pointing at
   unavailable tools). This closes the silent-omission gap: an installer cannot
   drop both the file and the manifest entry while leaving a retrieval pack
   enabled, and cannot strand the instruction after all retrieval packs are removed.
   One subtlety hardened during review: the existing `installed_packs`
   (`verify_workspace.py` ~2948-2951) is built from `manifest.capability_packs`
   **or** `config.capability_packs`, so it is *not* independent of manifest
   membership — a nonempty manifest that omits a pack while config still enables
   it would silently disable the check. The enabled retrieval-enforced set is
   therefore computed from the **union** of the manifest and config capability-pack
   lists (config is authoritative for "enabled"), so dropping a pack from the
   manifest's list cannot suppress enforcement.

3. **Install + tune weaving + registry + contracts.** `install-harness` installs
   the enforcement instruction whenever any retrieval-enforced pack is selected,
   **rendering its route-row block to exactly the selected set** (a one-pack
   install must not retain both rows, or it would fail the exact-set verifier),
   records it in the manifest `artifacts[]` with a checksum of the rendered file,
   and adds it as an overlay entry in each **selected** pack's
   `capability_pack_overlays[]` record. The capability-pack
   registry marks which packs are retrieval-enforced via a new **optional
   `retrieval_enforced` boolean** added to `capability-pack-registry.schema.json`
   (the schema is `additionalProperties: false`, so the property must be declared;
   no closed pack-ID enum changes). The `agent-engram` and `graphtor-docs` pack
   instructions (templates + dogfood mirrors) gain a cross-reference to the
   coordinator. `tune-harness` detects drift (pack enabled but enforcement
   instruction missing, stale, or representing the wrong pack set), re-renders
   the enabled route rows when the set changes **and updates the recorded manifest
   checksum**, and removes the file when no retrieval-enforced pack remains
   **together with its `artifacts[]` entry and both packs'
   `capability_pack_overlays[]` records** (no orphaned manifest state). As the
   terminal task, 075.005-T also performs a **final dogfood manifest
   reconciliation**: it refreshes the `.autoharness/harness-manifest.yaml`
   checksums for every already-tracked artifact this shipment modifies —
   `install-harness/SKILL.md` (075.004), `tune-harness/SKILL.md` (075.005), and
   both pack instructions (075.007) — plus the new coordinator instruction, so
   dogfood `verify_workspace` reports no stale/user-modified checksums.

The two surfaces are **not equally hard**: surface 1 is *soft* session-time
routing discipline that an LLM agent self-applies; surface 2 is *hard*
installation/coherence enforcement that CI catches deterministically. The
"deterministic hook" the stash items ask for is the guarantee that a workspace
cannot silently drop the enforcement discipline without the verifier failing —
not a guarantee that the agent's every tool choice is intercepted.

Telemetry-based retrospective usage auditing (the telemetry epoch already carries
`operations.cli_tools`) is noted as a **future phase**, not built here.

## Rationale

* **Both stash seeds want the same mechanism.** `8EB5C5D8` explicitly says
  graphtor-docs needs a *"similar hook mechanism"* to engram's (`909F493D`). Two
  bespoke mechanisms would drift; one generic overlay parameterized by
  "retrieval-enforced pack" serves both and any future retrieval pack.

* **autoharness cannot intercept an agent's live tool calls.** The product is
  templates + a verifier, not a runtime that sits between the agent and its tools.
  A git `pre-push` hook (P-019) fires on git events and cannot observe mid-session
  tool choices, so it can only check index freshness — a weak proxy for "usage."
  The honest surfaces are therefore a **soft session-time** discipline (an
  instruction protocol the agent self-applies, like role-enforcement's
  pre-mutation protocol) and a **hard install/CI-time** verifier. This decision
  builds on both rather than over-promising an interceptor.

* **Reuses three proven patterns**, minimizing novel surface and review risk:
  1. `role-enforcement.instructions.md` — the fail-closed pre-operation protocol
     shape (classify → check → route → fail-closed).
  2. `_check_copilot_code_review_instruction` + tests — the "instruction artifact
     + deterministic verifier + drift/frontmatter/placeholder tests" template.
  3. `PACK_ASSERTIONS` — the manifest/profile-gated per-pack weaving check style.

* **Deterministic where it can be.** Enforcement of an LLM's tool *choice* is
  inherently soft, but the *presence, coherence, and wiring* of the enforcement
  discipline is fully deterministic and CI-catchable. That is the "deterministic
  hook" the stash items are really asking for: the workspace cannot silently drop
  the enforcement discipline without the verifier failing.

## Options considered

| Option | Verdict |
|---|---|
| **A. Two bespoke per-pack hooks** | Rejected — drift risk; contradicts `8EB5C5D8`'s "similar mechanism" framing. |
| **B. Git pre-push hook enforces usage** | Rejected as primary — git hooks cannot observe agent tool choices; only index-freshness proxy. May be a future adjunct under P-019. |
| **C. Runtime interceptor / tool-call gateway** | Rejected — autoharness does not own the agent runtime; out of product scope. |
| **D. Telemetry-based retrospective audit** | Deferred to a future phase — depends on the runtime emitting per-session tool usage into the epoch; useful as evidence, not as prevention. |
| **E. Generic Pre-Retrieval Routing Protocol instruction + deterministic verifier + install/tune weaving** | **Accepted** — native, deterministic where possible, reuses proven patterns, generic across retrieval packs. |

## Scope boundary

* **In scope:** the enforcement coordinator instruction template + dogfood
  mirror (thin coordinator with exemptions + sensitivity-aware fallback +
  conditional enabled-row rendering); the verifier check + tests (pack-enabled
  gating, exact-set, file/manifest/checksum); the `retrieval_enforced` registry
  schema property + registry data marking + registry tests; install-harness
  weaving + manifest `artifacts[]` + `capability_pack_overlays[]` records;
  `agent-engram` + `graphtor-docs` pack-instruction cross-references (templates +
  mirrors) + overlay-contract text; tune drift check (re-render on set change /
  remove when none remain); `docs/capability-packs.md` + a harness-architecture
  note; dogfood manifest tracking (this repo enables engram + graphtor-docs).
* **Out of scope:** telemetry capture of live tool usage; any git-hook usage
  proxy; a runtime tool-call interceptor; changing engram/graphtor-docs pack
  instruction *content* beyond a cross-reference to the coordinator; new closed
  pack-ID enums (the `retrieval_enforced` property is additive and does not touch
  the closed pack enums).

## Review hardening (adversarial design review, 2026-07-10)

An adversarial design review (rubber-duck, gpt-5.6-sol) accepted the core
architecture and required these corrections, all folded into the decision above
and the task breakdown:

* **P0 — Routing must defer, not override.** The coordinator carves out explicit
  exemptions (literal/regex/known-path → direct grep/read; per-phase health
  reuse; mixed queries may use both) and defers to each pack instruction for
  lifecycle/tool/fallback specifics, so it never contradicts the existing pack
  protocols.
* **P0 — Sensitivity-aware fallback.** Internal business-context misses must not
  fall back to public web; only public/external questions may.
* **P0 — Pack-enabled verifier gating.** Expectedness derives from the enabled
  retrieval-enforced set (not manifest membership); when a retrieval pack is
  enabled the file must exist, be manifest-listed with checksum, and represent
  exactly the enabled set — closing the silent-omission gap.
* **P0 — Registry schema property.** `retrieval_enforced` is declared in
  `capability-pack-registry.schema.json` (additionalProperties:false) with tests.
* **P1 — Thin coordinator + cross-references.** The coordinator owns only
  classification/precedence/exemptions/deviation-format; pack instructions win on
  details and gain a cross-reference; overlay-contract records updated.
* **P1 — Conditional rendering + exact-set verification** via stable route-row
  markers; tune re-renders on set change and removes the file when none remain.
* **P1 — Honest framing.** Soft session discipline + hard install coherence;
  deviation records are session-output signals, not audited telemetry.
* **P1 — Re-decomposition** into seven single-domain tasks (below).

### Second-pass review (resolutions confirmed no P0 remains)

A follow-up pass on the hardened doc confirmed the core design is sound with **no
remaining P0** and raised four P1 refinements, all folded in above:

* **Orphaned-overlay gap.** The verifier no-op now applies only when the file and
  manifest entry are both absent; a stranded instruction with no retrieval pack
  enabled fails as an orphaned overlay (surface 2). Tune flags/removes it (075.005-T).
* **Safeguard markers, not just route membership.** The verifier also checks the
  key safeguard invariant markers (pack deferral, direct-search exemptions,
  per-phase health reuse, internal-no-public-web) so a gutted-but-coherent
  instruction cannot pass; ambiguous sensitivity defaults to internal/no-public-web.
* **Dependency-cycle fix.** The constant↔registry drift guard moved from 075.006-T
  to 075.003-T; 075.006-T is now registry schema/data only (no verifier coupling),
  breaking the 075.002-T → 075.006-T → (drift needs verifier) cycle.
* **Decomposition granularity — deliberate judgment.** The reviewer flagged
  075.003/005/006/007 as touching several files. These are held at seven tasks by
  design: the affected work is mechanical documentation/template replication
  (e.g., 075.007-T adds one identical cross-reference line to a template+mirror
  pair per pack) and a single cohesive parametrized test matrix (075.003-T), where
  "files touched" overcounts blast radius and each unit is well under the 2-hour
  horizon. Further fragmentation would add dependency-wiring risk (the very cycle
  just corrected) without reducing per-task error compounding. Ownership is kept
  non-overlapping: install-contract text lives in 075.004-T, documentation-contract
  text in 075.005-T.

## Task decomposition (seven single-domain units)

| Task | Domain | Scope |
|---|---|---|
| 075.001-T | instruction | Coordinator instruction template + dogfood mirror (exemptions, sensitivity-aware fallback, conditional enabled-row rendering, stable markers, defers to pack protocols) |
| 075.002-T | verifier code | `_check_capability_pack_enforcement` (pack-enabled gating, exact-set via markers, independent file/manifest/checksum) |
| 075.003-T | test | Verifier behavior matrix (none / engram-only / graphtor-only / both; missing-file; missing-manifest-entry; wrong-set; **orphaned-overlay** (file/manifest present, no pack); gutted-safeguard-marker; placeholder; frontmatter flip) **plus the constant↔registry drift guard** (verifier's retrieval-enforced constant equals the registry-marked set) |
| 075.004-T | install-workflow | install-harness conditional install + manifest `artifacts[]` + `capability_pack_overlays[]` + dogfood mirror checksum |
| 075.005-T | tune + docs | tune drift (re-render on set change / remove when none / flag orphaned overlay) + `docs/capability-packs.md` + harness-architecture note |
| 075.006-T | schema/data | `retrieval_enforced` registry schema property + registry data marking (engram + graphtor-docs) + registry schema/data validation tests (no verifier coupling) |
| 075.007-T | instruction cross-ref | `agent-engram` + `graphtor-docs` templates + mirrors reference the coordinator; overlay-contract text alignment |

## Verification expectation (for Ship)

* Full unittest suite green, including new `tests/test_capability_pack_enforcement.py`
  and updated `tests/test_capability_pack_registry.py`.
* `verify_workspace` on the dogfood repo passes with the enforcement instruction
  installed, manifest-tracked (`artifacts[]` + both packs' `capability_pack_overlays[]`),
  and its rendered route rows representing exactly {engram, graphtor-docs}.
* No unresolved `{{VARIABLE}}` in the installed mirror; markdownlint heading
  hierarchy (MD001/MD025/MD041) clean; all cross-references resolve.
* Adversarial code review confirms: no exemption regressions (legitimate
  literal/known-path grep still allowed), no public-web fallback path for
  internal business-context (ambiguous sensitivity defaults to internal),
  verifier no-ops cleanly only when file+manifest are both absent (orphaned
  overlay fails otherwise), safeguard invariant markers are verified (not just
  route-set membership), and exact-set marker matching (not loose substring).
