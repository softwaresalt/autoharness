# V2 Model Routing Proposal

``` yaml
model_routing:
  # Base Fallback Tiers
  tier1: *claude-tier1-fast
  tier2: *claude-tier2-standard
  tier3: *gpt-tier3-architect

  # Orchestrator & State Machine Supervision
  orchestrator:
    <<: *claude-tier2-standard
    subagents:
      dispatcher: *claude-tier1-fast             # Deterministic state routing & queue polling
      checkpoint_manager: *claude-tier1-fast     # Snapshotting & state resumption
      conflict_evaluator: *claude-tier3-reviewer # Circuit breaker for oscillation/deadlocks

  # Stage: Discovery -> gpt-6.1-sol Architect -> Claude Reviewer -> Serialization
  stage:
    <<: *gpt-tier3-architect
    phases:
      discover: *claude-tier1-ingest             # Traversal & context bundling
      architect: *gpt-tier3-architect            # gpt-6.1-sol drafts -F/-S specs & DAG edges
      review: *claude-tier3-reviewer             # Cross-family gate: Claude (xhigh) checks Sol
      repair: *gpt-tier3-architect               # gpt-6.1-sol patches review-flagged defects
      materialize: *claude-tier1-fast            # Rapid emission of .backlogit/*-T.md files

  # Ship: Coding, Verification & Escalation
  ship:
    <<: *claude-tier2-standard                   # Sonnet 5.5 (medium) for 1st-pass implementation
    phases:
      context_slice: *claude-tier1-ingest        # AST-aware context slicing
      implement: *claude-tier2-standard          # Code generation & test implementation
      verify_triage: *claude-tier1-fast          # Parse test/build stderr output
    escalation:
      <<: *claude-tier2-repair                   # Escalates to Sonnet 5.5 (high, long_context)
      max_cycles: 2
      fallback: *gpt-tier3-architect             # Cross-family circuit breaker if Anthropic stalls

  # Cross-Family PR Gate
  anchor_review: *claude-tier3-reviewer          # Flipped to Claude (xhigh) against gpt-6.1-sol Architect

  # Capability Pack Subagents
  subagents:
    backlogit_ops: *claude-tier1-fast            # Backlog CRUD & dependency registration
    engram_curator: *claude-tier1-fast           # Context indexing & compaction
    graphtor_indexer: *claude-tier1-ingest       # Doc graph traversal & drift checks
    security_auditor: *claude-tier3-reviewer     # Static policy and security constraints
```
