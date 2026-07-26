# 088-F Compression Experiment — Benchmark Report

- Total cases: 13
- Compression-positive cases: 6
- Decline-control cases: 7
- SAFE WIN count: 7

| Case | Category | Verdict | Notes |
|---|---|---|---|
| pytest-vv-experiment-suite | compression_positive | INCONCLUSIVE (model tokenizer unavailable) | INCONCLUSIVE: model tokenizer unavailable -- criterion 1 (lower tokens under both tokenizers) cannot be proven, so this case is never reported as a safe win on fallback-only evidence |
| backlogit-doctor-findings | compression_positive | INCONCLUSIVE (model tokenizer unavailable) | INCONCLUSIVE: model tokenizer unavailable -- criterion 1 (lower tokens under both tokenizers) cannot be proven, so this case is never reported as a safe win on fallback-only evidence |
| git-log-stat-history | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| backlogit-list-json-mcp-shaped | compression_positive | INCONCLUSIVE (model tokenizer unavailable) | INCONCLUSIVE: model tokenizer unavailable -- criterion 1 (lower tokens under both tokenizers) cannot be proven, so this case is never reported as a safe win on fallback-only evidence |
| workspace-file-inventory | compression_positive | INCONCLUSIVE (model tokenizer unavailable) | INCONCLUSIVE: model tokenizer unavailable -- criterion 1 (lower tokens under both tokenizers) cannot be proven, so this case is never reported as a safe win on fallback-only evidence |
| graphtor-search-results-representative | compression_positive | INCONCLUSIVE (model tokenizer unavailable) | INCONCLUSIVE: model tokenizer unavailable -- criterion 1 (lower tokens under both tokenizers) cannot be proven, so this case is never reported as a safe win on fallback-only evidence [synthetic-representative: Engram/graphtor MCP search surface not running in this benchmark environment] |
| tiny-output-decline | decline_control | SAFE WIN | tiny_output |
| unwritable-store-passthrough | decline_control | SAFE WIN | unwritable_store |
| secret-bearing-output-decline | decline_control | SAFE WIN | secret_bearing |
| gate-readiness-verdict-decline | decline_control | SAFE WIN | gate_readiness_verdict |
| failure-bearing-gh-run-view-representative | decline_control | SAFE WIN | failure_bearing_success [synthetic-representative: emulates a failed `gh run view --log-failed` without depending on a live failed CI run] |
| active-stack-trace-decline | decline_control | SAFE WIN | active_stack_trace |
| operator-approval-text-decline | decline_control | SAFE WIN | operator_approval_text |

## Per-case criteria detail

### pytest-vv-experiment-suite (compression_positive)
- `byte_equivalent_retrieval`: True
- `no_extra_rows_beyond_stash`: True
- `lower_tokens_fallback`: True
- `lower_tokens_model`: False
- `lower_tokens_both`: False
- `model_tokenizer_available`: False
- `evidence_oracle_passes`: True
- `task_answerable_from_compressed_view`: True
- `capture_succeeded`: True
- `raw_tokens_fallback`: 5423
- `compressed_tokens_fallback`: 233
- `net_savings_tokens_fallback`: 5190
- `projected_savings_10_turns_fallback`: 51900

### backlogit-doctor-findings (compression_positive)
- `byte_equivalent_retrieval`: True
- `no_extra_rows_beyond_stash`: True
- `lower_tokens_fallback`: True
- `lower_tokens_model`: False
- `lower_tokens_both`: False
- `model_tokenizer_available`: False
- `evidence_oracle_passes`: True
- `task_answerable_from_compressed_view`: True
- `capture_succeeded`: True
- `raw_tokens_fallback`: 3654
- `compressed_tokens_fallback`: 401
- `net_savings_tokens_fallback`: 3253
- `projected_savings_10_turns_fallback`: 32530

### git-log-stat-history (compression_positive)
- `compressed_at_all`: False

### backlogit-list-json-mcp-shaped (compression_positive)
- `byte_equivalent_retrieval`: True
- `no_extra_rows_beyond_stash`: True
- `lower_tokens_fallback`: True
- `lower_tokens_model`: False
- `lower_tokens_both`: False
- `model_tokenizer_available`: False
- `evidence_oracle_passes`: True
- `task_answerable_from_compressed_view`: True
- `capture_succeeded`: True
- `raw_tokens_fallback`: 15000
- `compressed_tokens_fallback`: 250
- `net_savings_tokens_fallback`: 14750
- `projected_savings_10_turns_fallback`: 147500

### workspace-file-inventory (compression_positive)
- `byte_equivalent_retrieval`: True
- `no_extra_rows_beyond_stash`: True
- `lower_tokens_fallback`: True
- `lower_tokens_model`: False
- `lower_tokens_both`: False
- `model_tokenizer_available`: False
- `evidence_oracle_passes`: True
- `task_answerable_from_compressed_view`: True
- `capture_succeeded`: True
- `raw_tokens_fallback`: 13321
- `compressed_tokens_fallback`: 118
- `net_savings_tokens_fallback`: 13203
- `projected_savings_10_turns_fallback`: 132030

### graphtor-search-results-representative (compression_positive)
- `byte_equivalent_retrieval`: True
- `no_extra_rows_beyond_stash`: True
- `lower_tokens_fallback`: True
- `lower_tokens_model`: False
- `lower_tokens_both`: False
- `model_tokenizer_available`: False
- `evidence_oracle_passes`: True
- `task_answerable_from_compressed_view`: True
- `capture_succeeded`: True
- `raw_tokens_fallback`: 8827
- `compressed_tokens_fallback`: 323
- `net_savings_tokens_fallback`: 8504
- `projected_savings_10_turns_fallback`: 85040

### tiny-output-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### unwritable-store-passthrough (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### secret-bearing-output-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### gate-readiness-verdict-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### failure-bearing-gh-run-view-representative (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### active-stack-trace-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### operator-approval-text-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True