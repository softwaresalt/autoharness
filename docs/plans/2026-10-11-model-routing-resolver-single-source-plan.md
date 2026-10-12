---
title: "Model routing resolver: a single deterministic source of truth for route resolution (R1-A)"
description: "Plan for the first release unit of the 040-DL model-routing design. Pin today's route-resolution semantics as language-neutral vectors, extract them into one pure module, make verify-workspace delegate to it with unchanged outputs, expose it as a read-only `autoharness routing resolve` CLI, and let the Orchestrator declare invocation routes from that CLI with a declared prose fallback. No new config keys, no schema change, no routing value change."
doc_type: plan
status: reviewed
created: 2026-10-11
source_stash: BF66F08B
source_deliberation: docs/decisions/2026-10-11-model-routing-v2-deliberation.md
deliberation_id: 040-DL
baseline_document: docs/design-docs/model-routing-v2.md
release: "R1-A"
harvested_feature: "207-F"
harvested_shipment: "214-S"
successor_plan: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md
review_record: docs/reviews/2026-10-11-model-routing-resolver-single-source-plan-review.md
requires_plan_hardening: "yes"
---

# Model routing resolver: a single deterministic source of truth (R1-A)

## Outcome

After this plan ships:

* `src/autoharness/model_routing.py` is the one definition of route resolution (tier
  fallback, role routes, `context_tier`, nested/legacy/tier3 escalation, both-present
  ambiguity, role-scoped same-route guard). It is a pure function over parsed config data,
  and that purity is enforced by a test guard rather than assumed.
* Language-neutral JSON vectors pin that behavior, so a later Go port (`F194A1D8`) can run
  the same cases.
* `verify_workspace.py` and the install variable derivation delegate to the module. Public
  outputs (`targeted_checks` shapes, rendered variables) are unchanged.
* `autoharness routing resolve --workspace <path> --site <stage|ship|orchestrator>
  [--kind route|escalation] --json` prints one JSON document and exits `0` (resolved), `1`
  (resolved with a declared degradation, for example a same-route escalation), or `2`
  (unresolved or invalid config, or a YAML anchor, alias, or merge key under `model_routing`
  in a config that declares schema 1.2.0; fail closed). The raw-YAML check is one shared
  function (`model_routing_yaml.check_model_routing_yaml`, unit A2a) because `yaml.safe_load`
  erases those constructs before the config reaches the resolver; `verify-workspace` calls
  the same function in R1-B.
* The Orchestrator declares its Stage and Ship invocation routes from that CLI when it is
  available (`TOOL_OK`) and otherwise follows the existing prose with
  `TOOL_DEGRADED: routing-resolver-cli`. Its config-validation clause validates against the
  schema version matching the document's own `schema_version`. The Stage and Ship
  agents' own escalation-directive prose still resolves by the existing prose until R2, so
  after this release the resolver is the single source for verification, install derivation,
  the CLI, and the Orchestrator, and is not yet the only executed definition.
* No config key, schema, policy, or routing value changes. The dogfood
  `.autoharness/config.yaml` is untouched.

## Problem Frame

Route precedence is implemented in `src/autoharness/verify_workspace.py` as private helpers
(`_model_routing_tier_dict`, `_tier_fallback_dict`, `_resolve_role_route_field`,
`_resolve_context_tier`, `_derive_tier_route_variables`,
`_derive_orchestrator_route_variables`, `_derive_role_route_variables`,
`_effective_escalation_route_for_role`, `_effective_escalation_context_tier_for_role`,
`_escalation_route_has_any_field`, `_add_role_route_resolution_check`,
`_add_escalation_route_resolution_check`) and re-described in prose in the Orchestrator,
Stage, and Ship templates and in `escalation-protocol.instructions.md`. At runtime the
Orchestrator follows the prose by reading `.autoharness/config.yaml`, so an LLM executes the
precedence. The copies have drifted: stale route literals in the Orchestrator mirror and in
the escalation-protocol instruction, and a Stage escalation that resolves to Stage's own
route (`1F13DF5E`, `3C19FA0F`; deliberation `040-DL` Finding 4).

This release removes the duplication without changing behavior. It is the prerequisite for
the catalog and bindings release (`R1-B`), which adds new routing keys. Adding keys on top
of three hand-maintained copies of the precedence would multiply the drift.

Scope boundaries (P-021 C1):

* In scope: the resolver module, vectors, delegation, CLI, the Orchestrator directive.
* Out of scope: new config keys (R1-B), escalation `chain` and review diversity (R2/R3),
  switching the Stage and Ship escalation-directive prose to the CLI (R2), Stage and
  Orchestrator route data (`3C19FA0F`, `1F13DF5E`), the stale
  `escalation-protocol.instructions.md` prose (recorded as an R2 follow-up), removal of
  frontmatter route fields (`79021C29`).

