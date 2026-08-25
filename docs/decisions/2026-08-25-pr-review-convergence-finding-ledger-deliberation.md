---
title: "PR-Review Convergence: Finding Ledger + Epoch + Monotone Measure, with the DAG as Diagnostic Layer"
date: 2026-08-25
status: decided
source_stash: 34AAF1C7
deliberation_id: 028-DL
prior_spike: docs/decisions/2026-08-16-observable-termination-record-spike.md
related_artifacts: [001-SP, 110-F, 115-F]
lineage_pr: [229, 325, 328, 348]
source: docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md
doc_type: decision
artifact_kind: deliberation
agent: stage
route: claude-opus-5 / anthropic / high
---

# PR-Review Convergence: Finding Ledger + Epoch + Monotone Measure

* **Stash (living tracker)**: `34AAF1C7` — refined, linked, **not archived**
* **Deliberation artifact**: `028-DL`
* **Mode**: normal (non-dark) Stage deliberation; **strictly read-only**
* **Verdict**: **SPIKE-FIRST — with a now-executable spike.** Not planned, not
  hardened, not reviewed, not harvested. No shipment created.

## Scope and constraints

Read-only inspection of this repository plus backlogit query surfaces. No
source, template, schema, or config file was modified. No branch, worktree,
commit, push, or PR was created. **No spike/research worktree was created** —
the P-016 Stage exception was deliberately not exercised. Pre-existing dirty
worktree state (`.mcp.json`, `.backlogit/stash.jsonl`, `.backlogit/runtime/`)
was preserved untouched.

## 1. The intent, stated precisely

Make issue-resolution convergence during the PR review cycle **measurable and
observable**, so that a review loop can be *shown* to be converging, stalled,
or diverging — rather than being terminated by operator fatigue.

The operator's hypothesis under test:

> Use backlogit's SQLite database to record DAG nodes that track
> issue-resolution convergence during the PR review cycle, because DAG work
> items relate naturally to code/documentation implementation.

**Verdict on the hypothesis**: the *instinct* is right and materially advances
this entry — it re-aims the problem at PR review, where node identity is
externally solved. But the *architecture as literally stated* is wrong on three
counts, and **a DAG alone cannot deliver the stated intent.**

## 2. Central finding — why a naive DAG is insufficient

**The observed non-termination is not state revisitation.** A visited-set or
cycle detector would have fired *zero times* across every motivating incident.

The evidence is direct and unambiguous:

* `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`:
  "fixing one finding often surfaces a new, real finding on the very next pass
  (either a mirror bug in the same fix, or a consequence of the fix itself)."
* `docs/compound/093-S-review-loop-convergence.md`: 13 rounds; the final
  "bounded convergence pass" fixed 4 deferred + 5 new findings and **still**
  surfaced 2 more genuine hard blockers.

Every node is genuinely **new**. The process is not looping — it is a
**non-terminating productive descent under a regenerating external oracle**.

The formal error is precise:

> **Acyclicity implies termination only over a finite, fixed node set.**

Here the node set is not fixed. It is generated on demand by Copilot as a
function of the current HEAD, and is therefore unbounded. Termination requires
a **well-founded monotone measure that strictly decreases** — which acyclicity
does not provide and cannot provide. Conflating *acyclic* with *terminating* is
the naive-DAG error in one line.

### 2.1 Second error — four distinct graphs collided into one

| # | Graph | Nodes | Edge semantics | Identity | Status in this repo |
|---|---|---|---|---|---|
| 1 | **Work-item dependency DAG** | shipments/tasks | "must ship after" | assigned by backlogit | **Already exists.** `item_deps`, 488 `blocks` edges; reader = `autoharness gate dag-readiness` with cycle detection, ready-set, critical path, transitive closure |
| 2 | **Review-finding / evidence graph** | review findings | supersedes, regression-of, caused-by | **externally assigned (GitHub thread node ID) — solved for free** | **Does not exist** |
| 3 | **Reasoning-state graph** | agent epistemic states | state transitions | **unsolved** — the blocker across four prior triages | Does not exist |
| 4 | **Execution/event history** | events | temporal succession (a *sequence*, not a graph) | monotonic id | **Already exists.** `item_log_entries` (append-only, FTS); `src/autoharness/telemetry/` |

The proposal collides graph (2) with graph (1)'s storage and graph (3)'s
ambition. Graph (2) is the correct target — and it is the **only one of the
four where node identity is already solved**, because GitHub assigns stable
review-thread node IDs.

### 2.2 Third error — the storage target is disposable

`.github/instructions/backlogit.instructions.md` (Data Ownership Rule):

