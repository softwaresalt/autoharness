# Composability / single-source-of-truth across autoharness surfaces — spike findings and decision

* **Date**: 2026-08-09
* **Spike artifact**: `004-SP`
* **Living tracker**: stash `34D50F2D`, candidate **(a)** only
* **Agent / route**: Stage — `claude-opus-5` / `anthropic` / `high`
* **Base**: `main` = `origin/main` = `6dbdde67a8932b0765af4af664f2d92c318a6ccc`
* **Mode**: normal (non-dark) Stage research; **read-only**
* **Classification**: **PARTIAL GAP**
* **Verdict**: **CONDITIONAL PROCEED** (confidence medium-high)

## Scope and constraints

Research-only. No source, template, schema, or config file was modified. No
branch, worktree, commit, push, or PR was created. No implementation feature,
task, or shipment was created. No Ship work was performed. External sidecars
(`backlogit`, Engram, `graphtor-docs`) were treated as strictly read-only and
were not mutated.

**No spike/research worktree was created.** The single existing clean worktree
was sufficient for a read-only investigation, so the Stage P-016 spike/research
worktree exception was deliberately *not* exercised.

## Operator decisions recorded (authoritative)

1. **Sequencing** — remaining work proceeds as candidate **(a)** first, then
   candidate **(c)**, beginning with this spike.
2. **Engram authority** — Engram is a **read-only workspace-memory sidecar**. It
   has **no execution or mutation authority**. autoharness may consult it to
   improve performance and outcomes. Candidate (c) must **not** assign authority
   to Engram.
3. **Model names** — product-spec model names are **illustrative and
   non-authoritative** because models change frequently. `.autoharness/config.yaml`
   is the authority for dynamic model routing. **Do not create work to hardcode
   spec model names.**
4. **Composability intent** — one source of truth for autoharness functionality,
   exposed through thin API, MCP, and CLI surfaces. Each surface must invoke the
   same underlying codebase rather than reimplementing behavior. Where this
   already exists, document and preserve it; where partial or absent, identify
   the smallest gap.

## Surface inventory

| Surface | Status | Evidence |
|---|---|---|
| **CLI** | **The only real surface.** 11 commands, hand-rolled arg parsing (no `argparse`). | `pyproject.toml` `[project.scripts] autoharness = "autoharness.cli:main"`; `cli.py:2253` `main()` |
| **Python library** | **Nominal, not contractual.** Importable core exists but has zero consumers outside `src/` and `tests/`; no `__all__`, no declared public API. | `autoharness/__init__.py` is 7 lines; scans of `scripts/` and `templates/` for `from autoharness` / `import autoharness` return zero hits |
| **MCP (own)** | **ABSENT** — not partial. No MCP SDK dependency, no server implementation. | Deps are only `jsonschema` + `PyYAML`; zero hits for `FastMCP`, `mcp.server`, `stdio_server`, `@mcp.`, `Server(` in `src/` |
| **MCP (consumed / validated)** | Present. autoharness validates *other tools'* MCP registry mappings. | `verify_workspace.py:140-159` — `OP_CREATE_MCP` … `OP_RESOLVE_CHECKPOINT_MCP` |
| **Agent prose (de-facto 2nd surface)** | Present but stringly-typed: argv + exit codes + ad-hoc JSON. | Templates/skills shell out, e.g. `autoharness gate pipeline-topology --mode agent --shipment {shipment_id} --phase pre_claim --json` |
| **Marketplace plugin** | Packaging only (agents + skills). No code surface. | `plugin.json` |

A telling detail: the telemetry contract *already models* the multi-surface world
that does not yet exist. `telemetry/tool_event.py:35` defines
`TOOL_SURFACES = frozenset({"mcp","cli","shell","builtin","api","unknown"})`,
while autoharness's own single emission site hardcodes `tool_surface='cli'`
(`cli.py:789`).

## Call-path map (surface → core)

Entries marked **(\*)** are **policy leaked into the adapter** — business
decisions a second surface would be forced to reimplement.