## Requirements Trace

| # | Requirement (040-DL decision) | Unit |
|---|---|---|
| RA1 | Today's resolution semantics are pinned as language-neutral vectors before any refactor (D5) | A1 |
| RA2 | One pure module implements those semantics, with no I/O, enforced by a test guard (D5) | A2 |
| RA3 | `verify_workspace` and install derivation delegate to it; public outputs unchanged (D5, D10) | A3 |
| RA4 | Read-only `routing resolve` CLI with a pinned document shape and fail-closed exit codes (D5, D9) | A4 |
| RA4a | One shared raw-YAML guard rejects anchors, aliases, and merge keys under `model_routing` for a 1.2.0 config, in both the CLI (exit `2`) and, in R1-B, `verify-workspace`; advisory below 1.2.0 (D2, D9) | A2a, A4 (consumed by R1-B B6) |
| RA5 | Orchestrator declares routes from the CLI with a declared prose fallback; validates config against the matching schema version (D5, D9, P-012) | A5 |
| RA6 | No new config keys, schema, policy, or routing-value change (D1, D11) | all (guard in A3 and A5 acceptance) |

## Planned Resolver Contract (shared with R1-B)

Defined here so R1-B can extend it. Names are the planned public surface of
`src/autoharness/model_routing.py`.

```python
ROUTE_FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
ROLE_DEFAULT_TIER = {"orchestrator": "tier2", "stage": "tier3", "ship": "tier2"}

@dataclass(frozen=True)
class ResolvedRoute:
    site: str                          # "stage", "ship", "orchestrator"
    kind: str                          # "route" | "escalation"
    model_family: str
    model_provider: str
    reasoning_effort: str
    context_tier: str                  # never empty; "default" when unset everywhere
    tier_class: str | None             # "tier1" | "tier2" | "tier3" | None when unknown
    resolution_chain: tuple[str, ...]  # ordered provenance, e.g. ("stage.model_family", "tier3.model_provider")
    degraded: tuple[str, ...]          # e.g. ("ESCALATION_DEGRADED: same-route",)
    errors: tuple[str, ...]            # e.g. ("AMBIGUOUS_ESCALATION_CONFIG", "ROUTING_UNRESOLVED: model_family")
    def to_document(self) -> dict[str, Any]: ...

def resolve_site(config: Mapping[str, Any], site: str, *, kind: str = "route",
                 installed_roles: frozenset[str] = frozenset()) -> ResolvedRoute: ...
```

Rules reproduced exactly from today's code (no new behavior):

* A tier may be a plain string (treated as `model_family`; no other field) or a mapping
  whose `model` backs `model_family` when `model_family` is unset.
* A role route resolves each field independently: role block, then the role's default tier,
  then (for `context_tier` only) the terminal `default`.
* Escalation: nested `<role>.escalation` if it declares any of `model_family`,
  `model_provider`, `reasoning_effort`; else legacy flat `escalation`; each unset field
  falls back to `tier3` and never to the other source. Both nested and flat declared is
  `AMBIGUOUS_ESCALATION_CONFIG`.
* Same-route guard compares `(model_family, model_provider, reasoning_effort)` only,
  role-scoped; a field unset on either side carries no signal; `context_tier` is excluded.
* Unresolved `model_family` is an error. Empty `model_provider`/`reasoning_effort` is valid
  ("leave empty to use the model default").
* `config.overrides` (194.006-T, AS-F9) is **not an input to the resolver**. It is a
  render-time layer applied by `_authoritative_route_variables` over the config-derived
  route-family variables, outside `model_routing.py`; A3 does not delegate it
  (`_authoritative_route_variables`, `_route_family_variables`, `_compose_artifact_variables`,
  and `_context_tier_override_error` stay in `verify_workspace.py` unchanged), and
  `routing resolve` therefore reports the config-derived route. R1-B (B6a, B7) composes that
  layer explicitly, in one shared function, wherever an installed frontmatter is compared
  with a route, instead of comparing it with raw resolver output (PR #513 review-fix cycle 5,
  thread `PRRT_kwDORzpWpM6rmyoz`). Whether the CLI and R3's invocation-time route should
  include that layer is a deferred decision (stash `EB56281C`).

CLI document (`schema_version: "1.0.0"`, keys pinned by the A4 test): `schema_version`,
`site`, `kind`, `resolved` (the four fields plus `tier_class`), `resolution_chain`,
`degraded`, `errors`, `exit_code`. Publishing a JSON Schema for this document is deferred
to R2/R3, when more consumers exist; the keys are pinned by test until then.

## Implementation Units

