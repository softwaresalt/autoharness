---
title: "WSL-Backed Local Linux Build Feasibility"
date: "2026-07-13"
description: "Feasibility spike framing for using Windows Subsystem for Linux to run local Linux build/test/lint/format gates that mirror GitHub Actions ubuntu-latest and feed the unified CI + local-gating primitive."
topic: "Can autoharness use WSL on Windows dev boxes to produce local Linux-build evidence and reduce redundant GitHub Actions CI usage?"
depth: "spike"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-13-wsl-local-linux-builds-spike.md
source_stash_ids:
  - "2807E5E4"
backlog_items:
  - "081-F"
linked_artifacts:
  - "docs/decisions/2026-07-10-unified-ci-local-gating-primitive-deliberation.md"
  - ".githooks/pre-push"
  - "templates/scripts/pre-push-quality-gates.ps1.tmpl"
  - "templates/scripts/pre-push-quality-gates.sh.tmpl"
tags:
  - "wsl"
  - "local-gating"
  - "github-actions"
  - "pre-push-hook"
  - "primitive-5"
  - "primitive-8"
  - "primitive-10"
  - "operator-approval"
---

# WSL-Backed Local Linux Build Feasibility

## Status

**PROPOSED — operator inspection permission, provisioning approval, and
architecture decision required before implementation.** This spike is intentionally
limited to framing. It did not inspect the machine for WSL state, install WSL,
enable Windows features, install a distro, install Linux packages, edit hooks,
edit CI, or run provisioning commands. Read-only WSL/distro inspection is
non-destructive but still requires operator permission for the selected machine;
actual WSL setup/provisioning is destructive/system-changing and requires explicit
operator approval under Principle VII.

## Problem (stash 2807E5E4)

The unified CI + local-gating primitive accepted on 2026-07-10 intentionally keeps
regular CI Linux-only and relies on local pre-push gates to reduce remote cost.
The stash asks whether a Windows developer box can use WSL to run Linux build,
test, lint, and format gates locally, mirroring GitHub Actions `ubuntu-latest`,
then record enough local Linux-build evidence that remote CI can be reduced or
skipped when evidence is present.

## Relevant existing decision context

`docs/decisions/2026-07-10-unified-ci-local-gating-primitive-deliberation.md`
records:

* the aggregation gate is the single required status check;
* path impact, not PR title, decides whether expensive gates run;
* regular PR/push CI is Linux-only while Windows/macOS remain outside regular CI;
* local pre-push gates are the critical counterweight to minimal remote CI;
* full local build evidence is part of PR readiness for code-changing PRs.

WSL could deepen that primitive by giving Windows operators a local Linux surface,
but it cannot safely justify skipping remote checks until the evidence contract,
publication/trust mechanism, parity expectations, and fallback behavior are
decided.

## Feasibility areas

### 1. Detection

A future implementation would need read-only detection before any provisioning:

* Is `wsl.exe` present?
* Is WSL enabled and on WSL2?
* Which distros exist (`wsl.exe --list --verbose`) and which one is the default?
* Does the chosen distro have required toolchain commands?
* Is the repository path accessible from the distro, and does the distro have
  permissions to read/write needed working-tree files?

Detection can be non-destructive, but this staging item still treats it as an
operator-controlled inspection of a selected machine. Provisioning is a separate
permission class and is not read-only.

### 2. Distro/toolchain provisioning

Installing WSL, enabling Windows optional features, installing a distro, running
`apt`, installing language toolchains, or mutating shell profiles are all
operator-approved actions. They can change system state, require reboot/admin
rights, consume disk, and break local developer assumptions. AFK automation must
not perform them.

A safe product shape would separate:

* **inspect/detect** — read-only, only after the operator authorizes inspection
  of the selected machine;
* **recommend** — list missing prerequisites and exact commands for the operator;
* **provision** — destructive/system-changing, opt-in, explicit, logged, and
  separately operator-approved;
* **verify** — run deterministic gates and record evidence.

### 3. Windows-to-WSL path translation

The runner needs reliable translation between Windows paths and Linux paths:

* Windows repo: `C:\Source\GitHub\autoharness`
* WSL mount form: `/mnt/c/Source/GitHub/autoharness`
* Native WSL repo form, if cloned inside the distro: `/home/<user>/...`

Potential issues include spaces, casing, symlinks, line endings, executable bits,
file watcher behavior, and performance differences between `/mnt/c` and native
ext4 storage. The pre-push hook must know where evidence is produced and must not
write outside the workspace.

### 4. Parity with GitHub Actions `ubuntu-latest`

