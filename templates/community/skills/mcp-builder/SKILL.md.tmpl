---
# Source: references/awesome-claude-skills/mcp-builder/SKILL.md
# License: see LICENSE.txt in source repo
name: mcp-builder
description: 'Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services.'
---

# MCP Server Development Guide

## Overview

To create high-quality MCP (Model Context Protocol) servers that enable LLMs to effectively interact with external services, use this skill. An MCP server provides tools that allow LLMs to access external services and APIs. The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks using the tools provided.

## High-Level Workflow

Creating a high-quality MCP server involves four main phases:

### Phase 1: Deep Research and Planning

#### 1.1 Understand Agent-Centric Design Principles

Before diving into implementation, understand how to design tools for AI agents:

**Build for Workflows, Not Just API Endpoints:**
- Don't simply wrap existing API endpoints - build thoughtful, high-impact workflow tools
- Consolidate related operations (e.g., `schedule_event` that both checks availability and creates event)
- Focus on tools that enable complete tasks, not just individual API calls
- Consider what workflows agents actually need to accomplish

**Optimize for Limited Context:**
- Agents have constrained context windows - make every token count
- Return high-signal information, not exhaustive data dumps
- Provide "concise" vs "detailed" response format options
- Default to human-readable identifiers over technical codes (names over IDs)
- Consider the agent's context budget as a scarce resource

**Design Actionable Error Messages:**
- Error messages should guide agents toward correct usage patterns
- Suggest specific next steps: "Try using filter='active_only' to reduce results"
- Make errors educational, not just diagnostic
- Help agents learn proper tool usage through clear feedback

**Follow Natural Task Subdivisions:**
- Tool names should reflect how humans think about tasks
- Group related tools with consistent prefixes for discoverability
- Design tools around natural workflows, not just API structure

**Use Evaluation-Driven Development:**
- Create realistic evaluation scenarios early
- Let agent feedback drive tool improvements
- Prototype quickly and iterate based on actual agent performance

#### 1.2 Study API Documentation

To integrate a service, read through **ALL** available API documentation:
- Official API reference documentation
- Authentication and authorization requirements
- Rate limiting and pagination patterns
- Error responses and status codes
- Available endpoints and their parameters
- Data models and schemas

#### 1.3 Create a Comprehensive Implementation Plan

Based on your research, create a detailed plan that includes:

**Tool Selection:**
- List the most valuable endpoints/operations to implement
- Prioritize tools that enable the most common and important use cases
- Consider which tools work together to enable complex workflows

**Shared Utilities and Helpers:**
- Identify common API request patterns
- Plan pagination helpers
- Design filtering and formatting utilities
- Plan error handling strategies

**Input/Output Design:**
- Define input validation models (choose the idiomatic validation library for your language — e.g., Pydantic for Python, Zod for TypeScript)
- Design consistent response formats (e.g., JSON or Markdown), and configurable levels of detail
- Plan for large-scale usage (thousands of users/resources)
- Implement character limits and truncation strategies

**Error Handling Strategy:**
- Plan graceful failure modes
- Design clear, actionable, LLM-friendly, natural language error messages which prompt further action
- Consider rate limiting and timeout scenarios
- Handle authentication and authorization errors

### Phase 2: Implementation

Now that you have a comprehensive plan, begin implementation.

#### 2.1 Set Up Project Structure

Choose your implementation language and set up the project accordingly:

- Use the MCP SDK for your chosen language (Python SDK, TypeScript SDK, etc.)
- Define input validation models using idiomatic tools for your language
- Organize into modules if the server is complex; a single file is fine for simple servers

#### 2.2 Implement Core Infrastructure First

Create shared utilities before implementing tools:
- API request helper functions
- Error handling utilities
- Response formatting functions (JSON and Markdown)
- Pagination helpers
- Authentication/token management

#### 2.3 Implement Tools Systematically

For each tool in the plan:

**Define Input Schema:**
- Use the idiomatic validation library for your language
- Include proper constraints (min/max length, regex patterns, min/max values, ranges)
- Provide clear, descriptive field descriptions with examples

**Write Comprehensive Docstrings/Descriptions:**
- One-line summary of what the tool does
- Detailed explanation of purpose and functionality
- Explicit parameter types with examples
- Complete return type schema
- Usage examples (when to use, when not to use)
- Error handling documentation, which outlines how to proceed given specific errors

**Implement Tool Logic:**
- Use shared utilities to avoid code duplication
- Follow async/await patterns for all I/O
- Implement proper error handling
- Support multiple response formats (JSON and Markdown)
- Respect pagination parameters
- Check character limits and truncate appropriately

**Add Tool Annotations:**
- `readOnlyHint`: true (for read-only operations)
- `destructiveHint`: false (for non-destructive operations)
- `idempotentHint`: true (if repeated calls have same effect)
- `openWorldHint`: true (if interacting with external systems)

### Phase 3: Review and Refine

After initial implementation:

#### 3.1 Code Quality Review

Review the code for:
- **DRY Principle**: No duplicated code between tools
- **Composability**: Shared logic extracted into functions
- **Consistency**: Similar operations return similar formats
- **Error Handling**: All external calls have error handling
- **Type Safety**: Full type coverage
- **Documentation**: Every tool has comprehensive docstrings/descriptions

#### 3.2 Test and Build

**Important:** MCP servers are long-running processes that wait for requests over stdio or HTTP. Running them directly in your main process will cause it to hang indefinitely.

**Safe ways to test the server:**
- Use an evaluation harness (see Phase 4) — recommended approach
- Run the server in a separate terminal session
- Use a timeout when testing: `timeout 5s python server.py`

Verify your implementation compiles or passes syntax checks:
- For compiled languages: run the build step and ensure no errors
- For interpreted languages: verify syntax and import correctness
- Run the evaluation harness to test actual tool behavior

#### 3.3 Quality Checklist

Verify implementation quality:

- [ ] All tools have comprehensive docstrings with examples
- [ ] Input validation uses proper constraints
- [ ] Error messages are actionable and LLM-friendly
- [ ] Response formats are consistent across tools
- [ ] Pagination is handled correctly
- [ ] Character limits and truncation are implemented
- [ ] Tool annotations are set correctly
- [ ] No duplicated code between tools
- [ ] All external calls have error handling
- [ ] Authentication is handled securely

### Phase 4: Create Evaluations

After implementing your MCP server, create comprehensive evaluations to test its effectiveness.

#### 4.1 Understand Evaluation Purpose

Evaluations test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

#### 4.2 Create Evaluation Questions

Follow this process to create effective evaluations:

1. **Tool Inspection**: List available tools and understand their capabilities
2. **Content Exploration**: Use READ-ONLY operations to explore available data
3. **Question Generation**: Create complex, realistic questions
4. **Answer Verification**: Solve each question yourself to verify answers

#### 4.3 Evaluation Requirements

Each question must be:
- **Independent**: Not dependent on other questions
- **Read-only**: Only non-destructive operations required
- **Complex**: Requiring multiple tool calls and deep exploration
- **Realistic**: Based on real use cases humans would care about
- **Verifiable**: Single, clear answer that can be verified
- **Stable**: Answer won't change over time

Generated by autoharness | Template: community/skills/mcp-builder/SKILL.md.tmpl