Execution posture for every unit: characterization-first. A1 pins today's behavior while the
old code is still the only implementation; A2 to A5 then move behavior without changing it.
Canonical test gate for every code unit:
`$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

### A1: Pin today's route-resolution semantics as language-neutral vectors

**Files (2):** `tests/fixtures/model_routing/existing-semantics.json` (new),
`tests/test_model_routing_existing_semantics_vectors.py` (new).

**Change:** Author about 14 cases as JSON (`config` in, expected resolution out): tier-only
config; role override with only some fields; Stage with no route (falls to `tier3`); Ship
(falls to `tier2`); Orchestrator `context_tier` falling to `tier2`; a legacy plain-string
tier; unset `model_family`; empty `model_provider` and `reasoning_effort` (valid, no error:
the runtime default); nested escalation with partial fields (per-field `tier3`);
legacy flat escalation used when no nested; both-present `AMBIGUOUS_ESCALATION_CONFIG`;
same-route guard true; same family but different provider (not degraded); `context_tier`
difference only (still same-route); installed-role widening. The test runs each case through
the **current** `verify_workspace` helpers and asserts the fixture, so it passes on main
today and fails if any later refactor changes behavior.

**Tests (scenarios):** every vector equals current-helper output; vector ids are unique; the
fixture is valid JSON with no Python-specific constructs.

**Acceptance criteria:** the test passes against unmodified `verify_workspace.py`; no
production file is modified.

**Harness surface:** `harness-surface:none` (no `src/` file). **Size/complexity:** `S` /
`medium`. **Depends on:** none.

### A2: Pure resolver module

**Files (3):** `src/autoharness/model_routing.py` (new),
`tests/test_model_routing_resolver.py` (new), `tests/_resolver_purity_guard.py` (new test
helper; a flat module that discovery does not collect, like `tests/_env_patch.py`).

**Change:** Implement `ResolvedRoute` and `resolve_site` per the planned contract. Reuse the
single `context_tier` enum, `frontmatter_contract.CONTEXT_TIER_VALUES` (194-F H-C5), rather
than a second copy. No I/O, no imports from `verify_workspace` (avoid a cycle).

**Purity guard (makes "no I/O" a tested property, not a convention).** Running the resolver
on a plain dictionary does not prove purity: an implementation could still read a file or an
environment variable and the vector would pass. `tests/_resolver_purity_guard.py` (stdlib
only: `contextlib`, `unittest.mock`, `ast`) therefore provides:

* `forbid_io()`: a context manager that, for the duration of the block, replaces the
  filesystem, environment, process, and network entry points with stubs that raise
  `ImpureAccessError` (an `AssertionError` subclass). Filesystem: `builtins.open`,
  `io.open`, `os.open`, `os.stat`, `os.lstat`, `os.scandir`, `os.listdir`, `os.getcwd`,
  `os.path.exists`, `os.path.isfile`, `os.path.isdir`, and the `pathlib.Path` methods
  `open`, `read_text`, `read_bytes`, `write_text`, `write_bytes`, `stat`, `lstat`, `exists`,
  `is_file`, `is_dir`, `iterdir`, `glob`, `rglob`, `resolve`, `cwd`. Environment: the
  `os.environ` attribute (replaced by a mapping whose every access raises; never
  `patch.dict`, which clears and restores the real mapping, the hazard
  `tests/_env_patch.py` exists to avoid), `os.getenv`, `os.putenv`. Process and network:
  `subprocess.Popen`, `os.system`, `os.popen`, `socket.socket`, `socket.create_connection`,
  `socket.getaddrinfo`. Every violation is also recorded and `__exit__` raises
  `ImpureAccessError` if any was recorded, so a resolver that swallows the error with
  `except Exception` still fails the test. All patches are restored on exit, including
  after an exception.
* `guarded_resolve(*args, **kwargs)`: calls `model_routing.resolve_site` inside
  `forbid_io()`. Every resolver call in `tests/test_model_routing_resolver.py` goes through
  it (R1-B's `tests/test_model_routing_catalog_bindings.py` reuses it), and vector fixtures
  are loaded in `setUpClass`, outside any guarded call.
* `assert_module_import_pure(module)`: a static complement over the module's source (an
  `ast` walk of every import and name, including function-local imports). It allows only
  `__future__`, `dataclasses`, `typing`, `collections.abc`, `enum`, `re`, `types`, and
  `from autoharness.frontmatter_contract import CONTEXT_TIER_VALUES`; any import of, or
  reference to, `os`, `io`, `sys`, `pathlib`, `subprocess`, `socket`, `shutil`, `tempfile`,
  `yaml`, `open`, `environ`, or `getenv` fails. This closes the two bypasses a runtime patch
  cannot see: a name bound at import time (`from os import environ` keeps the original
  object) and a function-local import.

**Tests (scenarios):**

* the A1 vectors parametrized against `guarded_resolve` (the whole run is under
  `forbid_io()`); ambiguity returns the error with no per-role resolution; unresolved
  `model_family` returns `ROUTING_UNRESOLVED`; an empty `model_provider` or
  `reasoning_effort` returns no error; a config carrying a top-level `overrides` mapping
  resolves exactly as without it (the resolver has no override layer);
* **guard self-tests (negative):** a deliberately impure stub resolver for each channel
  (`open`, `Path.read_text`, `os.stat` or `Path.exists`, `os.listdir`, `os.environ[...]`,
  `os.getenv`, `subprocess.run`, a socket connection) fails under `forbid_io()` with
  `ImpureAccessError`; a stub that catches `Exception` around the impure call still fails at
  `__exit__`; a pure stub passes; after the block, `open`, `os.environ`, and `pathlib.Path`
  behave normally (a real temporary-file read succeeds);
* `assert_module_import_pure(model_routing)` passes, and a fixture module that does
  `from os import environ` (or imports `pathlib` inside a function) fails it;
* a source assertion in `tests/test_model_routing_resolver.py` that no resolver call in
  this module bypasses `guarded_resolve` (the same grep-style technique B3a uses).

**Acceptance criteria:** every A1 vector passes through `guarded_resolve` with identical
results; the guard self-tests prove the guard trips on every listed channel (a guard that
cannot fail is not accepted); `assert_module_import_pure(model_routing)` passes; the module
performs no filesystem, environment, subprocess, or network access.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A1.

### A2a: Shared raw-YAML guard for `model_routing` (anchors, aliases, merge keys)

**Files (2):** `src/autoharness/model_routing_yaml.py` (new),
`tests/test_model_routing_yaml.py` (new).

**Why a shared unit.** `yaml.safe_load` resolves anchors, aliases, and merge keys at parse
time, so the resulting dictionary is plain, schema-valid data and the construct is invisible
to the schema and to the pure resolver. The prohibition (040-DL D2, D9) can therefore only be
enforced on the raw YAML text, **before** loading. Two consumers need it: the `routing
resolve` CLI (A4, this release) and `verify-workspace` (R1-B unit B6). One function owns the
rule so the two cannot disagree, and it lands in R1-A because A4 is its first consumer and
`215-S` (R1-B) blocks on `214-S`, so the second consumer (B6) always sees it already shipped.
It is a separate module, not part of `model_routing.py`, because it imports `yaml` (the pure
module's static import allowlist forbids it).

**Change:** One public function and its result type:

```python
@dataclass(frozen=True)
class YamlGuardResult:
    errors: tuple[str, ...]      # fail closed, e.g. "ROUTING_ANCHOR_UNSUPPORTED: alias at line 12"
    warnings: tuple[str, ...]    # advisory (declared schema_version below 1.2.0)
    parse_error: str | None      # a YAML syntax error is reported here, never raised

