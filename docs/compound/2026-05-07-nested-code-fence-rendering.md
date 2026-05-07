---
problem_type: nested_code_fence_rendering
category: markdown_authoring
root_cause: Backslash escaping inside fenced code blocks does not work in standard Markdown. Triple-backtick delimiters inside a triple-backtick fence must use a 4-backtick outer fence instead of escaping with backslashes.
tags: [markdown, code-fence, template-authoring, nested-fences]
shipment: 011-S
date: 2026-05-07
---

# Nested Code Fences in Markdown Documentation

## Problem

A spike document contained a template skeleton inside a ` ```markdown ` fenced
code block. Inside the skeleton, a multi-step plan example used triple-backtick
fences written as `\`\`\`` (backslash-escaped). In rendered Markdown, backslashes
inside a code fence are **not** processed as escape characters — they appear
literally, producing `\`\`\`` instead of ` ``` ` in the rendered output.

## Root Cause

Standard Markdown (and GitHub Flavored Markdown) treats code fence content as
verbatim text. No character escaping applies inside a code fence. A triple-backtick
sequence inside a triple-backtick-delimited fence will prematurely close the outer
fence; backslash-escaping it has no effect on rendering.

## Fix

Use a 4-backtick outer fence when the code block content needs to contain
triple-backtick fences:

````text
````markdown
...outer content with ``` inner fences ``` works fine here...
````
````

Or use tilde-fenced outer blocks:

````text
~~~~markdown
...outer content with ``` inner fences ``` works fine here...
~~~~
````

## When this applies

Any time a template skeleton, code example, or instruction block needs to show
a code fence as part of its content — which is common in autoharness spike
documents that include template skeletons with Markdown structure examples.

## Verification

In GitHub PR review, Copilot reviewer flags this as a rendering issue. Check
rendered Markdown preview — literal backslashes before triple-backticks are the
visible symptom.
