# Adversarial ideation: the primitive is sound, its trigger does not exist — build the deferral counter or do not build the agent

**Date**: 2026-08-25
**Artifact type**: Deliberation (decision artifact)
**Deliberation ID**: `030-DL`
**Intake**: stash `08D71FD5` (active, medium, feature)
**Related**: `028-DL` (termination/monotone measure), `029-DL` (convention survival law), stash `34AAF1C7` (5× deferral), stash `8AC574F1` (missing engine skills), stash `7628C291` (leaf-executor contradiction, spun off here)
**Route**: claude-opus-5 / anthropic / high (P-013.5)
**Scope**: deliberation only — no harvest, no shipment, no branch, no worktree (P-016)

---

## Conclusion up front

Build the primitive as a **new agent** named `adversarial-ideation`, **conditional on
shipping its trigger in the same unit of work**.

The design question that matters is not "agent or skill" — that is answerable in a
paragraph. It is: **what machine invokes this thing?** Today the answer is *nothing*,
and the trigger the intake assumed already exists (repeat-deferral detection) **does
not exist**. I verified this against `.backlogit/stash.jsonl`, the markdown/JSONL source
of truth, not against prose — and, after a correction round, not against the SQLite cache
either (§4.1b, §4.1c).

Under `029-DL`'s law, an ideation agent shipped without a producer or penalizer is a
cell-4 artifact with a measured decay trajectory. So this deliberation's real output is
a **conditional build with a named, checkable gate criterion** (§4.6), not an
enthusiastic yes.

This is **not** a deferral. It is a build recommendation with a precondition that is
itself specified, sized, and independently valuable.

---

## 1. Gap analysis — verified, with two corrections

I re-read every template rather than trusting the intake summary. The intake's
capability gaps (divergent generation, idea-level challenge, multi-round dialectic,
framing critique, anti-conservatism counterweight) are **confirmed**. Two of its
supporting claims are **wrong**, and one of them is load-bearing.

| Primitive | Intake claim | Verified | Evidence |
|---|---|---|---|
| `brainstorm/SKILL.md.tmpl` | Intake funnel; pressure-tests framing at §1.3; no independent challenger | ✅ Confirmed | L121–130 `Step 1.3 Frame and Pressure-Test`; zero matches for `adversar`/`round`/`counter`. The pressure-test is **self-administered by the same reasoner**. |
| `deliberate/SKILL.md.tmpl` | 2–4 options, single reasoner, no divergent expansion | ✅ Confirmed | L132 "identify 2-4 viable approaches"; L288 quality bar "At least 2 options". Zero matches for `adversar`/`challeng`/`round` in 309 lines. |
| `spike/SKILL.md.tmpl` | Narrow empirical investigation | ✅ Confirmed | — |
| `iterative-experiment/SKILL.md.tmpl` | Requires numeric metric command; inapplicable | ✅ Confirmed | 136 lines, metric/baseline/revert loop. |
| `adversarial-review.agent.md.tmpl` | Reviews artifacts vs. ruleset for defects; reuse target for consensus machinery | ⚠️ **Partially wrong** — see §2.3 | Consensus tiering is *agreement-seeking*; structurally single-round. |
| `learnings-researcher` | Tier 1 read-only retrieval | ✅ Confirmed | — |

**Correction 1 (§2.2)**: the premise "skills cannot dispatch" is **false in this
repository**. It is contradicted by two shipped skills.

**Correction 2 (§2.3)**: adversarial-review's consensus machinery is **not** safely
reusable in the divergent phase. Reusing it there *causes* the conservatism failure
this primitive exists to prevent.

---

## 2. Ruling: agent, not skill, not orchestrator-embedded

### 2.1 Against orchestrator-embedded — you are right, and the precedent is stronger than you argued

Upheld. The Orchestrator already has an exact structural slot for this, which makes
the argument mechanical rather than philosophical.

`.github/agents/_orchestrator.agent.md` L110–121 defines an **Elective Agents** table:
trigger phrases + routing rule + a concurrency guard, with all doing delegated to a
separate agent file (`auto-mergeinstall`, `auto-tune`). The Orchestrator holds *five
columns of routing metadata and zero lines of execution logic* for both. Embedding
ideation logic would make it the first Orchestrator capability that executes rather
than routes.

**However — one correction to the obvious next step.** This primitive must **not** be
registered as an *elective agent*. That contract explicitly states elective agents are
"**operator-initiated only**: never invoked autonomously" (L120). The durability
mechanism in §4 requires exactly the opposite — autonomous, gate-triggered invocation.
Registering it as elective would make the trigger contract self-contradictory on day
one.

Correct placement: a **Stage-invoked pipeline subagent** (Stage Step 2 routing),
*plus* an Orchestrator trigger phrase for direct operator entry. Two entry points, one
agent. This is a genuinely new row shape and the routing table needs a third category.