def check_model_routing_yaml(raw_text: str, schema_version: str | None) -> YamlGuardResult: ...
```

The function walks the `yaml.parse` **event stream** (not `safe_load`) and flags, anywhere in
the value of the top-level `model_routing` key: a node carrying an anchor, an alias event,
and a merge key (a plain, unquoted `<<` scalar in mapping-key position; a quoted `"<<"` key is
an ordinary string). Constructs outside `model_routing` are ignored. Severity follows the
declared `schema_version`, parsed as dotted integers: below `1.2.0` the findings are
`warnings`; at or above `1.2.0`, or when the version is missing or unparsable, they are
`errors` (fail closed; a 1.1.0 config with aliases is **not** rejected, as D2 scopes the
prohibition to 1.2.0 and advises older configs). Findings are in document order with the
construct kind and a 1-based line. Pure over text: no filesystem, environment, subprocess, or
network access.

**Tests (scenarios):** every call runs under the A2 `forbid_io()` guard
(`tests/_resolver_purity_guard.py`). An anchor definition, an alias, and a merge key under
`model_routing` are each flagged with kind and line; an anchor on a sequence node; flow-style
and block-style forms; `errors` at `1.2.0`, a missing version, and an unparsable version;
`warnings` (not errors) at `1.1.0`, `1.0.0`, and `0.9.0`; anchors and aliases **outside**
`model_routing` are ignored; a quoted `"<<"` key and `&`/`*` inside a string or a comment are
not flagged; the baseline-shaped document (undefined aliases) reports the aliases without
raising; syntactically broken YAML sets `parse_error` and does not raise; empty text yields no
findings; the module imports standalone.

**Acceptance criteria:** all scenarios pass; the function is the only anchor/alias/merge-key
scanner in the code base (A4 and, in R1-B, B6 each assert they delegate to it); no existing
file is modified.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `S` /
`medium`. **Depends on:** A2 (reuses the purity guard).

### A3: Delegate verify_workspace and install derivation to the resolver

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_resolver_delegation.py` (new).

