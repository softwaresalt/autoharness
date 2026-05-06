---
title: "git reset --hard preserves branch attachment; git checkout hash detaches HEAD"
problem_type: git-state-corruption
category: template-authoring
root_cause: "Using 'git checkout <hash>' to restore a branch to a winning commit detaches HEAD. Any follow-up commit or push goes to a detached ref, not the experiment branch. Use 'git reset --hard <hash>' to move the branch tip without detaching HEAD."
tags: [git, template-authoring, iterative-experiment, detached-HEAD, branch-safety]
shipment: 007-S
date: 2026-05-05
---

## Problem

In the iterative-experiment skill template, Phase 4 (Summary) originally used:

```
git checkout <winning-commit-hash>
```

This detaches HEAD from the experiment branch. Any `git push` or commit after this point goes to the detached ref, not the branch that was created in Phase 1. The operator is effectively on a ghost branch after the winning commit is selected.

## Fix

```
git reset --hard <winning-commit-hash>
```

`git reset --hard` moves the **branch tip** to the target commit without detaching HEAD. The experiment branch remains attached, and all follow-up operations (push, further commits) target the correct ref.

## Rule

In any skill template that needs to move a branch to a specific commit:
- Use `git reset --hard <hash>` — branch stays attached, working tree updated
- Never use `git checkout <hash>` — detaches HEAD, subsequent push goes to wrong ref

This is especially important in iterative templates where the agent continues to operate after the reset.
