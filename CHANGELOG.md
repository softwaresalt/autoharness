# Changelog

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