**Change:** Replace the bodies of the helpers listed in the Problem Frame with calls into
`model_routing`, keeping every function name, signature, and return shape so existing tests
and the install variable derivation keep working. Do not touch check keys or error strings
(tests and `verify-harness` consume them). The `config.overrides` layer is not delegated
(see the contract above): `_authoritative_route_variables`, `_route_family_variables`,
`_compose_artifact_variables`, and `_context_tier_override_error` are not in the delegated
list and stay unchanged, so overrides still apply over the delegated tier and role values
exactly as today (the existing `test_route_variable_precedence` pins it, unmodified).

**Tests (scenarios):** the A1 characterization test still passes unchanged; a delegation test
asserts each helper returns a value computed by `model_routing` (by patching the module and
asserting it is called); the existing `test_route_variable_precedence`,
`test_context_tier_resolution`, `test_escalation_*`, and `test_verify_workspace` suites pass
unmodified.

**Acceptance criteria:** the whole suite passes with no edits to any pre-existing test; the
diff to `verify_workspace.py` removes logic (net deletions) and adds no new check key.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A2.

### A4: `autoharness routing resolve` CLI

**Files (3):** `src/autoharness/cli.py`, `tests/test_cli_routing_resolve.py` (new),
`CHANGELOG.md` (one entry).

**Change:** Add a `routing` command with a `resolve` subcommand modeled on `harness resolve`
(argparse, `allow_abbrev=False`, one JSON document plus LF on stdout, nothing on stderr after
a successful parse). `--workspace` is required and non-empty. The command reads
`.autoharness/config.yaml` with `yaml.safe_load`, then applies the E8B5B3C5/H6 fail-closed
precheck in full: a missing, unparseable, empty, or `schema_version`-less config, or a config
that fails validation against the schema version matching its own `schema_version` (the same
`resolve_contract_schema_path` plus `Draft7Validator` path `verify_workspace` uses; `jsonschema`
is already a runtime dependency), yields a document with `errors` and exit `2`. There is no
last-known-good fallback. **Raw-YAML guard (040-DL D2, D9):** because `safe_load` erases
anchors, aliases, and merge keys before validation, the command also passes the raw file text
and the observed `schema_version` to the A2a function `check_model_routing_yaml`, **before**
schema validation, so the named code is deterministic whichever schema versions exist. Any
guard `errors` (a construct under `model_routing` in a config that declares 1.2.0 or later)
produce a document whose `errors` carry the `ROUTING_ANCHOR_UNSUPPORTED` entries and exit `2`.
A config declaring `1.1.0` or older is **not** rejected: its guard `warnings` are not emitted
by the CLI (the pinned document key set is unchanged; the advisory belongs to
`verify-workspace`). The CLI contains no scanner of its own. Add the command to `USAGE`.

**Tests (scenarios):** dogfood-shaped fixture config resolves Stage and Ship and escalation
with the expected tuples; same-route escalation gives exit `1` with `ESCALATION_DEGRADED`;
missing config gives exit `2`; a schema-invalid config gives exit `2`; **a config declaring
`schema_version: "1.2.0"` with an anchor, an alias, or a merge key under `model_routing` gives
exit `2` with `ROUTING_ANCHOR_UNSUPPORTED` in `errors` (the regression for the CLI path:
without the guard `safe_load` would hand the resolver plain data and the command would
succeed); the same constructs in a `schema_version: "1.1.0"` config are not rejected and
resolve exactly as the de-aliased config does; the command calls
`model_routing_yaml.check_model_routing_yaml` (patched and asserted) and contains no
`yaml.parse` or event scan of its own;** the document key set is exactly the pinned set; the
command is read-only (a before/after snapshot of the fixture workspace tree, relative paths
plus SHA-256 of each file, is identical for every scenario above, and stderr is empty on a
successful parse).

**Acceptance criteria:** exit codes and key set pinned by test; an aliased 1.2.0 config exits
`2` with `ROUTING_ANCHOR_UNSUPPORTED` and an aliased 1.1.0 config is not rejected; the CLI
delegates to the shared A2a function; the read-only snapshot assertion passes; running it against this
workspace prints Stage `claude-sonnet-5.5`/`anthropic`/`xhigh`/`default` and Ship
`claude-haiku-5.5`/`anthropic`/`xhigh`/`long_context` (recorded in closure, not asserted by
a test that would encode operator data).

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A2, A2a.

### A5: Orchestrator declares routes from the CLI, with a declared fallback

**Files (triple + test):** `templates/agents/_orchestrator.agent.md.tmpl`,
`.github/agents/_orchestrator.agent.md`, `.autoharness/harness-manifest.yaml` (checksum
refresh), `tests/test_orchestrator_routing_cli_directive_contract.py` (new).