> Treat backlogit's markdown files as the current-state source of truth, its
> query index as a **disposable cache**, and its event or telemetry streams as
> append-only tool-managed history.

`backlogit_sync_index` rehydrates SQLite **from markdown** — it rehydrated 963
items during this session alone. Convergence records written *only* to that
SQLite are destroyed by the next sync. **Writing them there is a data-loss
architecture** unless the ownership contract is deliberately changed, which is
a separate and far larger decision.

Note the near-miss precedent: backlogit's `gate_evidence` table (354 rows;
`item_id` PRIMARY KEY, columns `gate_status`/`evidence_sha`/`head_sha`) has
exactly the right **HEAD-pinning** idea — but its primary key means one row per
item, overwritten. It is a *latest-snapshot* table and **cannot carry a round
series**, so it cannot measure convergence either.

## 3. The gap the existing gates leave open

`src/autoharness/gates/copilot_review.py` is a fail-closed pre-merge gate that
verifies Copilot review completed **for the current HEAD** and that every
Copilot-authored thread is resolved.

**This is a current-state predicate, not a convergence measure.** It answers
"is the frontier empty *right now*?" It never answers "is the frontier
*shrinking*?" Consequently it passes cleanly on the final round of a 15-round
divergent loop, and is structurally blind to exactly the failure this entry is
about.

That gap is the strongest evidence that something beyond the existing gates is
genuinely needed — and it defines precisely what that something must compute.

## 4. Motivating evidence — four independent non-terminations

| PR | Rounds | How it actually ended |
|---|---|---|
| #325 | 15+ Stage review passes | **Operator authority** |
| #229 (093-S) | 13 Copilot rounds | Operator-introduced **push-cap protocol** |
| #328 (128-S) | 5 rounds, 21 threads | **3-of-3 cycle cap** consumed; round 5 still finding |
| #348 | 7 rounds, 2 sessions | Breaker **deliberately exceeded twice** under narrow operator authorization |

In every case the terminator was **operator authority or a counting cap** —
never a convergence property of the process.

### 4.1 A mechanism the operator already discovered, worth preserving

From `093-S`:

> **Resolving does not re-trigger.** `resolveReviewThread` (GraphQL) and
> `gh pr edit --body` do **not** cause a new Copilot review round; only a
> `git push` of new commits does.

This is decisive for the model: **push, not thread resolution, is the epoch
boundary.** Any convergence measure must be keyed on HEAD, not on resolution
events. This is direct empirical support for HEAD-keyed epochs.

## 5. What a DAG alone cannot guarantee

| Property | Why a DAG does not give it | What does |
|---|---|---|
| **Termination** | acyclicity ≠ termination over an unbounded node set | a well-founded, strictly decreasing measure |
| **Progress** | edges record structure, not trend | monotonicity over a round window |
| **Fixed point** | no notion of "same input, no new output" | idempotence check: review over unchanged HEAD yields nothing new |
| **Oracle stability** | assumes a deterministic node generator | Copilot is nondeterministic — any fixed point is *probabilistic*, not logical |
| **Freedom from thrash** | — | causal `regression_of` edges + SCC detection — **the one place the DAG genuinely earns its keep** |
| **Scope discipline** | models resolution, not disposition | P-021 C1 verdict + C2 capture on every terminal state |

The last row matters more than it looks. Under P-021 a finding can be
**genuine and legitimately out of scope**. "Unresolved" and "not converged"
are therefore *different predicates*, and any model that equates them will
mis-classify correct behaviour as divergence.

## 6. Options considered

* **A — Reasoning-state visited-set/DAG** (original framing). *Rejected for
  this use case*: requires solving reasoning-state identity, and would not fire
  on the observed failures.
* **B — Extend the work-item DAG.** *Rejected*: conflates plan-time sequencing
  ("must ship after") with runtime evidence ("was raised, then superseded"),
  and would pollute the dag-readiness contract, which carries a documented
  permanent no-scheduler NON-GOAL.
* **C — DAG nodes in backlogit SQLite** (operator hypothesis, literal form).
  *Rejected as stated*: disposable-cache violation; also forces backlogit to
  learn what a "Copilot review finding" is.
* **D — Finding ledger + state machine, no graph.** Strong, but cannot explain
  *why* a loop fails to converge, nor detect fix-A-regresses-B thrash.
* **E — Event log + materialized graph.** Strong on replay/recovery, matches
  the telemetry precedent, but heaviest and presumes a validated model.
* **F — HYBRID (recommended target).** See below.
* **G — Retrospective-only analyzer (MVE).** Cheapest possible falsification.
  See below.

## 7. Recommended architecture (Option F)

> **ledger + epoch + measure delivers TERMINATION; the DAG delivers
> EXPLANATION.**

