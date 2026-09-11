# SHIP-3 file-lock script security hardening — task 0 de-risking matrix and token/digest vectors

- **Shipment**: 161-S (SHIP-3 — file-lock script security hardening, template-first)
- **Feature**: 153-F
- **Task**: 153.004-T (de-risking prerequisite, H9, blocking for 153.001-T and 153.002-T)
- **Plan**: `docs/plans/2026-08-31-ship3-file-lock-script-security-hardening-plan.md`
- **Scope**: record-only. No production script, template, or instruction files were
  edited to produce this document. All observations below were gathered against the
  **current, unmodified** `templates/skills/file-lock/scripts/{acquire,release}_lock.{ps1,sh}`
  in scratch fixtures outside the repository working tree.
- **Environment**: Windows PowerShell (`Resolve-Path`, `.NET` `FileSystemInfo`/`Path`,
  `System.Security.Cryptography`) and WSL bash 5.3.9 (`realpath`, `dirname`, `git`,
  `sha256sum`) on the same host.

## Part 1 — two-platform path-resolution and lock-path behaviour matrix

Seven escape/edge cases, each recorded as **(a)** the observed behaviour of the
platform's resolution primitives against the **current, unmodified** scripts and
**(b)** the intended post-fix behaviour that tasks 1 and 2 must implement.

### Case 1 — absolute path outside the workspace root

| Platform | Observed (current scripts) | Intended post-fix |
|---|---|---|
| Windows | `Resolve-Path` on an absolute path outside the root returns that path unchanged (string-normalized only); the current scripts perform **no root-containment check at all**, so the path is accepted. | After H2/H4: resolve the candidate path and the workspace root to fully-resolved real paths, then reject via path-segment comparison (not string-prefix) when the candidate is not a descendant of the root. |
| POSIX | `realpath /outside/evil.txt` correctly returns the absolute, fully-resolved outside path. The current scripts likewise perform no containment check, so it is accepted. | Same containment check as Windows, expressed with POSIX-native resolution (`realpath` or equivalent). |

Empirical (POSIX, `realpath`):
```
$ realpath "$root/posix/outside/evil.txt"
/…/flock-matrix-800072660/posix/outside/evil.txt
```

### Case 2 — `../` traversal

| Platform | Observed | Intended post-fix |
|---|---|---|
| Windows | `[System.IO.Path]::GetFullPath` collapses `..` segments via pure string normalization (no filesystem access, no reparse-point awareness) and returns the outside path; current scripts accept it (no containment check). | Same H2/H4 containment check as case 1; `..` collapse is necessary but not sufficient — it must be followed by descendant comparison against the resolved root. |
| POSIX | `realpath` collapses `../../outside/evil.txt` (run from `ws/sub`) to the outside path correctly. | Same containment check. |

Empirical (POSIX):
```
$ cd ws/sub && realpath ../../outside/evil.txt
/…/flock-matrix-800072660/posix/outside/evil.txt
```

### Case 3 — directory symlink/junction pointing outside the root (finding 3)

This is the case H2 names explicitly: containment must be enforced **after** full
symlink/junction resolution of **both** sides, because resolving one side only (or
comparing unresolved strings) leaves the escape open.

| Platform | Observed | Intended post-fix |
|---|---|---|
| Windows | `Resolve-Path` does **not** dereference a directory junction/symlink — it returns the literal path through the link, unresolved. `[System.IO.Path]::GetFullPath` likewise does not dereference reparse points. Only `[System.IO.FileSystemInfo]::ResolveLinkTarget($true)` correctly resolves a reparse-point directory to its real final target (confirmed: `LinkType=Junction`, `Target=<real outside path>`). The current scripts use `Resolve-Path`/string normalization only, so a workspace-root-contained symlink pointing outside is **silently accepted** — confirmed defect. | Must resolve the **full real path** by walking every ancestor path segment for reparse points (a single call only resolves one level; a chain of nested reparse points requires iterative resolution) before comparing the resolved candidate to the resolved root. |
| POSIX | `realpath` **does** fully and correctly dereference a symlinked directory in one call, returning the real outside target. However, the current scripts use `cd $(dirname "$path") && pwd -P` as their existing mechanism — empirically this **also** resolves through the symlink correctly, because `cd` traverses the symlink and `pwd -P` reports the physical (non-symlink) working directory. | POSIX already has a working primitive (`realpath`, or the existing `cd`+`pwd -P` idiom) for this case; the POSIX-side fix is primarily to **add the containment comparison that is currently entirely absent**, not to fix path resolution itself. |

