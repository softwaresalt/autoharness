# Changelog

## 1.3.2 - 2026-04-26

### Changed

- Added branch management guardrails to Ship agent template: Branch Retention (NON-NEGOTIABLE) directive in Step 5 prevents premature checkout of the default branch while a feature PR is pending; Post-Merge Branch Protocol (NON-NEGOTIABLE) in Step 6 requires all closure work on a dedicated `post-merge/{feature_slug}` branch with its own PR; Branch Management Rules section consolidates the constraints.
- Added branch retention and post-merge branch protocol to pr-lifecycle skill template: Step 5 now includes a NON-NEGOTIABLE branch retention directive; Step 6 explicitly prohibits working on the default branch after merge.
- Added `ship_branch_management` and `pr_lifecycle_branch_retention` foundation assertions to `verify-workspace` so installed harnesses are validated for the new branch management markers.

## 1.3.1 - 2026-04-26

### Changed

- Enforced deterministic step-sequence execution in the Stage agent template with a NON-NEGOTIABLE step sequence contract, forward pointers after harvest, mandatory shipment assembly language, and a pre-summary verification gate that halts if `shipment_id` is missing.
- Hardened Ship agent fallback path to recommend running Stage first when no shipment exists, rather than silently proceeding with direct assembly.
- Added `stage_shipment_determinism` foundation assertion to `verify-workspace` so installed harnesses are validated for the new determinism markers.
- Added three behavioral constraints to Stage prohibiting: skipping shipment assembly, handing off feature ID instead of shipment ID, and presenting summary before all steps complete.

## 1.3.0 - 2026-04-25

### Added

- Recognized legacy `0.9.0` schema contracts for harness config, workspace profile, and harness manifest, with explicit migration proposals instead of treating them as unknown contract failures.
- Added backlogit SQL schema and YAML frontmatter/tooling instruction templates so backlog-aware harnesses can use `backlogit_query_sql` and field-level tooling guidance deterministically.
- Added deterministic regression coverage for backlogit overlay docs, intercom review workflow ordering, foundation copilot guidance, and install/tune branch-safety guidance.

### Changed

- Expanded `verify-workspace` targeted checks and warning reporting so repeated compatibility drift is grouped into clearer summaries while preserving the underlying finding count.
- Updated install and tune workflow guidance to keep generated output on feature branches or as local uncommitted changes pending pull-request review, rather than recommending direct default-branch commit or push.
- Replaced heuristic backlogit stale-artifact cleanup with explicit source-artifact cleanup driven by stable backlogit metadata when the `backlogit` capability pack is enabled.

### Documentation

- Updated README, Getting Started, Tuning Guide, Capability Packs, and backlogit integration docs to match the current install/tune behavior, schema-contract handling, and backlogit overlay surface.