**Change:** At the Stage and Ship invocation sites, first resolve via
`autoharness routing resolve --workspace . --site stage|ship --json` (log `TOOL_OK:
routing-resolver-cli`); on CLI failure log `TOOL_DEGRADED: routing-resolver-cli` and follow
the existing prose resolution; a CLI exit `2` halts that invocation (fail closed). Replace
the schema-validation wording that names only `schemas/harness-config.schema.json` with "the
schema version matching the document's own `schema_version`" (versioned mirror), because the
root schema tracks only the current version. Preserve every token required by
`_add_orchestrator_invocation_routing_directive_check` (`context_tier`,
`ROUTING_DEGRADED: context_tier` at both sites). Do **not** edit any route literal in the
prose (those belong to `1F13DF5E`, which awaits an operator decision), and do not change
Step 0 (shared with `209-S`).

**Tests (scenarios):** both sites name the CLI and the `TOOL_DEGRADED` fallback; required
tokens are still present at both sites; the versioned-mirror clause is present; template and
mirror both carry the markers; manifest checksum matches the committed mirror.

**Acceptance criteria:** the existing orchestrator directive checks and the paired-edit
marker tests pass; the manifest checksum equals the committed mirror.

**Harness surface:** `harness-surface:none` (no `src/` file). **Size/complexity:** `M` /
`low`. **Depends on:** A4.

## Dependency Graph

```text
A1 -> A2 -> A3
A2 -> A2a -> A4 -> A5
```

No cycles. A3 and A2a/A4 are independent after A2 and touch different production files; they
are ordered A3 then A2a then A4 only for review simplicity. The A2a function is consumed a
second time by R1-B unit B6 (shipment `215-S` blocks on `214-S`, so it has shipped by then).

## Decisions and Rationale

* **Characterize before extracting (A1 first).** The refactor target is a 5.9k-line file
  with many pinned tests. Vectors generated from the current helpers make "behavior
  preserved" checkable by something other than the existing tests alone, and they double as
  the Go-parity contract.
* **Pure function over parsed data, with purity enforced by a test guard.** Keeps the
  resolver testable without a workspace and portable.
* **CLI is read-only and fail-closed.** Mirrors `harness resolve`; no stale fallback
  (E8B5B3C5).
* **The raw-YAML prohibition lives in one shared function, called before loading.** `safe_load`
  erases anchors, aliases, and merge keys, so a check that runs on loaded data (or only in
  `verify-workspace`) cannot protect the runtime path. One function (A2a) serves the CLI now
  and `verify-workspace` in R1-B, gated on the declared `schema_version` exactly as D2 states
  (error at 1.2.0, advisory below), so the two surfaces cannot disagree. It sits in R1-A
  because the CLI is its first consumer; placing it in R1-B would have shipped a CLI that
  accepts a configuration `verify-workspace` rejects.
* **Prose stays as the declared fallback.** Runtimes without the CLI do not regress; the
  degradation is visible (P-012).
* **No JSON Schema for the CLI document yet.** Pinned keys are enough for one consumer;
  publishing now would freeze a contract before R1-B and R2 shape it.

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| The refactor changes a verify result subtly | A1 vectors run against the old helpers first; A3 forbids editing any pre-existing test; net-deletion acceptance criterion. |
| `verify_workspace` result shapes carry extra keys (`per_role`, `resolved_escalation_*`) that vectors miss | A1 includes a case per shape consumer; A3 asserts the shape through the existing suite. |
| Merge conflict with the queued `209-S` to `213-S` chain on the Orchestrator pair and the manifest | Shipment sequenced after `213-S`; A5 avoids Step 0 and route literals; rebase at claim time. |
| New Python surface while the operator steers toward Go | Pure module plus JSON vectors; thin CLI; cross-read with `039-DL`; not held by `207-S`. |
| The Orchestrator CLI call is unavailable in some runtimes | Declared `TOOL_DEGRADED` fallback to the existing prose. |
| A3 touches many lines of a huge file | Size `M`; one concern; whole-suite gate. |
| The CLI succeeds for a config `verify-workspace` rejects (aliases vanish in `safe_load`) | A2a runs on raw text before loading, in the CLI and in `verify-workspace`; A4 has an exit-`2` regression test and a delegation assertion; no second scanner exists. |

## Plan Hardening Signals (REQUIRED)

* Public API, schema, or contract change: **present**. A new CLI command and a pinned JSON
  document shape; the verification refactor touches a fail-closed gate (P-013.5/P-013.6).
* Security, auth, permission, or compliance-sensitive behavior: **absent**. The resolver
  grants no authority; it reads config and returns a route. (It does not enable any
  cross-provider route; no routing value changes.)
* Migration, backfill, destructive data/config action, or irreversible step: **absent**. No
  config or schema change; the diff is reversible by revert.