A WSL distro is not automatically the same as GitHub's hosted runner. Parity has
to be explicit:

* distro release vs `ubuntu-latest` image version;
* installed system packages;
* Python/Node/Go/Rust versions;
* environment variables, locale, shell, and PATH;
* service dependencies and network access;
* cache state and preinstalled tools;
* checkout semantics and permissions.

The feasible target is likely **sufficient local Linux confidence**, not bitwise
hosted-runner identity. Any remote-CI skip must describe that residual risk.

### 5. Wiring into local-gating and PR readiness

A future WSL runner could be invoked by the local pre-push quality-gate hook as an
optional Linux gate. It should emit a local evidence record such as:

```text
.autoharness/gates/linux-build-evidence.json
```

Candidate evidence fields: `commit_sha`, `workspace_path`, `wsl_distro`,
`distro_version`, `kernel`, `toolchain_versions`, `commands`, `start_time`,
`end_time`, `exit_codes`, `logs_digest`, `status`, and `parity_profile`. The PR
Local Review Readiness block could then cite the successful WSL evidence as the
full local Linux build result. However, `.autoharness/gates/` is gitignored and
local-only, so GitHub Actions cannot observe that file directly and cannot trust
it as a remote-CI skip signal without an explicit publication/trust mechanism.

### 6. Remote CI reduction policy

Skipping or reducing GitHub Actions must fail closed. Local evidence under
`.autoharness/gates/` is useful for PR readiness, but it is not by itself a
transport that remote CI can trust because the path is not committed or uploaded
to GitHub. Remote CI remains authoritative until the operator chooses an evidence
publication/trust mechanism, such as a signed commit status/check-run, an
attestation, committed metadata with tamper checks, a workflow artifact produced
by a trusted runner, or an explicit advisory-only policy.

* If evidence is absent, stale, for the wrong commit, from the wrong distro, or
  failed, remote Linux CI still runs.
* If local evidence exists but no trusted publication mechanism exists, remote
  Linux CI still runs and the local evidence is advisory/local-readiness only.
* If local evidence exists but remote CI is required by branch rules, the harness
  reports evidence but does not bypass rules.
* If the evidence contract cannot be verified, treat local Linux verification as
  advisory only.

## Risks

* WSL provisioning is destructive/system-changing and may require admin rights or
  reboot.
* WSL local state can drift away from GitHub's hosted runner image.
* Running from `/mnt/c` can be slower or behaviorally different than native Linux
  filesystems.
* Toolchain installs may use network/system package managers and create supply
  chain exposure.
* Evidence can become stale if tied to a prior commit or prior distro state.
* Reducing remote CI too aggressively can weaken the merge gate and contradict
  the fail-closed CI primitive.
* A gitignored local evidence file cannot be observed by GitHub Actions; treating
  it as a remote skip signal without a signed/verified publication path would be
  a trust-boundary bug.

## Recommendation

Start with an **operator-approved feasibility spike**, not implementation. The
spike should first obtain read-only inspection permission for a selected machine,
then detect WSL/distro state, define the evidence contract, run a small
representative gate inside an operator-selected distro if available, compare it to
the current GitHub Actions `ubuntu-latest` gate, and report parity gaps. Any
installation/feature enablement/distro/package provisioning requires separate
Principle VII approval. Only after that should the operator decide whether to wire
WSL into the pre-push hook and whether any remote-CI reduction is acceptable.

## Operator Decision Required

The operator must decide **three separate questions**: (1) whether to permit
read-only inspection of a selected machine for WSL/distro presence; (2) whether
to explicitly approve any destructive installation, Windows feature enablement,
distro setup, or package/toolchain provisioning under Principle VII; and (3) what
evidence publication/trust mechanism, if any, can let local WSL evidence affect
remote CI. Until a trusted publication mechanism exists, remote CI remains
authoritative and WSL evidence can satisfy local PR readiness only as an advisory
or locally cited signal.

## Open questions

1. Is WSL already installed on the target dev box, and if so which distro/version
   should be considered canonical?
2. Should repositories be tested from `/mnt/c/...` or cloned inside the WSL distro?
3. Which gate commands must run under WSL for a workspace to claim Linux local
   readiness?
4. What exact evidence fields are required for a PR body to cite local Linux build
   success?
5. What evidence publication/trust mechanism would GitHub Actions accept: signed
   status/check-run, attestation, committed metadata, uploaded artifact, or
   advisory-only?
6. Can remote CI ever be skipped, or should WSL only reduce investigation time
   while GitHub Actions remains the authoritative merge signal?
7. Who owns WSL toolchain drift and updates?