The operator's DAG is the **diagnostic layer**, not the convergence layer.
That is the direct answer to "is this a naive DAG that misses other
mechanisms?" — yes, and the missing mechanisms are **epoch pinning**, the
**monotone measure**, and the **disposition state machine**.

1. **Finding ledger** — the primary object. Keyed on GitHub thread node ID.
   Per-finding lifecycle: `open → fixed | declined | deferred (P-021 C2
   capture) | superseded`. All four terminal states are legitimate.
   Convergence = every finding terminal.
2. **HEAD-pinned epochs (rounds)** — findings belong to a round keyed on
   `head_sha`. This is what makes *new vs. carried-over* computable at all.
3. **Monotone measure + fixed-point check** — the actual termination witness.
   `new_findings(round n)` over a 3-round window. Converging iff trending to
   zero; diverging iff non-decreasing.
4. **DAG edges as diagnostics** — `supersedes`, `regression_of`, `caused_by`.
   These explain *why* the measure is not decreasing (thrash vs. genuine
   depth). **SCC detection over `regression_of`** catches the one genuine cycle
   that can actually occur here: fix A breaks B, fix B breaks A.
5. **Disposition binding** — every terminal state carries its P-021 C1 verdict
   and, where applicable, its C2 capture reference.

## 8. Cross-repo boundary (interface contract)

| Concern | Owner |
|---|---|
| Generic persistence, query, link storage, append-only item logs | **backlogit** |
| Finding schema, disposition state machine, measure, thresholds, verdict enum, P-018/P-021 binding | **autoharness harness** (`src/autoharness/gates/`, alongside `copilot_review.py`) |

**Rules so neither side embeds the other's policy:**

* backlogit MUST NEVER learn what a "Copilot review finding" is, what
  "convergence" means, or own a threshold.
* The harness reads and writes **only** through backlogit's public MCP/CLI
  operations (`append_comment`, item log entries, markdown sections) — **never**
  by direct SQLite writes.
* Notably, **the MVE requires zero backlogit change**, which is itself evidence
  the boundary is drawn in the right place.

## 9. Minimum viable experiment (Phase 1)

A read-only, **report-only** analyzer:

```bash
autoharness gate review-convergence <pr> --repo <owner/name> [--json]
```

Derives HEAD-keyed rounds from GraphQL review threads (the same query surface
`copilot_review.py` already uses), classifies each thread per round as
new/carried/resolved, and emits the `new_findings_per_round` series plus a
verdict: `CONVERGING | STALLED | DIVERGING | INSUFFICIENT_DATA`. **Always exits
0 in v0.**

### 9.1 Why this slice survives the 2026-08-16 spike's objections

| Prior finding | How this slice answers it |
|---|---|
| **F5** — no consumer ⇒ write-only emission ⇒ *appearance* of reliability | It is **reader-only**. There is nothing write-only about it — strictly stronger than the spike's "ship the reader in the same slice." |
| **F4** — prose-only bounds ⇒ emission edits every agent's contract surface | It changes **no agent-contract prose at all**. Blast radius dodged entirely. |
| Safety note — governing when agents stop is authority-expanding | It is **report-only**; it governs nothing. |
| "Don't attempt DAG/visited-set until real measurements exist" | Agreed — and this deliberation goes further: for PR review, duplicate-state detection is the wrong instrument *regardless* of measurements. |

### 9.2 The unlock that dissolves the four-session blocker

The 2026-08-15 annotation deferred this entry because answering it "requires
observing instrumented agent runs… no such instrumentation exists in this
workspace."

**For the PR-review framing, that blocker does not apply.** GitHub already
holds, retrospectively, the complete round-by-round review history of every PR
this harness has ever shipped — with stable thread node IDs supplying the node
identity that reasoning states lack. Merge commits are mandatory here (P-009;
squash and rebase forbidden), so commit history is preserved and rounds are
reconstructable.

**Nothing needs to be instrumented to answer the question.**

### 9.3 Falsification test (the gate on everything downstream)

Run the analyzer retrospectively against **PR #229** (13 rounds), **PR #325**
(15+, the motivating case), **PR #328** (5), **PR #348** (7), and **at least
two healthy PRs** with 0–1 rounds.

It **MUST** classify the pathological PRs `DIVERGING`/`STALLED` and the healthy
ones `CONVERGING`, using only data GitHub already holds.

> **If it cannot separate those populations retrospectively, the convergence
> model is falsified and this entry should be closed rather than staged
> further** — cheaply, and before any persistence, schema, or policy work is
> authorized.

## 10. Staged path