### 2.2 Against "craft anew" via the leaf-executor argument — right conclusion, false premise

Your stated reasoning was: *skills are leaf executors and cannot dispatch; genuine
challenge needs model diversity; therefore agent.*

**The middle premise is false.** Two shipped skills in this repo dispatch subagents
with cross-model routing:

- `templates/skills/review/SKILL.md.tmpl` L33–35: *"This skill spawns reviewer
  subagents… Maximum depth: review skill → persona subagent (1 hop)."* L159 spawns five
  always-on personas. L164 assigns an anchor reviewer route.
- `templates/skills/plan-review/SKILL.md.tmpl` L11–13: identical dispatch declaration.

These directly contradict `harness-architecture.instructions.md` L163 ("Skills are leaf
executors (no subagent spawning)") and `role-enforcement.instructions.md` L81. The rule
is asserted in two instruction files and violated by two skills. *That contradiction is
itself a defect worth a separate entry — see §7.4.*

**The conclusion survives on a sound premise: route-declaration authority.**

`role-enforcement.instructions.md` L81 (P-013.5) states the part that is actually
enforced: skills *"do not declare their own `model_family` / `model_provider` /
`reasoning_effort` frontmatter"* and a skill *"runs **inside the invoking agent's
already-routed session**."*

The consequence is visible in the code. `review/SKILL.md.tmpl` L136 must hedge:

> "Use a different model from the caller when available… **Cross-model is preferred but
> not blocking.**"

It hedges because it *structurally cannot guarantee* diversity — it has no frontmatter
in which to declare a route. It can request diversity and silently proceed without it.
Contrast `adversarial-review.agent.md.tmpl`, which declares **eight** routing fields in
frontmatter (`model_provider`, `model_family`, `alt_review_*`, `anchor_review_*`,
`reasoning_effort`, `subagent_depth`).

Now apply your `ESCALATION_DEGRADED` analogy — which is *tighter* than you claimed. The
same-route no-op is not merely an aesthetic parallel; `install-harness/SKILL.md` L437
defines it as a **fail-closed resolution outcome**: when the resolved route tuple equals
the acting role's own route, the result is `ESCALATION_DEGRADED` and the agent **halts
to the operator rather than proceeding**. It is a detected, named, halting condition.

A skill-shaped ideation loop degrades to self-challenge **silently and undetectably**,
because it never resolved a route to compare against. An agent-shaped one can declare
challenger routes, compare tuples, and emit `IDEATION_DEGRADED: same-route challenger`
by exactly the existing mechanism.

**Ruling: agent — because only agents can *declare and verify* routes, not because only
agents can dispatch.** Same verdict, load-bearing premise replaced. The distinction
matters: had the design rested on the dispatch premise, the first reviewer to cite
`review/SKILL.md` would have collapsed the justification.

### 2.3 Against wholesale craft-anew — right in direction, wrong about which parts reuse

You argued adversarial-review already implements consensus tiering and rebuilding it is
duplication. Reuse is correct for *part* of the loop and **actively harmful** for the
rest.

adversarial-review Phase 3 assigns confidence by **agreement count**: HIGH = flagged by
all reviewers; **LOW / "unique" = flagged by exactly one**. Phase 4 then scores
`confidence_weight × severity_weight`, where LOW = 1. Minority positions are
systematically down-weighted 3× relative to unanimous ones.

That is correct for defect detection — an issue all models see is probably real. It is
**inverted for divergent ideation**:

- An idea every challenger converges on early is usually the *conventional* one.
- The highest-value move in the motivating session (framing critique) would have been a
  **unique** finding — LOW confidence, priority score 1 — and would have been sorted to
  the bottom of the queue.
- Agreement-weighted scoring applied to ideas *is* a conservatism amplifier. `34AAF1C7`
  reaching an identical defer verdict across four independent triages is what
  consensus-seeking over ideas produces: reliable, reproducible, and wrong.

Additionally, adversarial-review is **structurally single-round**: Phases 1–6 run once,
with a re-review capped at 2 cycles *over remediated files*. That is a verification
retry, not a dialectic. There is no position → challenge → defend → re-challenge loop
and no convergence measure.

**Ruling on reuse:**

| Machinery | Verdict |
|---|---|
| Parallel multi-route subagent dispatch (Phase 2) | **Reuse directly** |
| Model route assignment table + anchor/alt fallback + declared degradation (Phase 1) | **Reuse directly** — this is where `IDEATION_DEGRADED` comes from |
| Structured-JSON-only subagent returns | **Reuse directly** |
| Consensus/majority/plurality/unique tiering | **Reuse in convergent pruning only (§3, Phase E)** |
| `confidence × severity` scoring | **Invert for divergence**: preserve unique positions at full weight; never prune an idea for being held by one challenger |
| Capped re-review cycle | **Replace** with the monotone measure in §5 |

So: not "craft anew", not "extend in place". **Compose**: a new agent that dispatches
via adversarial-review's proven routing machinery and supplies the genuinely new parts
(round loop, novelty ledger, framing phase, advocacy floor).

---

## 3. Loop shape

Five phases, with a **round ledger** as the connecting datum.

**Phase A — Framing critique (1 round, no loop).**
A framing-attacker challenger on a route distinct from the caller receives only the
problem statement. It must answer: *is this question correctly posed?* Output: `FRAMING_OK`,
or a named reframing with the specific defect. A reframing **restarts Phase B against the
new frame** and is recorded. Rationale: this was the single highest-value move in the
motivating session and it must run before option generation, not as a critique of options.

**Phase B — Divergent over-generation.**
Target ≥ 6 candidate directions (vs. `deliberate`'s 2–4), explicitly including at least
one that violates a stated constraint, flagged as such. Over-generation is the
counterweight to `deliberate`'s single-reasoner narrowness. No scoring, no pruning, no
challenger in this phase — evaluation here is what collapses the space prematurely.

**Phase C — Independent challengers on distinct routes.**
Three fixed core stances (§6.4) dispatched in parallel, each on a **distinct resolved
route tuple**. Each returns structured challenges only:

```json
{"stance":"framing-attacker|aggressive-advocate|conservative-skeptic",
 "target_claim":"verbatim claim being challenged",
 "challenge":"the argument",
 "evidence_demanded":"what measurement would settle this",
 "novel":true}
```

`target_claim` being **verbatim and mandatory** is what makes subsumption checkable in §5.
A challenge with no `target_claim` is not substantive and does not count toward `N_r`.

**Phase D — Defend or adopt-with-evidence.**
For each challenge the position-holder must return exactly one of:
`DEFEND` (with argument), `ADOPT` (position revised, revision recorded), or
`ADOPT_PENDING_EVIDENCE` (a named measurement is run, then defend or adopt on the result).

`ADOPT_PENDING_EVIDENCE` is the mechanism that produced this session's two reversals —
both were driven by *new measurements taken in response to challenge*, not by rhetoric.
Preserving it is the highest-value part of the design. A `DEFEND` that ignores an
`evidence_demanded` field where the measurement is cheap and available is a protocol
violation, not a defence.

Loop C→D until the §5 termination rule fires.

**Phase E — Convergent pruning with a named #1.**
Only here does consensus tiering apply. Output: a ranked list with **one named #1
recommendation**, every surviving minority position preserved verbatim with its
challenger and rationale, and every reversal logged with the round and evidence that
caused it. "No named #1" is not a permitted output — that is the deferral failure mode.

---

## 4. Durability — the make-or-break section

`029-DL`: *a convention survives iff a machine either PRODUCES it or PENALIZES ITS
ABSENCE. Being read is neither necessary nor sufficient.*

### 4.1 The proposed trigger does not exist. I checked the schema.

> **CORRECTED 2026-08-25 (round 2).** The first version of this section rested on three
> facts, two of which were wrong because they were read from the **SQLite cache instead
> of the markdown/JSONL source of truth**. The conclusion is unchanged and the corrected
> facts make it *stronger*. See §4.1b for the correction and §4.1c for the worked example.

The task proposed repeat-deferral as the trigger, on the basis that `34AAF1C7` was
re-triaged four times and that this is "mechanically detectable from stash/deliberation
history." **It is not.**

Source of truth — `.backlogit/stash.jsonl`, 13 active entries, field union:

```
created_at, deliberation_id, id, kind, priority, text
```

Two findings, each sufficient on its own:

1. **`deliberation_id` is a scalar, not a list.** `34AAF1C7` holds exactly one value —
   `028-DL` — despite four-plus documented re-triages. Every prior deliberation ID was
   overwritten or never written. The history is *destroyed by the schema*, not merely
   unqueried. **(This finding was correct in v1 and stands unchanged.)**
2. **There is no triage or deferral counter.** No `triage_count`, no `deferral_count`, no
   per-triage event record. Nothing to threshold against.

And the fact that replaces the two withdrawn ones:

3. **`created_at` exists, is correctly populated, and still cannot answer the
   question.** Values are genuine and monotonic — `34D50F2D` 08-02, `34AAF1C7` 08-12,
   `08D71FD5` 08-25 20:08, `8AC574F1` 08-25 20:51, `7628C291` 08-25 21:05. The CLI even
   surfaces a derived `age_days`. But **age is not triage count.** `created_at` cannot
   distinguish "deferred five times over two weeks" from "sat untouched for two weeks" —
   and that discrimination is precisely what the trigger needs. A `blocked_stale`-style
   age threshold over `created_at` would fire on every old entry regardless of whether
   anyone ever looked at it, which is a different and much weaker signal than
   repeat-deferral.

This is the sharper form of the argument: the stash surface has a **working, accurate
timestamp that is still structurally incapable of expressing the predicate**. The gap is
not a missing or broken field — it is a missing *event log*. See §4.3.

### 4.1b Correction of record

| v1 claim | Status | Actual |
|---|---|---|
| "no `created_at`" | ❌ **WRONG** | `created_at` exists in `stash.jsonl` and is correctly populated with distinct, monotonic values |
| "`updated_at` is identical across all three live entries — a re-index stamp" | ❌ **WRONG** | `updated_at` **does not exist** on stash entries in the source of truth, nor on the CLI surface. There was nothing to be identical. |
| "`deliberation_id` is a scalar" | ✅ **STANDS** | Confirmed against `stash.jsonl`; `34AAF1C7` holds only `028-DL` |

Neither withdrawn fact was load-bearing for the conclusion, and fact 3 above is a
stronger replacement than either.

### 4.1c Worked example: the cache-vs-source-of-truth hazard, demonstrated

`029-DL` established that **the SQLite index is a disposable cache rehydrated from
markdown; markdown is the source of truth.** This section committed exactly that error,
two sessions after that correction was written, *by the same agent that wrote it*. It is
recorded here because a hazard that catches its own author is better evidence than any
assertion of the rule.

**What happened.** I queried `sqlite_master` and `stash_entries` in the backlogit index
and reported the result as "the live schema." The three surfaces do not agree:

| Surface | Fields |
|---|---|
| `.backlogit/stash.jsonl` (**source of truth**) | `created_at`, `deliberation_id`, `id`, `kind`, `priority`, `text` |
| CLI `stash get` | `id`, `priority`, `kind`, `text`, `age_days` (+ `deliberation_id` when set) |
| SQLite `stash_entries` (**cache**) | `stash_id`, `priority`, `kind`, `text`, `deliberation_id`, `state`, `source_path`, `updated_at` |

The cache diverges from source in **both directions at once**:

* it **invents** `updated_at`, which exists nowhere in source — it is rehydration
  bookkeeping, not domain data;
* it **drops** `created_at`, which does exist in source — which is why the cache-derived
  reading produced the false negative "there is no creation timestamp."

**The clincher — the evidence was manufactured by the act of measuring.** The uniform
timestamp I cited (`2026-08-25T20:55:46.09`, identical across the three entries I
sampled) was written by **my own Step 0.1 `backlogit sync`** at session start. On
re-query after this session's later writes, `08D71FD5.updated_at` had moved to
`2026-08-25T21:07:10.12`. The column also carries mixed timezone representations across
rows (older entries at `-07:00`, freshly-touched ones `Z`-normalized), which is
incidental cache metadata leaking through. **I measured my own tool invocation and
reported it as a property of the domain.**

**Transferable rule, stated for reuse:** *a claim about what a schema does or does not
record must be verified against the markdown/JSONL source of truth. The SQLite index may
be used to find and count things; it may never be used to establish absence of a field,
because it is lossy in both directions — it drops source fields and adds its own.* A
field whose values are suspiciously uniform across unrelated rows should be treated as
rehydration bookkeeping until proven otherwise.

This belongs in `docs/compound/` independently of whether the ideation agent is built.

### 4.1d The residual finding

The only record of the deferral history is **append-only prose inside the `text` blob**,
self-narrated by Stage under an ad-hoc header it invented:

> `[STAGE DARK-FACTORY RE-TRIAGE 2026-08-14 …]` … `[STAGE DARK-FACTORY RE-TRIAGE 2026-08-15 …]`
> "This is a third independent Stage triage reaching the same conclusion…"

### 4.2 Cell placement — the honest answer

That prose convention is **read-but-tolerated**: agents read it, nothing produces it,
nothing penalizes its absence. `029-DL` cell 3, measured trajectory 0→18→59→**41%**,
already decaying.

So the proposal as framed puts **two** artifacts in decaying cells: the trigger
convention in cell 3, and an ideation agent that nothing invokes in cell 4 (AC-block
trajectory 0→22→62→52→**15%**).

**Stated plainly, as instructed: as framed, this is a cell-4 artifact and it will rot.**
The agent would be invoked during the session that builds it, demoed once, and then
never fire again — because the only thing that would fire it is a Stage agent
remembering to.

I am not recommending against building. I am recommending that **the trigger is the
deliverable and the agent is the payload**, and that they ship together.

### 4.3 The producer precedent already exists in this workspace

`.backlogit/hooks.yaml`, live and enabled:

```yaml
event_thresholds:
    blocked_stale_days: 7
agent_subscriptions:
    stage:
        - feature_review_ready
        - blocked_stale
```

This is a **machine crossing a threshold, emitting an event, and pushing it to Stage**.
Stage does not remember to check for stale blocked items; it is *told*. That is a
working cell-1/cell-2 mechanism in the same config file, and it is the exact template
the ideation trigger should copy. The design does not need a novel mechanism — it needs
the existing one extended to a surface that currently lacks it.

**The root cause is a surface asymmetry, and the correction in §4.1 sharpens it.**
Items have a full event log — `item_log_entries(item_id, timestamp, actor, event_type,
content, delta_json)` — so an item's history is a *sequence of recorded events*. A stash
entry has exactly **one** timestamp, `created_at`, and no log table at all. That single
timestamp is accurate and usable; it simply answers a different question. Age is a
**point**, deferral count is a **sequence**, and no point-valued field can encode a
sequence no matter how correctly it is populated.

That is why `blocked_stale_days` works on items and has no stash analogue: it thresholds
over an event history that the stash surface does not keep. Deferrals happen on the one
surface with no log. **The missing thing is an event log, not a missing or broken
field** — which is precisely why D2 (§4.4) attaches the counter to `item_log_entries`
rather than trying to add another column to the stash.

### 4.4 Three durability options, ranked

**D1 — Upstream schema change (strongest, not owned).**
Add `deferral_count` + an append-only `deliberation_ids` list to the **stash
source-of-truth record** (`stash.jsonl`, not merely the index projection); emit a
`repeat_deferral` hook at threshold ≥ 2, subscribed by Stage exactly as `blocked_stale`
is. Cell 1 (produced).
**Blocking risk: autoharness does not own backlogit.** `.autoharness/backlog-registry.yaml`
abstracts it as `tool_name: "backlogit"`; the binary is external (v1.10.1); no backlogit
source exists in this repo (all 66 `.go` files are in the gitignored `references/`
checkout, which does not contain it). This is an upstream feature request with unbounded
latency. **Do not make the build depend on it.**

**D2 — Harness-owned counter via item materialization (the substrate).**
On a defer decision, Stage materializes the entry as a deferred item and appends a
`deferred` event to `item_log_entries` — a table that already exists and already records
`actor` and `event_type`. The counter becomes a one-line query:

```sql
SELECT item_id, count(*) AS deferrals FROM item_log_entries
WHERE event_type = 'deferred' GROUP BY item_id HAVING deferrals >= 2
```

No upstream change. Machine-written, not narrated. **This is the substrate D3 checks.**

**D3 — Penalizer via `verify-harness` (the durable minimum).**
`verify-harness` is **installed in this workspace** (one of only four engine skills) and
is already a PASS / PASS-WITH-WARNINGS / **FAIL** machine with adversarial multi-reviewer
consensus. Add a check: *any item with ≥ 2 `deferred` events and no linked ideation
artifact → FAIL.* Absence penalized. Cell 2 — the closure-artifact trajectory
0→68→91→**100%**, the strongest measured curve after machine production.

**Ruling: D2 + D3 ship with the agent. D1 is filed upstream and is not a dependency.**

### 4.5 A second, stronger producer — the P-006 analogue

There is a cell-1 (produced) mechanism already ratified in the Stage agent itself.
Step 3.3 reads a plan's `Requires plan hardening` field and — critically — **treats an
absent field as `yes` (fail-safe)**. The plan-generating machine *produces* the trigger
field; the consuming gate cannot be evaded by omission.

Direct analogue: `deliberate` and `impl-plan` artifacts emit
`Requires adversarial ideation: yes | no`, absent → `yes`. Signals: high blast radius,
≥ 2 prior deferrals, or a single-reasoner option set of ≤ 3.

**Honest limitation**: `impl-plan`, `plan-review`, `harvest`, and `deliberate` are **not
installed in this workspace** (stash `8AC574F1`). This producer is therefore **inert
here** and only active in target workspaces with a full install. It is the better
long-term mechanism and the weaker short-term one. D3 does not share this limitation —
`verify-harness` is installed — which is why D3 is the durable minimum and this is the
complement.

### 4.6 Gate criterion (the named condition on the build)

> **The `adversarial-ideation` agent MUST NOT be harvested or shipped unless the same
> unit of work also delivers (a) a machine-written deferral counter (D2) and (b) a
> `verify-harness` check that FAILS on ≥ 2 deferrals without a linked ideation artifact
> (D3).**
>
> **If (a) and (b) are descoped, the recommendation inverts to DO NOT BUILD** — because
> a correct, elegant, uninvoked ideation agent is strictly worse than no agent: it
> consumes maintenance and review budget, appears in the primitive map as a solved
> problem, and suppresses future attempts at the same capability.

This is checkable at harvest time by a human or a gate, and it is a named criterion —
not a spike-first punt.

---

## 5. Termination — monotone measure and degenerate cases

`028-DL`: acyclicity implies termination only over a **finite fixed node set**; a dynamic
node set needs a **well-founded monotone measure**. Ideation generates ideas on demand
from a nondeterministic oracle — an open node set. A round cap alone is a blunt
instrument that cannot distinguish "converged" from "truncated".

### 5.1 Definitions

- **Round ledger** `L_r` — canonicalized set of substantive challenges accepted through
  round `r`.
- **Substantive** — a challenge with a non-empty verbatim `target_claim` that names a
  specific claim in the current position. Challenges without one are discarded, not
  counted.
- **Novel** — not subsumed by any entry in `L_{r-1}`. Subsumption is checked on
  `(target_claim, challenge)` semantics; a restatement in different wording **is**
  subsumed.
- `N_r` = count of substantive **and** novel challenges in round `r`.

### 5.2 The measure

`N_r` alone is **not** well-founded — a challenger can oscillate 3 → 5 → 3 indefinitely.
So novelty is the *quality* signal and a separate quantity carries *termination*:

```
B₀ = R_max          (R_max = 3)
B_r = min(B_{r−1} − 1, N_r)
terminate when B_r ≤ 0
```

`B_r ≤ B_{r-1} − 1` makes `B` a **strictly decreasing integer sequence bounded below by
0** — well-founded on ℕ, so termination is guaranteed in ≤ `R_max` rounds **regardless of
oracle behaviour**. The `min` with `N_r` makes it terminate *earlier* when novelty
collapses. Termination never depends on challenger cooperation; only earliness does.

`R_max = 3` reuses the repo's existing circuit-breaker constant (3 consecutive failures,
3 review-fix cycles, 3-attempt escalation) rather than introducing a new one.

### 5.3 Calibration against the one empirical trace

The motivating session measured 8 → 5 → 3 substantive challenges:

| r | `N_r` | `B_r = min(B_{r−1}−1, N_r)` | Action |
|---|---|---|---|
| 0 | — | 3 | — |
| 1 | 8 | `min(2, 8)` = **2** | continue |
| 2 | 5 | `min(1, 5)` = **1** | continue |
| 3 | 3 | `min(0, 3)` = **0** | **terminate** |

The rule reproduces the observed three-round session exactly, terminating on the round
where the ad-hoc loop actually stopped. That is one data point, not a validation — but it
is calibration against real measurement rather than assertion.

### 5.4 Degenerate cases

**Volume without novelty.** A challenger emits 20 challenges, all subsumed by `L_{r-1}`
→ `N_r = 0` → `B_r = 0` → terminate. Emit `TERMINATED: novelty_exhausted (round r)`.
Volume cannot extend the loop; this is why the measure counts novelty and not challenges.

**Two challengers deadlock.** If reciprocal re-assertion is genuinely non-novel, the
subsumption rule zeroes `N_r` and it terminates as above. If both sustain genuinely novel
arguments every round, `B_r` still forces termination at the cap — and the artifact emits
`UNRESOLVED_DISAGREEMENT` with **both positions preserved verbatim**. Forcing consensus
here would reintroduce exactly the agreement-seeking bias rejected in §2.3. An honest
recorded disagreement is a valid terminal state; a manufactured consensus is not.

**Advocacy collapse — the `34AAF1C7` failure mode, made mechanical.** If the
aggressive-advocate returns zero substantive positions in a round while the
conservative-skeptic returns > 0, emit `ADVOCACY_COLLAPSE` and **the verdict for that
round may not be `defer`**. This is the anti-conservatism counterweight expressed as a
checkable asymmetry rather than an exhortation. Five consecutive deferrals on a sibling
entry is direct evidence that an unenforced counterweight is no counterweight.

**Framing reset.** A `FRAMING_OK: false` verdict in Phase A restarts Phase B against the
new frame and resets `L_r` — the ledger is frame-relative, and challenges against a
discarded frame must not suppress novel challenges against the new one. **`B_r` does not
reset**, which bounds total work across resets and prevents reframing from becoming an
unbounded loop. At most `R_max` resets, and each consumes budget.

---

## 6. Integration surfaces

### 6.1 Template definition

`templates/agents/adversarial-ideation.agent.md.tmpl` — sibling of
`adversarial-review.agent.md.tmpl`, mirroring its frontmatter contract:

```yaml
name: Adversarial Ideation
maturity: experimental
tools: read, agent, search, edit
max_subagent_tier: 1
subagent_depth: 2
reasoning_effort: "{{TIER_3_REASONING_EFFORT}}"
model_provider: "{{TIER_3_PROVIDER}}"
model_family: "{{TIER_3_FAMILY}}"
challenger_alt_provider: "{{ALT_REVIEW_PROVIDER}}"
challenger_alt_family: "{{ALT_REVIEW_FAMILY}}"
challenger_anchor_provider: "{{ANCHOR_REVIEW_PROVIDER}}"
challenger_anchor_family: "{{ANCHOR_REVIEW_FAMILY}}"
```

`subagent_depth: 2` matches adversarial-review. Stage(1) → ideation(2) → challengers(3)
is already the operating norm (Stage → `review` skill → persona is the same depth).

### 6.2 Installed dogfood copy — a real decision, not a formality

**Finding**: `.github/agents/` contains **only five** files (`_orchestrator`, `_ship`,
`_stage`, `auto-mergeinstall`, `auto-tune`). `adversarial-review` and the eleven
`review/` personas have **no installed dogfood copy**. This workspace installs a
deliberate subset.

But the §4 durability mechanism requires Stage to invoke this agent *in this workspace*.
An uninstalled agent cannot be invoked, and the D3 gate would fail permanently on an
artifact that cannot exist. **Therefore `.github/agents/adversarial-ideation.agent.md`
MUST be installed here** — unlike adversarial-review, this one is not optional in the
dogfood set. This is a direct consequence of choosing a durability mechanism, and it is
the kind of coupling that is invisible until the gate starts failing.

### 6.3 `install-harness` variable table

Add rows to `.github/skills/install-harness/SKILL.md` (table at L425+, same block as
`{{ANCHOR_REVIEW_*}}` at L447–449 and `{{ALT_REVIEW_*}}` at L524–525):

| Variable | Source | Default |
|---|---|---|
| `{{IDEATION_ROUNDS_MAX}}` | `config.ideation.rounds_max` | `3` |
| `{{IDEATION_DIVERGENCE_MIN}}` | `config.ideation.divergence_min` | `6` |
| `{{IDEATION_DEFERRAL_THRESHOLD}}` | `config.ideation.deferral_threshold` | `2` |
| `{{IDEATION_MODE}}` | `config.ideation.mode` | `interactive` |

No new routing variables — challenger routes reuse the existing anchor/alt/tier set,
per §2.3.

### 6.4 Stances and modes (testing the two autopilot defaults)

**Fixed core stances, optionally extended — upheld.** Framing-attacker,
aggressive-advocate, and conservative-skeptic are always dispatched; topic-specific
challengers may be added. The reasoning is sound and now has a mechanical expression:
adaptive-only assignment permits the advocate to be quietly dropped, and §5.4's
`ADVOCACY_COLLAPSE` check is only meaningful if the advocate is *guaranteed present*. A
fixed roster is the precondition for the counterweight being checkable. The two defaults
are load-bearing on each other.

**Interactive by default, batch as the P-017 degradation — upheld with a
strengthening.** Recording challenge/response pairs as artifacts in both modes is
correct, but under §4's logic "the loop writes an artifact" is itself a convention that
needs a producer. It has one: the round ledger and `B_r` trace are **required inputs to
the termination rule**, not optional documentation. The agent cannot decide when to stop
without writing them. That places the audit trail in cell 1 (produced) rather than cell 4
— dark runs stay auditable because the artifact is *load-bearing for control flow*, not
because policy asks for it. That is the strongest form of the mechanism available here.

### 6.5 Primitive mapping

**This is a base-primitive deepening, not an 11th primitive** — required by the overlay
rules at `harness-architecture.instructions.md` L18 ("a capability pack may deepen one or
more primitives, but it must not redefine the primitive model").

| Primitive | Deepening |
|---|---|
| **4 — Orchestration, Delegation, Lifecycle Handoffs** *(primary)* | New dispatching agent in the Stage pipeline; new row in the Design Rules pipeline line at L161 |
| **3 — Model Routing and Escalation** | Route diversity is the core mechanism; `IDEATION_DEGRADED` extends the same-route no-op family |
| **7 — Observability and Evaluation** | Round ledger, `N_r`/`B_r` trace, and termination reason are first-class evaluation artifacts |
| **2 — Task Granularity and Horizon Scoping** | Feeds decomposition; over-generation counteracts premature narrowing |
| **8 — Workflow Policy** | The D3 gate is a policy-enforced precondition |

Primitive 4's pipeline line becomes:
`Brainstorm/Deliberate/Adversarial-Ideation/Spike → Plan → …`

### 6.6 Orchestrator trigger and routing rule

Trigger phrases: `adversarial ideation`, `brainstorm with pushback`, `challenge this
idea`, `ideate with challengers`.

Routing rule, given §2.1 — **a third category, not an elective-agent row**:

> Route to `adversarial-ideation` when (a) the operator uses a trigger phrase, **or**
> (b) Stage Step 2 receives a `repeat_deferral` signal at or above
> `{{IDEATION_DEFERRAL_THRESHOLD}}`, **or** (c) a plan or deliberation artifact declares
> `Requires adversarial ideation: yes` **or omits the field** (fail-safe, per §4.5).
> Unlike elective agents, autonomous invocation via (b)/(c) is **required**, not
> forbidden. Inherits the elective-agent concurrency guard: do not invoke while a
> shipment is `active`.

### 6.7 Docs

- `docs/design-docs/` — loop protocol and the termination proof sketch from §5.2.
- `harness-architecture.instructions.md` — Primitive 4 artifact list and pipeline line.
- `docs/compound/` — this artifact's §4 finding (deferral history is destroyed by the
  stash schema) is a reusable learning independent of whether the agent is built.

---

## 7. Gate verdict

**Deliberation: COMPLETE.** Gap analysis verified against files, two intake claims
corrected with citations, all seven deliverables addressed.

**Planning gate: NOT PASSED — machinery absent, not failed.**
`impl-plan`, `plan-review`, `harvest`, and `deliberate` are **not installed** in this
workspace (four engine skills only: `install-harness`, `tune-harness`, `verify-harness`,
`workspace-discovery`; stash `8AC574F1`). No impl-plan output is fabricated here and no
plan-review verdict is claimed. Deliberation itself was achievable without the
`deliberate` skill, as instructed.

**Recommendation: CONDITIONAL BUILD.**

**Build** `adversarial-ideation` as an agent (§2), with the loop of §3 and the
termination rule of §5 — **conditional on the §4.6 gate criterion**. The precondition
(D2 counter + D3 `verify-harness` check) is independently valuable: it makes *any*
repeat-deferral policy enforceable, including ones unrelated to ideation.

**Do not build** if the durability mechanism is descoped. Reasoned negative with named
criteria per §4.6 — an uninvoked ideation agent is worse than none, because it occupies
the primitive map slot while decaying.

### 7.1 What would falsify this recommendation

- Evidence that `deferral_count` already exists somewhere I did not query. Checked in the
  **source of truth**: `.backlogit/stash.jsonl` (all 13 active entries, full field union).
  Checked in the index and config: `stash_entries`, `stash_links`, `item_log_entries`,
  `gate_evidence`, `hooks.yaml`, `registry.yaml`. Checked on the CLI surface:
  `stash get`. Per §4.1c, only the first of these can establish **absence** of a field.
- A backlogit upstream commitment to D1 on a bounded timeline — would supersede D2.
- A demonstration that a skill can declare and *verify* its own route tuple, which would
  reopen §2.2's conclusion (though not its corrected premise).

### 7.2 Confidence

**High** on §1 (verified against files), §2.2 (direct citation), and §4.1 **as corrected**
(re-verified against `stash.jsonl`, the source of truth). The v1 confidence rating on this
section was itself miscalibrated — it read "High … (live schema and data)" while resting
on cache reads, which is the precise failure §4.1c documents. Confidence in a schema claim
may not exceed the authority of the surface it was read from.
**Medium-high** on §5 (measure is provably well-founded; calibration rests on a single
trace).
**Medium** on §4.4's D2/D3 split — `verify-harness`'s check-extension surface was
inspected at section level, not line-by-line.

### 7.3 Explicitly not a deferral

No spike is proposed. No "investigate first". The one genuine unknown — whether
`verify-harness` can host the D3 check — is resolvable during implementation, not a
precondition for deciding.

### 7.4 Spun off, not resolved here

The leaf-executor contradiction found in §2.2 (`review` and `plan-review` skills spawn
subagents while two instruction files forbid it) is a real defect in the instruction set,
independent of this design. Captured as stash **`7628C291`** (bug, medium) — either the
rule is overbroad and should be narrowed to the route-declaration half that *is* honoured,
or the two skills are in violation. This deliberation is not the place to rule on it.

---

## Provenance

Session 2026-08-25, branch `main`, HEAD `e697373d`. Stage route
claude-opus-5/anthropic/high. Deliberation-only: no harvest, no shipment, no branch, no
worktree (P-016). `.mcp.json` and `.backlogit/runtime/` untouched. `INDEX_SYNC_OK`
(967 artifacts). Intake stash `08D71FD5` remains **active** — not archived, since it is
not yet consumed into a backlog item.

**Correction round (2026-08-25, same session).** The operator challenged §4.1 and was
correct. Two of its three supporting facts were withdrawn — "no `created_at`" (false;
it exists and is correctly populated) and "`updated_at` is identical across entries"
(false; the field does not exist on stash entries in the source of truth). Both errors
originated in reading the SQLite cache rather than `.backlogit/stash.jsonl`. The scalar
`deliberation_id` finding stands. The **verdict is unchanged**: CONDITIONAL BUILD, with
inversion to DO NOT BUILD if the durability mechanism is descoped. The corrected facts
strengthen the argument — §4.1 now rests on a *working* timestamp that still cannot
express the predicate, which is a sharper claim than a broken one. The error itself is
recorded as §4.1c, a worked example of the `029-DL` cache-vs-source-of-truth hazard.
