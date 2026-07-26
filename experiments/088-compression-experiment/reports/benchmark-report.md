# 088-F Compression Experiment — Benchmark Report

- Total cases: 13
- Compression-positive cases: 6
- Decline-control cases: 7
- SAFE WIN count (six-criteria compression-positive bar): 0
- Decline-control-correct count: 6 of 7

| Case | Category | Verdict | Notes |
|---|---|---|---|
| pytest-vv-experiment-suite | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| backlogit-doctor-findings | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| git-log-stat-history | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| backlogit-list-json-mcp-shaped | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| workspace-file-inventory | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| graphtor-search-results-representative | compression_positive | NOT a safe win | hook declined this case; not a compression candidate |
| tiny-output-decline | decline_control | DECLINE CORRECT | tiny_output |
| unwritable-store-passthrough | decline_control | INCONCLUSIVE (mechanism not exercised) | unwritable_store [INCONCLUSIVE: hook declined before store.put() was reached; unwritable-store passthrough not exercised this run] |
| secret-bearing-output-decline | decline_control | DECLINE CORRECT | secret_bearing |
| gate-readiness-verdict-decline | decline_control | DECLINE CORRECT | gate_readiness_verdict |
| failure-bearing-gh-run-view-representative | decline_control | DECLINE CORRECT | failure_bearing_success [synthetic-representative: emulates a failed `gh run view --log-failed` without depending on a live failed CI run] |
| active-stack-trace-decline | decline_control | DECLINE CORRECT | active_stack_trace |
| operator-approval-text-decline | decline_control | DECLINE CORRECT | operator_approval_text |

## Per-case criteria detail

### pytest-vv-experiment-suite (compression_positive)
- `compressed_at_all`: False

### backlogit-doctor-findings (compression_positive)
- `compressed_at_all`: False

### git-log-stat-history (compression_positive)
- `compressed_at_all`: False

### backlogit-list-json-mcp-shaped (compression_positive)
- `compressed_at_all`: False

### workspace-file-inventory (compression_positive)
- `compressed_at_all`: False

### graphtor-search-results-representative (compression_positive)
- `compressed_at_all`: False

### tiny-output-decline (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True

### unwritable-store-passthrough (decline_control)
- `declined_as_expected`: True
- `no_durable_row_on_decline`: True
- `unwritable_store_path_exercised`: False

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