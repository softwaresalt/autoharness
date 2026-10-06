---
title: "RED roster attribution: a roster test must reach its stub through its own specified behavior, not a discarded preamble"
problem_type: tdd-evidence
category: validation
root_cause: "To give every roster test its own NotImplementedError marker, the B5 tests each started with a discarded call that ran the CLI on a workspace named after the test. Three of them specified behavior that never needed the stub (argparse parse errors and help, and the 47 codes through an already-green resolver), so their RED came only from the preamble: characterization dressed as RED, which FI-9 and the Marker Convention refuse."
tags: [p-004, red-evidence, marker-convention, fi-9, roster, characterization, unittest, harness-architect]
shipment: 195-S
date: 2026-10-06
source: docs/compound/2026-10-06-red-roster-attribution-preamble-calls.md
doc_type: learning
---

## Problem

The Marker Convention gives each roster test its own marker
`<prefix>:<test>`, usually by deriving the suffix from the test's request (a
fixture workspace named after the test method). When a test's body works on
other workspaces, or never calls the stubbed entry at all, a natural shortcut
is a first line such as `run_cli(resolve_argv(self.ws))` whose only job is to
raise the test's own marker in RED.

In 195-S (B5) three of seven roster tests reached the stub only that way:

* a test that ran all 47 codes through `_resolve`, which B4b had already made
  green, so its body would have passed;
* the parse-error and `--help` tests, whose specified behavior is plain
  argparse and is decided before any resolver call.

The run looked clean (7 roster ERRORs with distinct markers), but the local
Constitution review classified it as a P1: those three were characterization
tests, and their RED proved only that the preamble ran.

## Solution

* Classify each test by asking whether its own specified behavior is missing
  before implementation. If the behavior is argparse, an already-green
  module, or anything a stub-raised marker cannot show as missing, the test
  belongs in a characterization class outside the roster, recorded as
  characterization or gap characterization.
* When a roster test needs a first call for marker attribution, make that
  call part of the specification and assert its result (for example, the
  baseline `ALL_SURFACES_PRESENT` document), so the call is a real check and
  not a discarded preamble.
* If the reclassification happens after the RED run of record, do not rewrite
  the RED commit. Record the reduced roster, the reason, and which pre-B5
  outcomes are inferred rather than observed, in the GREEN or review-fix
  commit body and in the session note.
* Keep the structural roster-count check in step with the roster class.

## Prevention

Before the RED run, list each roster test with the line that first reaches
the stub and the behavior it specifies. Any test whose first stub hit is a
line the test does not assert, or whose body would pass or fail without the
stub, is not a roster test.