Empirical:
```
# Windows
PS> (Resolve-Path "$root\ws\linkout\evil.txt").Path
C:\…\ws\linkout\evil.txt          # NOT dereferenced — literal path through the junction
PS> [System.IO.FileSystemInfo] resolve-link-target on the junction itself
LinkType: Junction  Target: C:\…\outside      # correctly resolves, but only via this specific API

# POSIX
$ cd ws && realpath linkout/evil.txt
/…/posix/outside/evil.txt                      # correctly dereferenced
$ cd "$(dirname "$root/posix/ws/linkout/evil.txt")" && pwd -P
/…/posix/outside                                # current script's own idiom also dereferences correctly on POSIX
```

**Asymmetry recorded for tasks 1/2**: on Windows, the *currently used* resolution
primitive (`Resolve-Path`) is the one that fails to dereference; a different,
correct primitive exists but is not a single drop-in replacement (it resolves a
reparse point, not an arbitrary path string) and must be applied per ancestor
segment. On POSIX, `realpath` and the scripts' own existing `cd`+`pwd -P` idiom
already dereference correctly — the POSIX gap is the **absence of any containment
comparison**, not the resolution primitive itself.

### Case 4 — sibling directory sharing the root's name as a prefix (`/repo` vs `/repo-evil`)

H4 names this explicitly: prefix-string containment (`StartsWith`/`case ... in
"$WS"*`) is forbidden because it wrongly matches a sibling whose name merely
shares a prefix.

| Platform | Observed | Intended post-fix |
|---|---|---|
| Windows | `"$evilPath".StartsWith($rootPath)` returns `True` for `ws-evil` against root `ws` — confirmed empirically as a live bug class, not a hypothetical. The current scripts do not perform containment checks at all, so this is a **latent** defect that only becomes reachable once H2 is (mis-)implemented as a naive prefix check. | Path-segment comparison only (e.g., `Path.GetRelativePath(root, candidate)` and reject a result that starts with `..` or is rooted, i.e. `Path.IsPathRooted`) — never string-prefix. |
| POSIX | `case "$EVIL" in "$WS"*) ... esac` matches `ws-evil` against `ws` — confirmed `TRUE (BUG)` empirically. | Segment-aware comparison, e.g. compare the canonicalized candidate against `"$WS/"*` (root **plus a trailing separator**) or use `realpath --relative-to` and reject a result starting with `..`. |

Empirical (POSIX):
```
$ WS=.../posix/ws ; EVIL=.../posix/ws-evil
$ case $EVIL in "$WS"*) echo 'naive prefix match: TRUE (BUG)' ;; *) echo false ;; esac
naive prefix match: TRUE (BUG)
```

### Case 5 — root-level target that exists

| Platform | Observed | Intended post-fix |
|---|---|---|
| Windows | `Split-Path -Parent` on a **resolved absolute** root-level path returns the root directory correctly (no defect at this cell when the path is already absolute/resolved). | No change needed once containment operates on resolved absolute paths throughout. |
| POSIX | `dirname AGENTS.md` (relative, invoked with cwd = root) returns `.` — i.e., "current directory", not an empty string or an error. | No change needed provided the script always resolves to an absolute path before computing the lock-file directory, rather than relying on `dirname`'s relative, cwd-dependent answer. |

### Case 6 — root-level target that is MISSING (finding 6)