* External integration, operator checkpoint, or external dependency: **absent**. The
  Orchestrator's use of the CLI depends on the runtime exposing a terminal; fallback is
  declared.
* High runtime, rollout, or rollback risk: **present**. A behavior-preserving refactor of
  verification logic whose failure would turn fail-closed gates red or, worse, green.

Requires plan hardening: yes

## Runtime Verification and Closure

| Unit | Runtime surface | Verification before absorption |
|---|---|---|
| A3 | `autoharness verify-workspace` | Run it on this workspace before and after; the JSON report is identical except no new keys (record both hashes in closure). |
| A4 | `autoharness routing resolve` | Run for `stage`, `ship`, `orchestrator`, and `--kind escalation` against this workspace; run once against a copy with the config removed and confirm exit `2`; run once against a copy declaring `schema_version: "1.2.0"` with an alias under `model_routing` and confirm exit `2` with `ROUTING_ANCHOR_UNSUPPORTED`. |
| A5 | Orchestrator invocation directive | Confirm the template/mirror/manifest triple; confirm the CLI path and the declared fallback are both stated. |

Closure artifact: the shipment closure record under `docs/closure/` with the before/after
verify-workspace comparison. Rollback trigger: any difference in the verify-workspace report
or any pre-existing test needing an edit. Rollback: revert the shipment PR (additive module
and CLI; no data migration). Owner: Ship, validated by the operator at merge.

## Plan Hardening

**Required:** yes. Two signals are present: a new CLI contract and a behavior-preserving
refactor of a fail-closed verification gate. Hardening recorded 2026-10-12 (UTC).

**Learnings and instructions consulted:**

* `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` (P-013.5 gating
  pattern: existence-gated checks, per-check red/green pairs, directive tokens).
* `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` (not
  triggered here, but confirms no schema file may be touched in this release).
* `docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md`
  (`_orchestrator` is a paired-edit pair; manifest checksum triple).
* `.github/policies/workflow-policies.md` P-013.5, P-013.6, P-012, P-004 (marker convention,
  `harness-surface` rule).
* `.github/instructions/escalation-protocol.instructions.md` (resolution order and
  same-route guard definition the vectors must match).
* `.github/instructions/role-enforcement.instructions.md` (skill inheritance; unchanged).

**Protected invariants:**

* I1 verify-workspace output for this workspace is identical before and after A3 (no new
  key, no changed value), and the per-case check dicts recorded by the A1 vectors are
  identical after the refactor.
* I2 no pre-existing test is edited by any unit in this plan.
* I3 an invalid, missing, empty, or `schema_version`-less config makes the CLI exit `2`; no
  last-known-good fallback (E8B5B3C5/H6).
* I4 the P-013.5 directive tokens (`context_tier`, `ROUTING_DEGRADED: context_tier`) remain
  at both Orchestrator invocation sites.
* I5 the CLI is read-only: it writes nothing to disk and nothing to stderr after a
  successful parse.
* I6 `context_tier` is never part of the same-route comparison.
* I7 `model_routing.py` performs no filesystem, environment, subprocess, or network access.
* I8 the raw-YAML anchor/alias/merge-key rule has exactly one implementation
  (`model_routing_yaml.check_model_routing_yaml`), called on raw text before loading by the
  CLI (A4) and by `verify-workspace` (R1-B B6); a config declaring 1.1.0 or older is never
  rejected for these constructs.
  This is enforced by tests, not by convention: every resolver test call runs under the A2
  `forbid_io()` guard (proved able to fail by negative self-tests), and the module passes the
  static import allowlist.

**Risky actions:**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| A3: replace helper bodies in `verify_workspace.py` | high (a fail-closed gate could turn permissive) | PR review plus the I1 golden comparison | revert the shipment PR |
| A4: add the `routing` CLI command | low | PR review | revert |
| A5: edit `_orchestrator` template, mirror, and manifest checksum | medium (paired-edit pair; checksum mismatch fails verify) | PR review | revert; re-run checksum refresh |

**Added verification (tightens the plan):**

* A1 vectors additionally record, for every case, the full `role_route_resolution` and
  `escalation_route_resolution` targeted-check dicts (including `per_role`, `ambiguous`, and
  `same_route_roles`) as produced by the current code, and A3 asserts equality after the
  refactor. This catches a changed result shape that per-helper vectors miss without adding
  files to A1. The whole-report before/after `verify-workspace` comparison for this
  workspace is a closure-time runtime verification (see the table above), not a committed
  fixture.
* A3 acceptance is stated as a negative as well: the diff must add no new `targeted_checks`
  key and must modify no file under `tests/` other than the new delegation test.
