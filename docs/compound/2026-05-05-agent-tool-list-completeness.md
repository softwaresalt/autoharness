---
problem_type: template-authoring
category: agent-design
root_cause: incomplete-tool-declaration
tags: [agent, frontmatter, tools, write-permission, sentinel]
created: 2026-05-05
shipment: 006-S
---

# Agent Frontmatter Tool List Must Include Write Tools

## Problem

A new standalone agent was created with `tools: read, search, terminal` in its frontmatter. The agent's workflow explicitly described persisting a report file to `{{DOCS_SECURITY}}/`. If the runtime enforces the `tools:` allowlist, the agent cannot write the file — the `edit` tool is absent.

The same agent also had a behavioral constraint that said "read and search only" — which directly contradicted the workflow step that writes the report file.

## Root Cause

The tools list was copied from a read-only analysis agent. The report persistence step was added to the workflow without updating the frontmatter. The behavioral constraint was phrased too broadly, catching the intentional write.

## Solution

1. Add `edit` to the `tools:` frontmatter list for any agent that creates or writes files.
2. Scope the "read only" behavioral constraint precisely:
   - ❌ `Do not modify source files or config files — read and search only`
   - ✅ `Do not modify source files or config files — read and search only for analysis. May create/write the audit report under {{DOCS_SECURITY}}/ — this is the only permitted write operation.`

## Rule

> Before finalizing any agent template: cross-check the `tools:` list against every workflow phase. If any phase creates or writes a file, `edit` must appear in the tools list. Behavioral "read only" constraints must name the specific scope they apply to, not blanket the entire agent.

## Applied In

- `templates/agents/security-sentinel.agent.md.tmpl` — added `edit`; tightened behavioral constraint scope