| Phase | Content | Gate |
|---|---|---|
| **1** | MVE analyzer (§9). Read-only, report-only. | Stage-ownable spike |
| **2** | Persist the ledger as markdown-backed sections on the existing backlogit `-R` review artifact type (13 already exist) + append-only `item_log_entries`; add `supersedes`/`regression_of` diagnostic edges with SCC detection. | **Only if Phase 1 separates the populations** |
| **3** | Allow a `DIVERGING` verdict to block; bind into P-018/P-021. | **Only with explicit operator consent — authority-expanding** |

## 11. Failure modes and open risks

* **R1 — Thread-ID instability.** If Copilot re-posts a materially identical
  finding under a new thread node ID after a push, carried-over detection
  silently breaks and every round looks new. Fallback secondary identity:
  `(path, normalized rule/message hash)`. The MVE will expose whether this is
  real.
* **R2 — Docs-only pushes re-trigger review.** `093-S` records round 11 as "a
  docs/backlog-only tracking commit with zero source changes" that still
  triggered a fresh round. Rounds must be classified by whether HEAD touched
  reviewable paths, or the count inflates with no code delta.
* **R3 — Suppressed/body-only findings are invisible.** The `128-S` closure
  records "4 suppressed-only (review-body text, no thread)". Thread-based
  measures systematically undercount these.
* **R4 — Oracle nondeterminism.** The same HEAD can yield different findings, so
  pairwise comparison is unsound; measure over a window.
* **R5 — `gate_evidence` is a snapshot, not a history** (§2.2). Its `head_sha`
  column is nevertheless the correct pinning precedent to imitate.
* **R6 — Recovery/replay and idempotency are deliberately unaddressed in Phase
  1.** Phase 2 must define stale-round handling, re-analysis idempotency, and
  schema versioning before any persistence lands.

## 12. Open questions requiring operator authority

* **Q1 (hard gate, authority-expanding)** — May a convergence verdict *ever*
  block a merge? Phase 3 only. The standing safety note across three prior
  triages reserves any mechanism that *governs* when agents stop reasoning for
  explicit operator consent, and spike finding F6 showed the **enforcing**
  variant is the valuable half.
* **Q2** — Is `DIVERGING` always pathological? `093-S` notes that "fresh
  containment/safety-critical code invites deep, iterative scrutiny." Genuine
  deep review of novel safety-critical code may legitimately diverge. If so the
  verdict must stay advisory for that class, and the classifier needs a
  novelty/criticality input it does not currently have.
* **Q3** — Does backlogit get *any* change at all? The MVE needs none. Phase 2
  might want a `regression_of` link type (backlogit currently supports
  `related_to`, `duplicate_of`, `informs`, `supersedes`, `spike_ref`) — a
  separate-repo change requiring separate authorization.
* **Q4** — Should `34AAF1C7` be **split**? This deliberation retires
  "duplicate-state detection over reasoning states" as the wrong frame *for the
  PR-review use case*, but reasoning-state identity remains a genuinely
  separate, still-unsolved concern. Recommended split: **(a)** PR-review
  convergence [now executable] and **(b)** reasoning-state identity [still
  blocked]. **Not executed this session** — splitting a living tracker is an
  operator-visible reclassification.

## 13. Relationship to the 2026-08-16 spike

This deliberation does **not** overturn
`docs/decisions/2026-08-16-observable-termination-record-spike.md`
(conclusion DEFER, confidence high). It **satisfies its stated conditions**.

The spike said a future slice becomes worth harvesting when it "carries a
consumer with it," recommended picking one bound with a natural carrier
artifact, and said to ship the reader in the same slice or neither. The MVE
here is **reader-only** — strictly stronger. The spike also said not to attempt
duplicate-state detection or DAG traversal until real measurements exist; this
deliberation agrees and goes further.

**What changed since 2026-08-16**: the operator supplied a sharper target — the
PR review cycle specifically — and that target has an externally-supplied
stable node identity that reasoning states lack. That single fact converts the
entry's central blocker from *unanswerable-without-instrumentation* to
*answerable-by-retrospective-analysis-today*. This is not a fifth restatement
of the same deferral.

## 14. Stage gate conclusion and disposition

**Requirements are NOT genuinely ready.** Q1–Q4 require operator authority,
R1–R6 are unresolved technical risks, and the convergence model itself is
unfalsified. Therefore: **no impl-plan, no plan-harden, no plan-review, no
harvest, no shipment** this session. The correct next instrument is the Phase 1
retrospective spike, which is Stage-ownable and read-only.

Stash `34AAF1C7` stays **ACTIVE at MEDIUM priority** as the living tracker,
refined and linked to `028-DL`. **Not archived.** Its blocker has changed from
"unanswerable without instrumentation that does not exist" to "answerable now
by retrospective analysis of existing GitHub history."