This is the cell H4/finding-6 care about most: the failure mode differs by
platform, and the two scripts must still compute the **same** lock path for the
same logical target regardless of platform or CWD.

| Platform | Observed | Intended post-fix |
|---|---|---|
| Windows | `Split-Path -Parent` on a **relative, root-level, non-existent** file path returns an **empty string** (`""`). Empirically confirmed: `Join-Path ""` **throws** under `Set-StrictMode -Version Latest` (`Cannot bind argument to parameter 'Path' because it is an empty string`). This is a real crash, not a theoretical one, whenever a root-level target that does not yet exist is passed as a relative path. | Resolve the target path to an **absolute** path (relative to the resolved workspace root, not relying on `Split-Path -Parent` of the raw relative string) before ever computing a parent directory, so the parent is always well-defined. |
| POSIX | `dirname MISSING.md` (relative, missing target, cwd = root) returns `.` — same as the case-5 "present" cell. `dirname` does not distinguish existing vs missing targets; it is a pure string operation. Because the answer is `.` (current directory) rather than empty or an error, the POSIX side does **not crash**, but it silently depends on the caller's CWD being the intended root — an implicit assumption, not a verified one. | Same fix as Windows: resolve to an absolute path derived from an explicit, verified workspace root before computing the lock-file location, rather than trusting `dirname`'s cwd-relative answer. This removes the CWD-dependence on both platforms and gives acquire/release scripts (potentially invoked from different CWDs) an identical, root-anchored lock path for the same logical target. |

Empirical:
```
# Windows
PS> Split-Path -Parent "AGENTS.md"     # relative, root-level
                                        # (empty string)
PS> Set-StrictMode -Version Latest; Join-Path "" ".lock"
Join-Path: Cannot bind argument to parameter 'Path' because it is an empty string.

# POSIX
$ cd ws && dirname AGENTS.md
.
$ cd ws && dirname MISSING.md
.
```

**Note on symptom asymmetry**: the same root cause (root-level relative target,
parent directory computed from the raw path string rather than a resolved
absolute path) manifests as a **hard crash** on Windows (`Join-Path` throwing
under strict mode) and as a **silent, CWD-dependent but non-crashing** answer on
POSIX (`dirname` returning `.`). Both are defects under H5 (identical semantics
required); the fact that POSIX does not crash must not be read as "POSIX has no
bug here" — it has a *different*, harder-to-notice one (lock-path divergence if
acquire and release are ever invoked from different working directories).

### Case 7 — nested git checkout: `git rev-parse --show-toplevel` widens to the parent repository (finding 2)