* A2 enforces the "no I/O" requirement with a guard harness, because running the resolver on
  a plain dictionary cannot show that it does not read a file or an environment variable:
  `forbid_io()` makes filesystem, `os.environ`, subprocess, and socket access raise during
  every resolver test call; negative self-tests with deliberately impure stubs prove the
  guard trips (including a stub that swallows the error); and a static import allowlist
  closes the import-time and function-local-import bypasses. Stdlib only, run by the
  canonical `unittest discover` gate.
* A4 pins UTF-8 and LF output (as `harness resolve` does) and asserts nothing is written to
  stderr on a successful parse, on Windows and Linux. Read-only (I5) is asserted rather than
  claimed: the test snapshots the fixture workspace tree (relative paths plus SHA-256 of
  every file's bytes) before and after each invocation and requires it to be identical.
* A4 maps exit codes explicitly: `0` resolved; `1` resolved with a declared degradation (the
  caller must use the route **and** surface the degradation); `2` unresolved or invalid
  (the caller halts that invocation).
* A5 states the `autoharness` executable-not-found case as `TOOL_DEGRADED`
  (`routing-resolver-cli`), not a silent skip, and states that exit `1` is not a failure.

**Closure and rollback detail:** monitoring signal is the shipment closure comparison of
`verify-workspace` before and after; rollback trigger is any I1 difference or any
pre-existing test edit; rollback is a revert of the single shipment PR; owner is Ship;
validation window is the PR review plus the first Orchestrator Stage/Ship invocation after
merge.

**Review-gate capability risks:** the Stage session that authored this plan has no reviewer
subagent dispatch surface, so plan review runs as `single-agent-declared-degradation`
(every selected persona applied inline, P-012 declared). The anchor reviewer route
(`model_routing.anchor_review`) is not dispatchable from this session, so the cross-model
personas run same-model with `TOOL_DEGRADED: model-specific-review-routing`. The review
section must carry literal `dispatch_mode:` and `decision:` markers; harvest halts without
them.

**Unresolved operator decisions that block safe execution:** none. Items needing operator
authority for later releases are recorded in `040-DL` (OQ1 to OQ9) with defaults (confirmed
2026-10-12, except OQ5 and OQ8 which remain open); none blocks R1-A.

## Plan Review

Review record: `docs/reviews/2026-10-11-model-routing-resolver-single-source-plan-review.md`
(two cycles; recorded 2026-10-12 UTC).

dispatch_mode: single-agent-declared-degradation

decision: PASS

* **Gate decision:** no P0 or P1 findings. Cycle 1 produced two P2 findings (A4 omitted
  schema validation from the fail-closed precheck; the Outcome over-claimed "single source
  of truth" while Stage/Ship escalation prose is unchanged) and three P3 findings. Both P2
  findings were fixed in this plan and re-verified in cycle 2.
* **Plan hardening:** required (`Requires plan hardening: yes`) and satisfied
  (`## Plan Hardening`).
* **Persona coverage:** Constitution, Python, Scope Boundary, Learnings (always-on, inline
  pass); Architecture Strategist and Agent-Native Parity (cross-model, same-model fallback,
  `TOOL_DEGRADED: model-specific-review-routing`); Security Lens judged not triggered. Every
  selected persona was covered under
  `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
* **Findings:** A-F1 and A-F2 (P2, fixed); A-F3 (P3, fixed); A-F4, A-F5, A-F6 (P3,
  acknowledged).
* **Runtime verification and closure:** specified for A3, A4, and A5; no gaps.
* **Addendum (PR #513 review-fix cycle 1, 2026-10-12 UTC):** A2 gained the purity guard and
  A1/A2 pin the empty-`model_provider` rule; A4's read-only claim is asserted by a snapshot
  test. A delta check recorded in the review record's addendum leaves the gate decision
  above unchanged (earlier cycle records are not altered).
* **Addendum (PR #513 review-fix cycle 2, 2026-10-12 UTC):** new unit A2a (`207.006-T`) holds
  the one shared raw-YAML guard that the A4 CLI calls before schema validation (exit `2` for
  an anchor, alias, or merge key under `model_routing` in a 1.2.0 config) and that R1-B B6
  reuses; A4 gains the exit-`2` regression test; invariant I8 added. A delta check recorded in
  the review record's addendum leaves the gate decision above unchanged (findings A-F9 to
  A-F11, all P3).
* **Addendum (PR #513 review-fix cycle 3, 2026-10-12 UTC):** no R1-A unit changed. The finding
  (thread `PRRT_kwDORzpWpM6rlcW8`) was fixed in R1-B (new unit B4a, `208.014-T`); A5 is
  cross-referenced there as the Orchestrator owner of the new invariant I11 (validate an
  operator config against the schema matching the document's own `schema_version`), and its
  text is unchanged. A delta check recorded in the review record's addendum leaves the gate
  decision above unchanged (finding A-F12, P3).