| Command | Core call | Adapter-owned policy |
|---|---|---|
| `verify-workspace` | `verify_workspace(workspace_path, autoharness_home, staging_dir) -> dict` | **(\*)** `_report_has_failures` (`cli.py:112`) *defines* what counts as failure |
| `gate check` | `gate.check(...)` → `feedback.enforce(...)` → `build_correction_report(...)` | **Best in class** — `enforce()` owns `exit_code` in core. **(\*)** `_load_gate_config` (`cli.py:334`); **(\*)** the "no gates configured" early return |
| `gate size` | `sizing.size_task(..., fetch_fn=<CLI closure>)` | **(\*)** fail-open-unless-`--strict` exit policy |
| `gate copilot-review` | `gates.copilot_review` | **(\*)** `_audit_copilot_review_force` (`cli.py:599`) authors the override audit log |
| `gate pipeline-topology` | `topology.evaluate(TopologyInput, FilesystemTopologyReaders) -> TopologyResult` | **(\*)** adapter **mutates the verdict** via `dataclasses.replace(result, exit_code=0, forced=True, …)`; **(\*)** writes force-audit log (`cli.py:707`); **(\*)** ~60 lines of telemetry policy incl. outcome classification and redaction (`cli.py:736`) |
| `gate dag-readiness` | `compute_dag_readiness(...)` + `compute_next_eligible(...)` | **(\*)** adapter **literally synthesizes the entire `degraded` payload** (`cli.py:975-995`), self-documented as "the CLI-EXCLUSIVE synthesis of gate outcome 1"; **(\*)** `status` and `degraded_reason` have **no core owner** |
| `telemetry begin/record/event` | `telemetry.*` | **(\*)** ~150 lines of payload semantics: `_validate_record_epoch_id`, `_validate_record_timestamp`, `_merge_telemetry_context_payload`, `_merge_telemetry_context_into_event_payload`, `--compose-tool-events` hybrid fail-closed rule |
| `eval review/run` | `eval.reviewer` / `eval.runner` / `eval.summary` | Comparatively thin |
| `setup-vscode/-copilot-cli/-claude/-codex` | **none** | **~250 lines (`cli.py:1861-2252`) with no core module at all** — 100% single-surface |

### install / tune orchestration boundary

There is **no Python implementation of install or tune**.
`.github/skills/install-harness` and `tune-harness` are LLM-followed `SKILL.md`
workflows, and `install-harness` carries an explicit variable-resolution table
(`{{PROJECT_NAME}}`, `{{SUFFIX_*}}`, `{{DOCS_*}}`, `{{PRIMARY_LANGUAGE}}`,
`{{BUILD_COMMAND}}`, `{{CAPABILITY_PACKS_YAML}}`, …).

Yet `verify_workspace.py` **independently re-implements the same rules in Python**
in order to check the result: `_render_template` (`:1142`),
`_derive_template_variables` (`:2193`), `_language_defaults` (`:2148`),
`_resolve_source_template` (`:1974`), `_scan_uninstalled_templates` (`:2001`).

**Two independent authorities for one rule set, with no mechanism forcing them to
agree.** Drift is silent by construction. This is the largest genuine duplication
of business logic in the repository — and notably it is *prose-versus-code*,
not surface-versus-surface.

## Duplication / divergence / gap inventory

1. **D1 — install-vs-verify template-variable derivation** (F6 above). Real
   duplicated business logic across a prose skill and Python. Highest severity.
2. **D2 — verdict mutation in the adapter.** `gate pipeline-topology` `--force`
   rewrites a BLOCK into a PASS in `cli.py`, not in `topology.py`.
3. **D3 — CLI-exclusive gate outcome.** One of the seven observable
   `dag-readiness` outcomes (`degraded`) and the entire `status` field are
   unreachable from any non-CLI caller.
4. **D4 — observability policy in the adapter.** The only `ToolTelemetryEvent`
   construction site in the product is `cli.py:789`, including outcome
   classification and redaction rules.
5. **D5 — pass/fail definition in the adapter.** `verify-workspace`'s failure
   semantics live in `_report_has_failures`, not with the core that produces the
   report.
6. **D6 — telemetry payload semantics in the adapter.** ~150 lines of
   validation/merge rules that any second surface would have to duplicate.
7. **D7 — no core at all for `setup-*`.** ~250 lines of installer logic reachable
   only by running the CLI.
8. **D8 — divergent result shapes.** `verify-workspace` returns an untyped
   `dict[str, Any]`; gates return bespoke frozen dataclasses with `.to_dict()`;
   `dag-readiness` emits core `to_dict()` *plus* adapter-injected keys. No shared
   envelope.
