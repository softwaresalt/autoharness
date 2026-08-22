---
title: "Never serialize raw operator-controlled content into JSON verification/report artifacts"
source: docs/compound/2026-08-15-never-serialize-raw-operator-content-into-json-reports.md
doc_type: learning
---

# Never serialize raw operator-controlled content into JSON verification/report artifacts

**Context**: shipment 134-S / feature 125-F (startup-script contract migration,
PR #340). `startup_script_contract.py`'s `classify_startup_script` extracts a
preserved "custom-section tail" from a legacy or customized `start.ps1`/
`start.sh` — exactly the block where operators configure environment
variables and custom commands (Claude Code config dirs, `OPENAI_API_KEY`
loading, etc.). The first implementation carried this raw tail text directly
into both the `classification` dict and the derived migration `proposal`
dict, both of which are stored verbatim in `verify_workspace`'s
`report["startup_script_contracts"]` / `report["migration_proposals"]` and
then `json.dumps()`'d to an on-disk verification report.

**Finding** (Copilot review, round 3 of 3 on PR #340): this duplicates
whatever secrets the operator's custom tail contains into logs/report
artifacts on disk — a real secrets-exposure risk, not merely a style nit.

**Fix pattern**: when a classifier/verifier needs to *prove it found and
preserved* sensitive operator content, carry a **non-sensitive summary**
(content hash + size metadata: `sha256`, `byte_length`, `line_count`) forward
into any structure that gets serialized to disk or logs — never the raw
content. Any consumer that needs to actually reattach/apply the preserved
content (a migration step, not the report) must **re-read the original file
from disk** at apply time; it must never source the content from the
proposal/classification/report structure.

**Generalizable rule**: before adding any field to a dict/struct that
eventually flows into `json.dumps()` for an on-disk report, verification
artifact, or log line, ask whether that field could ever contain
operator/user-controlled content from outside the tool's own template
(env var blocks, custom command sections, config snippets, free-text
descriptions a human wrote for their own environment). If yes, summarize
(hash/size/count) rather than embed verbatim, and document in the surrounding
code comment *why* — the same reviewer (human or Copilot) will otherwise
flag every subsequent similar pattern in the same module.

**Regression test shape**: plant a synthetic secret token (e.g.
`AKIA_FAKE_SECRET_TOKEN_...`) in the sensitive content, run the
classification/serialization path, and assert `assertNotIn(secret_token,
json.dumps(structure))` for every structure that reaches disk. This is a
stronger and cheaper check than asserting on the summary's shape alone.
