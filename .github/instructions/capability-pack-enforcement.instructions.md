---
description: "Capability-pack usage-enforcement coordinator — cross-pack retrieval routing, precedence, exemptions, and sensitivity-aware fallback for retrieval-enforced packs (agent-engram, graphtor-docs)"
applyTo: '**'
---

# Capability-Pack Usage-Enforcement Instructions

This is a **thin coordinator** overlay for workspaces that enable one or more
**retrieval-enforced** capability packs. It owns the *cross-pack* concerns:
query **classification**, routing **precedence**, direct-tool **exemptions**,
sensitivity-aware **fallback**, and the **deviation-record format**.

It does **not** restate each pack's lifecycle, tool surface, freshness, or
fallback details.

<!-- safeguard:pack-deferral -->
## Deferral to Pack Instructions (authority)

For any pack listed in the routing table below, the pack's own instruction file
is **authoritative** for lifecycle checks, exact tool names, freshness/index
rules, and pack-specific fallback. This coordinator defers to:

<!-- BEGIN:capability-pack-deferral -->
* `.github/instructions/agent-engram.instructions.md` — engram lifecycle,
  indexed/semantic search, code-graph lookup, freshness. <!-- defer:agent-engram -->
* `.github/instructions/graphtor-docs.instructions.md` — graphtor-docs server
  lifecycle, indexed doc search, semantic retrieval, doc-link traversal. <!-- defer:graphtor-docs -->
<!-- END:capability-pack-deferral -->

When this coordinator and a pack instruction appear to conflict on a
pack-specific detail, the **pack instruction wins**. This coordinator only wins
on cross-pack classification, precedence, exemptions, and deviation format.

## Query Classification

Before a retrieval operation, classify the query and route it:

<!-- BEGIN:capability-pack-routes -->
| Query kind | Route to | Marker |
|---|---|---|
| Structural/conceptual **code** questions (symbols, callers/callees, blast radius, "where/how is X implemented") | **agent-engram** (indexed + code-graph search) | <!-- route:agent-engram --> |
| **Documentation / domain / business-context** questions (indexed docs, APIs, SoWs, process, data mapping, "what does the spec say") | **graphtor-docs** (indexed local documentation retrieval) | <!-- route:graphtor-docs --> |
<!-- END:capability-pack-routes -->

Mixed queries may use both packs. Route to the most specific pack first; widen
only if the specific route misses.

## Precedence

1. **Direct-tool exemptions** (below) always take precedence — never route an
   exempt query through a pack.
2. Otherwise route by the classification table to the **most specific** enabled
   pack.
3. Only after the routed pack misses (index gap, no result) do you consider the
   **sensitivity-aware fallback**.

<!-- safeguard:direct-search-exemptions -->
## Direct-Tool Exemptions

Direct tools stay first-class. Do **not** route these through a pack:

* **Literal-text / regex** search → use `grep`/ripgrep directly.
* **Known exact path** confirmation (you already know the file and want a
  line-level read) → open the file directly.
* Trivial single-file lookups where indexed search adds only latency.

These exemptions mirror the direct-search fallbacks already documented in the
individual pack instructions; this coordinator does not narrow them.

<!-- safeguard:per-phase-health-reuse -->
## Per-Phase Health Reuse

Verify pack/daemon/server reachability and index freshness **once per major
workflow phase** (or when results look wrong), then **reuse** that result for
the rest of the phase. Do **not** probe health before every individual call.
Follow each pack instruction for the exact lifecycle/status tool to call.

<!-- safeguard:internal-no-public-web -->
## Sensitivity-Aware Fallback

On an index miss, fallback depends on the **sensitivity** of the query:

* **Public / external** questions (open-source APIs, public standards, general
  library docs) may fall back to web search.
* **Internal business-context** misses (SoWs, internal design docs, process,
  data mapping, customer/deal specifics) **MUST NOT** be sent to public web
  search or any external service. Fall back to approved **local/internal**
  sources, or request that the missing source be configured/indexed.
* **Ambiguous sensitivity defaults to internal** — treat it as internal
  business-context and do **not** use public web (fail-closed on exfiltration
  risk).

## Deviation Record Format

When you deviate from a routed pack (exemption, fallback, or pack unavailable),
emit a **session-output** signal (not audited telemetry) so the decision is
legible:

```text
[PACK-ROUTING] query="<short>" classified=<code|docs|mixed> routed=<pack|direct|fallback> reason="<why>" sensitivity=<public|internal|ambiguous>
```

Deviation records are advisory observability signals. They do not require
operator approval, but they must be present when the routed pack is bypassed.

## Degraded Mode

If an enabled retrieval-enforced pack is unavailable, follow that pack's own
degraded-mode/fallback protocol. Continue with direct tools and the
sensitivity-aware fallback above; never send internal business-context to public
web to compensate for an unavailable pack.