9. **D9 — divergent error/exit-code semantics.** `ValueError → sys.exit(2)` per
   hand-rolled parser, typed `GatesConfigError` / `BacklogUnavailableError`, and a
   blanket `except Exception` fail-open in telemetry. Exit codes 0/1/2/3 mean
   different things per subcommand and are specified only in CLI prose.
10. **D10 — no declared public API and no second consumer** to prove the core is
    surface-sufficient.

### What is already good

`topology.py` defines a `TopologyReaders` `Protocol` (with
`FilesystemTopologyReaders` and `_NullReaders`); `runner.run_gate` accepts
`run_fn`; `sizing.size_task` accepts `fetch_fn`. The gate and telemetry cores are
genuinely surface-independent and heavily covered
(`test_gates_topology.py` 1814 lines, `test_gates_dag_readiness.py` 566,
`test_verify_workspace.py` 6306). **The missing piece is not testability — it is
that policy, observability, and degraded-mode synthesis sit above the core.**

## Product vs external boundary

* **autoharness product**: `src/autoharness/**`, `templates/**`, `schemas/**`,
  `.github/{agents,skills,instructions}/**`, `docs/**`, `plugin.json`.
* **External, out of scope, read-only**: `backlogit` (Go; own MCP + CLI),
  Engram (memory sidecar), `graphtor` (Rust; docs MCP).

autoharness consumes these via registry-declared MCP tools with CLI fallbacks and
must neither vendor nor reimplement them. Per operator decision 2, Engram carries
**no execution or mutation authority**.

## Assessment: PARTIAL GAP

A single-source-of-truth architecture **exists for the computational core** of
gates and telemetry (typed, dependency-injected, well-tested) but is
**incomplete at the seam**: policy/verdict-mutation/audit/telemetry/degraded
synthesis/config loading live in the adapter (D2–D6), one capability family has
no core at all (D7), the install-vs-verify rules are genuinely duplicated (D1),
there is no shared result envelope or error taxonomy (D8, D9), and there is no
declared public API or second consumer to prove sufficiency (D10).

It is neither ALREADY SATISFIED nor ABSENT.

## Recommendation: CONDITIONAL PROCEED

**Proceed only if candidate (a) is scoped as a *consolidation of logic that
already exists*, not as building an MCP server or an action/observation execution
engine.**

Product spec §3 as literally written — "treat CLI commands and MCP requests as
equivalent actions within the Action/Observation loop", sequential pipelining,
stderr routed back to the active model — describes an **agent runtime** (Copilot
CLI / Claude Code), which already owns the action/observation loop, tool
dispatch, and stderr surfacing. autoharness is a harness-*composition* tool.
Building a runtime executor inside it would be a large speculative framework with
no consumer in this repository. **If the operator wants §3 literally, the answer
is NO-GO.** The defensible residue of §3 is the internal one, which matches
operator decision 4 exactly.

### Minimal target architecture

1. **One thin application/service function per capability**, owning all policy
   currently stranded in `cli.py`: config loading, pass/fail definition,
   exit-code semantics, force-override and audit-log writing, telemetry emission,
   degraded-mode synthesis.
2. **One shared typed result envelope** — `status`, `exit_code`, `data`,
   `messages`, `warnings`, `artifacts` — with `.to_dict()`. **Wrap, do not
   rewrite** existing results, including the 4,453-line `verify_workspace` dict.
3. **One error taxonomy** — a single `AutoharnessError` base carrying a
   machine-readable `kind` — replacing the per-parser `ValueError → sys.exit(2)`
   pattern, plus a machine-readable exit-code contract.
4. **`cli.py` reduced to**: parse argv → call app function → render human/JSON →
   `sys.exit(result.exit_code)`. No policy.
5. **Declare the public API** (`__all__` + docs) once the seam exists.

**Do not build an MCP server or HTTP API now.** The deliverable of (a) is that
one *could* be added without touching policy. If proof-of-sufficiency is wanted,
add an in-process JSON dispatch used only by tests — not a real server.

### Authority / error / observability contracts

* Adapters **may** translate transport (argv, JSON, stdio) and render output.
* Adapters **must not** own policy or business decisions: no verdict mutation, no
  audit-log authorship, no telemetry classification, no synthesis of outcomes the
  core cannot produce.
* **Every observable outcome must be reachable from the core** — closing the
  CLI-exclusive `degraded` outcome.
* **Telemetry is emitted by the core**, with `tool_surface` supplied *by* the
  adapter, so the existing `TOOL_SURFACES` enum stops being aspirational.