| Platform | Observed | Intended post-fix |
|---|---|---|
| POSIX (git behaviour is platform-independent; verified on POSIX, applies identically on Windows git) | Constructed fixture: an outer git repository at `git-outer/` (`git init`), and an inner directory `git-outer/nested-ws/scripts/` with **no `.git` of its own**. Running `git rev-parse --show-toplevel` from inside `nested-ws/scripts` returns `git-outer` (the **outer, wider** root) — **not** `git-outer/nested-ws`, which is the intended workspace root in this scenario. Confirmed empirically. | Per the plan's decision (i): when no explicit `--workspace-root` parameter is supplied and a git-derived root is used as the implicit default, the script must not blindly trust an arbitrary ancestor `.git`. **Concrete operationalization recorded here for task 1's implementation** (the plan's own wording, "not an ancestor-or-equal of the script's own installed location", is underspecified against this exact fixture — see note below): require that the git-derived top-level, when `git rev-parse --show-toplevel` is invoked **from the script's own directory** (e.g. `$PSScriptRoot` / `dirname "$0"`, not the target file's directory), have the script's own directory as a **direct child named `scripts/`** of that top-level. In this fixture, `git-outer + "/scripts"` (`git-outer/scripts`) does **not** equal the script's actual directory (`git-outer/nested-ws/scripts`), so the check correctly fails closed and the script must demand an explicit `--workspace-root` rather than silently widening to `git-outer`. |

Empirical:
```
$ cd git-outer/nested-ws/scripts && git rev-parse --show-toplevel
/…/flock-matrix-800072660/git-outer          # widened to the OUTER repo — confirms finding 2
# intended inner workspace root was:
/…/flock-matrix-800072660/git-outer/nested-ws
```

**Implementation note for task 1**: the plan's decision (i) amendment ("git-derived
root is not an ancestor-or-equal of the script's own installed location") is
satisfied too loosely by an ancestor-only reading against this fixture — `git-outer`
**is** an ancestor of `git-outer/nested-ws/scripts`, so a bare ancestor-or-equal
check would **not** catch this exact widening case. The concrete, checkable
predicate recorded above (git-derived top-level's `scripts/` child must equal the
script's own resolved directory) preserves the plan's stated intent — fail closed
and demand the explicit parameter rather than silently trusting a widened
git-derived root — while being unambiguous to implement and test. This is a task
0/task 1 implementation-level clarification of an already-approved plan decision,
not a change to the plan's policy (H9/decision (i) are unchanged); it is recorded
here, per H9, so tasks 1 and 2 do not have to re-derive it independently.

---

## Part 2 — canonical token/digest interoperability vectors (V-a – V-e)

All values below were generated with standard, non-bespoke platform primitives —
PowerShell's `System.Security.Cryptography.RandomNumberGenerator` /
`[System.Security.Cryptography.SHA256]` and cross-checked against WSL bash's
`sha256sum` — and are **frozen, literal constants**. Per the plan, task 2 MUST
cite these vectors by name as the expected value source and MUST NOT compute an
expected digest from its own implementation.

### V-a — token encoding canonicalization (binding choice recorded here)

- **Entropy / length**: **32 bytes (256 bits)** of CSPRNG output — comfortably
  above the TC1 128-bit floor, chosen for headroom.
- **Encoding**: lowercase hexadecimal, **fixed length = 64 characters** (2 hex
  chars per byte, 32 bytes). This is the single valid length under TC2 — there is
  no separate "minimum" or "maximum" valid length.
- **Byte representation for digest input**: the token's **UTF-8 bytes**, encoded
  **without a BOM**, with **no trailing newline or carriage return**.
- **Case sensitivity**: the token alphabet is `[0-9a-f]` only; uppercase hex is
  **not** a valid token (see the V-c "malformed/uppercase" rejection case below).

**Critical empirical finding for V-a/V-b (BOM injection)**: writing the token to a
file with .NET's `[System.Text.Encoding]::UTF8` (e.g. via `WriteAllText` or the
PowerShell default file-encoding path) **silently injects a 3-byte UTF-8 BOM**
(`EF BB BF`) at the start of the file. Empirically confirmed: a 64-character
token written this way produced a **67-byte** file, and `Get-FileHash` over that
file produced a **different, wrong** digest (`69c90b40...`) than the correct,
BOM-free digest (`96aa0ac1...`) computed either from the raw in-memory UTF-8 bytes
(`[System.Text.Encoding]::UTF8.GetBytes()`, which does **not** add a BOM) or from
bash's `printf '%s' "$token" | sha256sum` over the same literal characters. This
is exactly the failure class V-a's "UTF-8 without BOM" and TC4's cross-platform
semantics guard against — **task 2 must never write the token to a file or use a
BOM-emitting encoding path** to compute or compare the digest; it must operate on
the raw string bytes directly (`GetBytes` in PowerShell; ordinary shell string
expansion / `printf '%s'` in POSIX, never `echo` without `-n`, which appends a
trailing newline that would also change the digest).

### V-b — digest canonicalization (binding choice recorded here)

- **Digest input**: the token's canonical UTF-8 bytes as in V-a — **no separator,
  no salt** — hashed directly.
- **Algorithm**: SHA-256 (satisfies TC3's "SHA-256 or stronger"; MD5/SHA-1
  forbidden).
- **Output representation**: **lowercase hexadecimal**, 64 characters, **no
  trailing whitespace, no filename suffix**.

**Empirical cross-tool divergence confirmed** (exactly the concern named in the
plan): `Get-FileHash -Algorithm SHA256` returns its `Hash` property in
**UPPERCASE** by default (`69C90B40...`), while POSIX `sha256sum` returns
**lowercase** and appends a `  <filename>` (or `  -` for stdin) suffix that must
be stripped. Task 2's implementation must explicitly `.ToLower()` any
`Get-FileHash` output (or avoid `Get-FileHash` entirely in favour of
`[System.Security.Cryptography.SHA256]::HashData`/`ComputeHash` composed
manually into lowercase hex, which is what was used to produce the vectors
below) and must strip `sha256sum`'s trailing `  -`/filename suffix before
comparing digests.

### V-c — frozen `(token → owner_digest)` constants

All five tokens below are canonical-length (64 lowercase-hex characters, V-a) and
their digests were computed twice — once via PowerShell (`SHA256.ComputeHash` over
`Encoding.UTF8.GetBytes(token)`) and once via WSL bash (`printf '%s' "$token" |
sha256sum`) — and **found identical** on both platforms, confirming V-d/V-c3
agreement on the expected values themselves.

| Label | Token (64 lowercase-hex chars) | `owner_digest` (SHA-256, lowercase hex) | Adversarial property |
|---|---|---|---|
| V-c-1 | `e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30a` | `96aa0ac1a81d5616a6a468f888d4f727958e15d33a6d9d00bf080d4c7ea2ae4e` | canonical valid-length token; all-lowercase-hex |
| V-c-2 | `cec53b030c1d80eab1582ab06daf42204906075565aad99a6c0d23c52b1059c2` | `be46528d300d259b3bfa5a32ace47f22972d500ae1412ce59a02fa7b480da4ad` | canonical valid-length token; all-lowercase-hex |
| V-c-3 | `ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff` | `df0790f236013511e91fa4532fb7761f62320a51a3868dabf4a13fe5f53e3263` | maximum-value character (`f`) repeated across the entire declared alphabet |
| V-c-4a | `e0f0240b96cf3810ac4679762271e2916785e5ce24b755f2ae59d4c454914d21` | `75004610c37b3f618cb133894712ee9c3fd68e9bb9036a33fc08ca4a6f9139e1` | first of a pair differing **only in the last character** (catches a truncating implementation) |
| V-c-4b | `e0f0240b96cf3810ac4679762271e2916785e5ce24b755f2ae59d4c454914d22` | `9c5fef6103f589f40e681b2ef292335e5145bc3b51f65464029d2b724573f6a7` | second of the pair — differs from V-c-4a only in the final hex digit (`1` vs `2`); digests **must** differ |

**Malformed/rejected vector (charset violation, not a length boundary)**: the
uppercase rendering of a valid-length token —
`E63716AC5086353E685AE35981418689874BA3DB75FE9D6C92B3CB9F8BADC991`... (64
uppercase hex characters) — is **invalid** under V-a's lowercase-only alphabet and
must be rejected outright, not lowercased-and-accepted, since silently
normalizing case would let a caller supply a token in a form neither variant
canonically produces.

### V-c2 — length-boundary rejection vectors (invalid by construction, no digest)

Both derived from V-c-1 by adding/removing exactly one trailing character. Per the
plan, these are rejected **before** a digest is computed — there is no
`(token → owner_digest)` pair for either.

| Label | Token | Length | Expected verdict |
|---|---|---|---|
| V-c2-short | `e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30` | 63 (one short) | **REJECT** — fail closed: non-zero exit, named error, no lock acquired, no digest computed |
| V-c2-long | `e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30aa` | 65 (one long) | **REJECT** — fail closed: non-zero exit, named error, no lock acquired, no digest computed |

These specifically catch (a) an implementation that pads/truncates a wrong-length
token into the valid length before validating, and (b) an implementation that
validates only a prefix of the supplied string and silently ignores trailing
characters. Both must be rejected as legibly invalid input, not coerced.

### V-c3 — cross-platform expectation for the length boundary (two-cell, per vector)

For **each** of V-c-1..V-c-4b (accept) and V-c2-short/V-c2-long (reject), both the
PowerShell and POSIX implementations of task 2 must produce the **identical**
verdict and observable:

| Vector | PowerShell verdict | POSIX verdict | Digest (if accepted) |
|---|---|---|---|
| V-c-1..V-c-4b | ACCEPT | ACCEPT | as recorded in V-c (identical both platforms) |
| V-c2-short | REJECT (non-zero exit, no lock, no digest) | REJECT (non-zero exit, no lock, no digest) | n/a |
| V-c2-long | REJECT (non-zero exit, no lock, no digest) | REJECT (non-zero exit, no lock, no digest) | n/a |

This table exists specifically because a length check implemented as PowerShell
`.Length` (UTF-16 code-unit count) versus a POSIX byte- or character-count check
could silently disagree at the boundary; recording the expectation here per-vector
turns that into a checkable assertion for task 2.

### V-d — two-cell round-trip direction matrix

| Direction | Expectation |
|---|---|
| acquire-PowerShell → verify-POSIX | A token generated by the PowerShell acquire script, when hashed by the POSIX release script's digest routine, must produce the **same** `owner_digest` recorded in V-c for that token value. |
| acquire-POSIX → verify-PowerShell | A token generated by the POSIX acquire script, when hashed by the PowerShell release script's digest routine, must produce the **same** `owner_digest` recorded in V-c for that token value. |

Task 0 confirms the **precondition** for this matrix — that both platforms'
standard SHA-256 utilities agree on the digest of each V-c token when the byte
representation is canonicalized per V-a/V-b (no BOM, no trailing newline,
lowercase output) — by cross-computing every V-c/V-c2 digest with both
`SHA256.ComputeHash` (PowerShell) and `sha256sum` (POSIX) and finding them
identical. Task 2's own acquire/verify code paths must be exercised against both
directions using these same frozen tokens as the actual round-trip test, not
merely re-confirming the utilities agree.

### V-e — no-SHA-256-utility fail-closed expected observable

| Platform | Expected observable when no SHA-256 utility is available |
|---|---|
| POSIX | Neither `sha256sum` nor `shasum -a 256` resolvable on `PATH`: script exits **non-zero**, prints a named error identifying the missing utility and the required remedy (install coreutils/perl-Digest-SHA), **does not** acquire or leave a lock, and does **not** fall back to a weaker digest or store the token in plaintext. |
| Windows | `[System.Security.Cryptography.SHA256]` is part of the .NET base class library shipped with PowerShell 5.1+/7+ and is not expected to be absent in any supported environment; if construction of the hash provider ever throws, the script must exit **non-zero** with a named error and must not acquire a lock — same fail-closed shape as POSIX, recorded for symmetry even though the triggering condition is not expected to occur in practice. |

---

## Summary for tasks 1 and 2

- **Task 1** (containment): implement H2/H4 using resolved-real-path,
  path-segment comparison on both platforms per cases 1–5; implement the
  iterative reparse-point-ancestor-walk for Windows per case 3; implement the
  concrete git-widening guard (git-derived-root's `scripts/` child must equal the
  script's own resolved directory) per case 7.
- **Task 2** (ownership): implement TC1–TC6 using the exact byte/encoding rules in
  V-a/V-b (32-byte/256-bit CSPRNG token, 64-lowercase-hex, no BOM, no trailing
  newline; SHA-256 digest, lowercase hex, no filename suffix), test against the
  frozen V-c/V-c2 vectors and the V-c3/V-d cross-platform expectations, and
  implement the V-e fail-closed path. Fix case 6's root-anchored lock-path
  computation (resolve to absolute path before computing parent) so acquire and
  release compute the same lock path regardless of CWD.

No production script, template, instruction, or manifest file was modified to
produce this document.