* **Engram remains read-only with no authority** (operator decision 2).
* **`.autoharness/config.yaml` remains the model-routing authority**; no spec
  model names are hardcoded (operator decision 3).

### Explicit non-goals

1. No autoharness-owned MCP server in (a).
2. No action/observation execution loop, sequential-pipelining engine, or
   stderr-to-model routing — agent-runtime responsibility.
3. No generic plugin/registry framework or abstract `Tool` base class built for
   symmetry.
4. No change to `backlogit`, Engram, or `graphtor`.
5. No hardcoded model names.
6. No rewrite of install/tune prose skills into Python — only *declare* one
   authority for the duplicated variable-derivation rules.
7. No parallel execution, scheduler, or extra worktree (P-001 / P-016 preserved).

### Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Behavior drift — `cli.py` exit codes are load-bearing for agent prose | Keep CLI-level tests (`test_gate_pipeline_topology_cli.py`, `test_telemetry_record_cli.py`, `test_telemetry_event_cli.py`) **unchanged** as a characterization suite; move logic beneath them |
| R2 | Scope creep into a runtime/MCP build, actively invited by spec §3 | Non-goals above + `plan-harden` (elevated blast radius: CLI distribution + multiple template families) |
| R3 | `verify_workspace.py` is 4,453 lines returning an untyped dict | Wrap in the envelope; never rewrite |
| R4 | The install-vs-verify dedup spans a prose skill **and** Python — width-isolation hazard | Make it a *declare-the-authority* documentation task first, not a code move |
| R5 | Zero external library consumers ⇒ no forcing function; refactor could be pure churn | Keep the operator's (a)→(c) sequence so (c) becomes the seam's first real consumer |

## Does candidate (c) depend on (a)?

**No — (c) *benefits from* (a) but is not blocked by it.**

Candidate (c) (background Verification & Compaction: log parsing, history
summarization, state pruning) already has **both** substrates:

* **Python-side**: `telemetry/reader.py`, `aggregation.py`,
  `tool_event_compose.py`, `_jsonl_segments.py`, `gaps.py`.
* **Prose-side**: P-020 post-merge compaction, context-efficiency instructions,
  and prune-on-restore already shipped via `002-SP` / `111-F`.

(c) could therefore be scoped independently today. The dividend of doing (a)
first is **structural**: with the shared application-service seam and result
envelope in place, (c)'s new log-parsing and summarization entry points land in
the core layer by default instead of accreting in `cli.py` — which is precisely
how `cli.py` reached 2,289 lines.

**Recommendation**: keep the operator's (a)-then-(c) sequence, but **do not
declare a blocking dependency**, so (c) can be re-scoped independently if (a) is
deferred or descoped.

## Bounded next-step decomposition (proposed only)

**Deliberately NOT created this session** — this spike is research-only. Each
item is under 2 hours and width-isolated.

| ID | Work | Size / Complexity |
|---|---|---|
| T1 | Document the surface inventory + call-path map under `docs/` (doc-only) | XS / trivial |
| T2 | Add the shared result envelope + error taxonomy with tests; no call-site changes | S / low |
| T3 | Extract `pipeline-topology` force/audit/telemetry policy out of `cli.py`, behind existing CLI tests | S / medium |
| T4 | Give `dag-readiness` `degraded`/`status` synthesis a core owner so all 7 outcomes are core-reachable | S / medium |
| T5 | Move verify pass/fail policy (`_report_has_failures`) + gate config loading into core | XS / low |
| T6 | Move telemetry payload merge/validation out of `cli.py` into telemetry app functions | M / medium |
| T7 | Declare the public library API once T2–T6 land | XS / trivial |
| T8 | Declare a single authority for template-variable derivation; cross-reference from install/tune prose (doc-only) | S / low |

T3–T6 are the real dedup; T1, T2, T7, T8 are cheap and independent.

If harvested, the covering feature carries **elevated blast radius** and
`impl-plan` **requires `plan-harden` (P-006)** before `plan-review`.

## Disposition

* Stash `34D50F2D` **remains ACTIVE** as the living tracker — candidate **(c)**
  is still outstanding after (a).
* Candidate **(c)** remains DEFERRED and requires its own
  spike → impl-plan → plan-review → harvest cycle.
* No implementation feature, task, or shipment was created by this spike.
