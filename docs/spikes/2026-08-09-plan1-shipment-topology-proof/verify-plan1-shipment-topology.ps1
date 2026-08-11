# READ-ONLY structural verification of the live .backlogit workspace, plus a
# disposable-fixture REPLAY of the exact live Plan-1 topology through the real
# backlogit 1.8.0 ShipShipment engine.
#
# Part 1 performs ONLY SELECT queries and `backlogit get` reads against the real
# workspace. It never mutates it.
# Part 2 rebuilds an isomorphic copy of the live topology in the system temp directory and closes
# all three shipments for real, asserting the F14 elimination end to end.
#
# The repository root is resolved from the script's own location rather than a
# hardcoded checkout, so the published proof is reproducible in any clone and on
# POSIX. Override with -Repo for out-of-tree verification.

[CmdletBinding()]
param(
    [string]$Repo,
    # Base ref for V10's branch-footprint diff. Defaults to origin/HEAD (the
    # repository's default branch), then origin/main, origin/master, main,
    # master - the first that resolves. Deliberately NOT the tracked upstream:
    # for a topic branch that is the remote copy of the SAME branch, which makes
    # merge-base == HEAD and the footprint empty. See the note at V10.
    [string]$BaseRef
)

$ErrorActionPreference = 'Stop'
$script:fail = 0
$script:total = 0

if (-not $Repo) {
    # <repo>/docs/spikes/<this-dir>/verify-plan1-shipment-topology.ps1 -> up 3
    $Repo = (Resolve-Path (Join-Path $PSScriptRoot '..' '..' '..')).Path
}
if (-not (Test-Path (Join-Path $Repo '.backlogit'))) {
    throw "No .backlogit workspace found under '$Repo'. Pass -Repo <path-to-clone>."
}
# CANONICALIZE before any Set-Location. A relative -Repo passes the check above
# (it resolves against the INVOCATION directory) but would then be re-resolved
# against whatever the current directory happens to be later - V9's archive
# probes run from the repo, and the final `Set-Location $repo` runs from the
# temp fixture, so a relative path would silently point somewhere else or fail.
$repo = (Resolve-Path $Repo).Path

function Assert([bool]$Cond, [string]$Msg) {
    $script:total++
    if ($Cond) { Write-Host "  PASS  $Msg" }
    else { Write-Host "  FAIL  $Msg" -ForegroundColor Red; $script:fail++ }
}

function Invoke-Bl {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$BlArgs)
    $out = (& backlogit --log-level error @BlArgs 2>&1) | Out-String
    # $ErrorActionPreference='Stop' does NOT make a NATIVE nonzero exit terminate.
    # Without this, a failed dep add / link / claim / ship / sync / doctor call is
    # captured as ordinary output and the proof continues against a topology that
    # was never created, invalidating every downstream assertion.
    if ($LASTEXITCODE -ne 0) {
        throw "backlogit $($BlArgs -join ' ') FAILED (exit $LASTEXITCODE): $out"
    }
    return $out
}

function Invoke-Sql([string]$Sql) {
    # DISTINGUISH "the query reported zero rows" FROM "the query did not report".
    # The original version returned @() for ANY output lacking a '[' marker, which
    # collapsed those two cases. That is exactly the wrong default here, because
    # several of the STRONGEST proofs in this suite are ZERO-RESULT proofs - V8's
    # "127-S has no dependencies", V9's "no stale 117.x tasks", V4's "117-F has no
    # children". Under the old behaviour a format change, a truncated read or an
    # unexpected banner would have been indistinguishable from an empty result set
    # and every one of those proofs would have passed VACUOUSLY.
    #
    # Verified against backlogit 1.8.0: a zero-row query emits the literal JSON
    # token `null`, NOT `[]`. So `null` is a LEGITIMATE empty result and must be
    # accepted; anything that is neither `null` nor a JSON array means the query
    # did not report its result, which is a HARNESS FAILURE and must throw.
    $o = Invoke-Bl query $Sql
    # Strip structured log lines so the payload check below can be exact rather
    # than a substring search (a substring search is how the original vacuity got
    # in: it accepted any output that happened to contain a bracket anywhere).
    $payload = (($o -split "`r?`n") | Where-Object { $_ -notmatch '^\s*time=' } | Out-String).Trim()
    if ($payload -eq 'null') { return @() }        # genuine zero-row result
    if (-not $payload.StartsWith('[')) {
        throw "backlogit query did not report a JSON result (expected a '[' array or the literal 'null' for zero rows) - refusing to treat unparsed output as an empty result set. Query: $Sql`nPayload: $payload"
    }
    $parsed = $payload | ConvertFrom-Json
    return @($parsed)
}

function Get-Art([string]$Id) {
    $o = Invoke-Bl get $Id --format json
    return ($o.Substring($o.IndexOf('{')) | ConvertFrom-Json)
}

# ===========================================================================
# PART 1 - READ-ONLY VERIFICATION OF THE LIVE WORKSPACE
# ===========================================================================
Set-Location $repo
Write-Host "`n########## PART 1: READ-ONLY VERIFICATION OF THE LIVE WORKSPACE ##########"

$plan = @{
    # 118.006-T (F27 stale-lock/--force-unlock split) and 118.007-T (F26 P-015
    # amendment) were ADDED on 2026-08-11 by accepted operator rulings. They are
    # children of 118-F, so V1's FULL COVERAGE assertion requires them here: a new
    # child that is not in the manifest is exactly the defect that check exists to
    # catch, and omitting them here would have made the verifier agree with a
    # broken topology.
    '127-S' = @{ Feat = '118-F'; Tasks = @('118.001-T', '118.002-T', '118.003-T', '118.004-T', '118.005-T', '118.006-T', '118.007-T') }
    '128-S' = @{ Feat = '119-F'; Tasks = @('119.001-T', '119.002-T', '119.003-T', '119.004-T', '119.005-T', '119.006-T') }
    '129-S' = @{ Feat = '120-F'; Tasks = @('120.001-T', '120.002-T', '120.003-T', '120.004-T', '120.005-T', '120.006-T', '120.007-T', '120.008-T') }
}

# Tasks created NATIVELY under their covering feature (never re-parented off
# 117-F), and therefore expected to carry no origin_feature provenance.
$script:nativeTasks = @('118.006-T', '118.007-T')

Write-Host "`n--- V1: every task has a valid, queued covering feature ---"
# NOTE: `backlogit get --format json` does NOT project size/complexity. Those two
# fields must be read from the `items` table, which is the authoritative store.
# Reading them via the JSON projection produced 38 false FAILs in the first pass.
$sizeEnum = @('XS', 'S', 'M', 'L', 'XL'); $cxEnum = @('trivial', 'low', 'medium', 'high')
$sc = @{}
foreach ($r in (Invoke-Sql "SELECT id, size, complexity, priority FROM items WHERE id LIKE '118.%' OR id LIKE '119.%' OR id LIKE '120.%'")) { $sc[$r.id] = $r }
foreach ($s in $plan.Keys | Sort-Object) {
    $f = $plan[$s].Feat
    $fa = Get-Art $f
    Assert ($fa.artifact_type -eq 'feature') "$f is a feature"
    Assert ($fa.status -eq 'queued') "$f status queued = '$($fa.status)'"
    foreach ($t in $plan[$s].Tasks) {
        $ta = Get-Art $t
        Assert ($ta.parent_id -eq $f) "$t parent_id = '$($ta.parent_id)' (expect $f)"
        Assert ($ta.status -eq 'queued') "$t status queued"
        Assert ($sc.ContainsKey($t) -and $sc[$t].size -in $sizeEnum) "$t size = '$($sc[$t].size)' (valid enum)"
        Assert ($sc.ContainsKey($t) -and $sc[$t].complexity -in $cxEnum) "$t complexity = '$($sc[$t].complexity)' (valid enum)"
        Assert ($sc[$t].size -notin @('L', 'XL')) "$t satisfies the 2-hour rule (size not L/XL)"
        # Provenance is asserted CONDITIONALLY, and the condition is the point.
        # 118.001-T..120.008-T were re-parented off 117-F and MUST retain
        # origin_feature = '117-F'. 118.006-T / 118.007-T were created natively
        # under 118-F on 2026-08-11 and were never under 117-F, so they MUST NOT
        # claim that provenance. Asserting it unconditionally would demand a FALSE
        # provenance record; dropping the assertion entirely would stop detecting
        # provenance loss on the 19 re-parented tasks. Both halves are checked.
        if ($t -in $script:nativeTasks) {
            Assert ($null -eq $ta.custom_fields.origin_feature) "$t was created natively under $f and correctly claims NO origin_feature"
        }
        else {
            Assert ($ta.custom_fields.origin_feature -eq '117-F') "$t retains origin_feature provenance = '$($ta.custom_fields.origin_feature)'"
        }
    }
}

Write-Host "`n--- V2: ROOT PLACEMENT - no covering feature has a parent ---"
foreach ($f in @('117-F', '118-F', '119-F', '120-F')) {
    $fa = Get-Art $f
    Assert ([string]::IsNullOrEmpty($fa.parent_id)) "$f is a ROOT feature (parent_id = '$($fa.parent_id)')"
}

Write-Host "`n--- V3: FULL COVERAGE - each feature's children == its shipment's task members ---"
foreach ($s in $plan.Keys | Sort-Object) {
    $f = $plan[$s].Feat
    $kids = @(Invoke-Sql "SELECT id FROM items WHERE parent_id = '$f' ORDER BY id" | ForEach-Object { $_.id })
    $expect = @($plan[$s].Tasks | Sort-Object)
    Assert (($kids -join ',') -eq ($expect -join ',')) "$f children == $s task members: [$($kids -join ',')]"
    $ship = Get-Art $s
    $members = @($ship.custom_fields.items)
    $missing = @($expect | Where-Object { $_ -notin $members })
    Assert ($missing.Count -eq 0) "$s manifest covers every child of $f (missing: $($missing.Count))"
    Assert ($members[0] -eq $f) "$s lists covering feature $f FIRST (parent-first ordering)"
    Assert ($f -in $members) "$s includes its covering feature as an EXPLICIT member"
    $extraneous = @($members | Where-Object { $_ -ne $f -and $_ -notin $expect -and $_ -ne '117-F' })
    Assert ($extraneous.Count -eq 0) "$s manifest contains no foreign items (extraneous: $($extraneous -join ','))"
}

Write-Host "`n--- V4: umbrella 117-F is CHILDLESS and is a member of the FINAL shipment only ---"
$uKids = @(Invoke-Sql "SELECT id FROM items WHERE parent_id = '117-F'")
Assert ($uKids.Count -eq 0) "117-F has ZERO children (count = $($uKids.Count))"
foreach ($s in @('127-S', '128-S')) {
    $m = @((Get-Art $s).custom_fields.items)
    Assert ('117-F' -notin $m) "$s does NOT list 117-F"
}
Assert ('117-F' -in @((Get-Art '129-S').custom_fields.items)) "129-S (final) DOES list 117-F for engine-native program closure"
# The message claims `related_to`, so the assertion has to TEST that. Projecting
# only target_id would pass on a link of ANY type - including a hierarchical or
# `blocks` edge, which is precisely the thing this proof exists to rule out for
# the umbrella - and Part 2 would then replay a different relationship than the
# live topology. Filter on link_type FIRST, and assert the non-related_to set is
# empty so a stray edge of another type cannot hide behind a passing lookup.
$uAll = @((Get-Art '117-F').links)
$uLinks = @($uAll | Where-Object { $_.link_type -eq 'related_to' } | ForEach-Object { $_.target_id })
foreach ($f in @('118-F', '119-F', '120-F')) { Assert ($f -in $uLinks) "117-F -> $f link present AND its link_type is related_to (non-hierarchical grouping)" }
$uOther = @($uAll | Where-Object { $_.link_type -ne 'related_to' } | ForEach-Object { "$($_.link_type):$($_.target_id)" })
Assert ($uOther.Count -eq 0) "117-F has NO outgoing link of any other type (found: $($uOther -join ','))"

Write-Host "`n--- V5: cross-shipment reachability - no feature is an ancestor of a foreign shipment's member ---"
foreach ($s in $plan.Keys | Sort-Object) {
    $members = @((Get-Art $s).custom_fields.items)
    $roots = @()
    foreach ($m in $members) {
        $cur = $m
        while ($cur) { $a = Get-Art $cur; if ($a.artifact_type -eq 'feature') { $roots += $a.id }; $cur = $a.parent_id }
    }
    $roots = @($roots | Sort-Object -Unique)
    $allowed = if ($s -eq '129-S') { @('117-F', '120-F') } else { @($plan[$s].Feat) }
    $leak = @($roots | Where-Object { $_ -notin $allowed })
    Assert ($leak.Count -eq 0) "$s featureScopeRoots = [$($roots -join ',')] - no leak outside [$($allowed -join ',')]"
}

Write-Host "`n--- V6: dependency DAG is acyclic ---"
$edges = @(Invoke-Sql "SELECT item_id, depends_on FROM item_deps")
$adj = @{}
foreach ($e in $edges) { if (-not $adj.ContainsKey($e.item_id)) { $adj[$e.item_id] = @() }; $adj[$e.item_id] += $e.depends_on }
$state = @{}
$cycle = $null
function Test-Dfs([string]$n) {
    if ($script:cycle) { return }
    $state[$n] = 1
    foreach ($m in ($adj[$n] | Where-Object { $_ })) {
        if ($state[$m] -eq 1) { $script:cycle = "$n -> $m"; return }
        if (-not $state.ContainsKey($m)) { Test-Dfs $m }
    }
    $state[$n] = 2
}
foreach ($n in $adj.Keys) { if (-not $state.ContainsKey($n)) { Test-Dfs $n } }
Assert ($null -eq $script:cycle) "dependency DAG over $($edges.Count) edges is ACYCLIC ($script:cycle)"

Write-Host "`n--- V7: 30 Plan-1 task blocks edges (27 survived re-parenting, then ruling-driven delta) ---"
# The authoritative expected edge set, as real live IDs. Part 2's fixture replay
# is DERIVED from this same list (see $liveEdges below), so the replay cannot
# silently drift from what V7 verified. A count-only check is insufficient:
# swapping one valid edge for another still yields the same total and would let
# the harness replay an obsolete graph while claiming an "exact live topology"
# proof. That is why the expected value below is an explicit SET, and why the
# 2026-08-11 ruling delta is enumerated rather than absorbed into a new count.
#
# RULING DELTA 2026-08-11 (27 -> 30): one edge REMOVED, FOUR ADDED.
#
# CAUTION, AND THE REASON THIS LIST IS A SET AND NOT A COUNT: the first draft of
# this delta listed only THREE additions and expected 29. It was built from a
# `backlogit query` run BEFORE `backlogit sync`, so the index had not yet picked
# up the `dependencies:` frontmatter written when 118.006-T was created. The live
# graph was correct; the EXPECTATION was stale. A count-only check would have been
# equally wrong and would have reported the same failure with no way to see what
# was missing - the set check named the absent edge directly. Rebuild this list
# from a POST-SYNC query.
#   REMOVED '119.004-T->119.003-T'  - F19/ruling 2. The event catalog moved UP
#     into 118.003-T (contracts.py), so events.py no longer depends on the state
#     machine. This edge WAS the cycle F19 reported: 119.003-T had to emit an
#     event type only 119.004-T defined, while 119.004-T depended back on
#     119.003-T. Removing it is the structural fix, not a reordering.
#   ADDED   '119.004-T->118.003-T'  - F19/ruling 2, the replacement edge: the bus
#     now depends on the shared contract that defines what it delivers.
#   ADDED   '120.005-T->118.003-T'  - F21/ruling 2: approvals implement the
#     upstream contract, so the fail-closed channel is no longer omissible from a
#     satisfiable runtime chain.
#   ADDED   '120.006-T->118.006-T'  - F25+F27/rulings 7 and 9: the CLI exposes
#     --force-unlock, whose stale-lock semantics 118.006-T owns.
#   ADDED   '118.006-T->118.005-T'  - F27/ruling 9, declared when 118.006-T was
#     created: the stale-lock lifecycle, --force-unlock and recycled-PID rejection
#     operate on the lock primitive 118.005-T defines, so the split task depends on
#     the task it was split from. Both are 127-S members, so this edge orders work
#     WITHIN the eligible cursor and does not affect shipment eligibility.
$script:expectedEdges = @(
    '118.005-T->118.003-T', '118.006-T->118.005-T',
    '119.001-T->118.003-T', '119.002-T->119.001-T', '119.003-T->118.003-T',
    '119.004-T->118.003-T', '119.004-T->118.004-T', '119.005-T->119.004-T',
    '119.006-T->119.003-T', '119.006-T->119.005-T',
    '120.001-T->118.001-T', '120.001-T->118.003-T', '120.002-T->118.003-T',
    '120.003-T->118.003-T',
    '120.004-T->119.001-T', '120.004-T->119.003-T', '120.004-T->119.005-T',
    '120.004-T->120.001-T', '120.004-T->120.002-T', '120.004-T->120.003-T',
    '120.005-T->118.003-T', '120.005-T->119.004-T', '120.005-T->120.004-T',
    '120.006-T->118.006-T', '120.006-T->120.004-T',
    '120.007-T->118.001-T', '120.007-T->118.002-T', '120.007-T->118.005-T',
    '120.007-T->120.006-T', '120.008-T->120.007-T'
)
$p1 = @(Invoke-Sql "SELECT item_id, depends_on FROM item_deps WHERE (item_id LIKE '118.%' OR item_id LIKE '119.%' OR item_id LIKE '120.%')")
Assert ($p1.Count -eq 30) "Plan-1 task-level blocks edges = $($p1.Count) (expect 30 = 27 pre-redesign - 1 removed + 4 added by the 2026-08-11 rulings)"
$liveSet = @($p1 | ForEach-Object { "$($_.item_id)->$($_.depends_on)" } | Sort-Object)
$expSet = @($script:expectedEdges | Sort-Object)
$missing = @($expSet | Where-Object { $_ -notin $liveSet })
$extra = @($liveSet | Where-Object { $_ -notin $expSet })
Assert ($missing.Count -eq 0 -and $extra.Count -eq 0) "live edge SET matches the expected 30 endpoint pairs exactly (missing: $($missing -join ','); extra: $($extra -join ','))"
$dangling = @($p1 | Where-Object { $_.depends_on -like '117.*' })
Assert ($dangling.Count -eq 0) "no dependency still points at a retired 117.x task ID ($($dangling.Count))"

Write-Host "`n--- V8: serial chain - only the FIRST shipment is eligible ---"
foreach ($pair in @(@('128-S', '127-S'), @('129-S', '128-S'))) {
    $d = @(Invoke-Sql "SELECT depends_on FROM item_deps WHERE item_id = '$($pair[0])' AND depends_on = '$($pair[1])'")
    Assert ($d.Count -eq 1) "$($pair[0]) blocks-on $($pair[1])"
}
$s127deps = @(Invoke-Sql "SELECT depends_on FROM item_deps WHERE item_id = '127-S'")
Assert ($s127deps.Count -eq 0) "127-S has no blocking predecessor - it is the ONLY eligible cursor"
foreach ($s in @('127-S', '128-S', '129-S')) { Assert ((Get-Art $s).status -eq 'queued') "$s is queued (unclaimed)" }

Write-Host "`n--- V9: retired artifacts archived, not deleted; supersession recorded ---"
foreach ($old in @('124-S', '125-S', '126-S')) {
    Assert (Test-Path "$repo\.backlogit\archive\$old.md") "$old preserved in archive (not deleted)"
    Assert (-not (Test-Path "$repo\.backlogit\queue\$old.md")) "$old removed from queue (not claimable)"
}
foreach ($pair in @(@('127-S', '124-S'), @('128-S', '125-S'), @('129-S', '126-S'))) {
    $l = @((Get-Art $pair[0]).links | Where-Object { $_.target_id -eq $pair[1] -and $_.link_type -eq 'supersedes' })
    Assert ($l.Count -eq 1) "$($pair[0]) supersedes $($pair[1])"
}
Assert (@(Invoke-Sql "SELECT id FROM items WHERE id LIKE '117.%'").Count -eq 0) "no stale 117.x task artifacts remain"

Write-Host "`n--- V10: no orphans / duplicates, scoped to Plan-1 artifacts (backlogit doctor) ---"
# The workspace carries PRE-EXISTING debt unrelated to this change: orphaned
# 048.001/002/003-T and archived_from_self_ref on 003-F/003.00x-T. Those artifacts
# are untouched by this session (proven below), so the assertion is scoped to the
# Plan-1 ID space rather than demanding a globally clean workspace.
$doc = Invoke-Bl doctor
$docFindings = @($doc -split '\[' | Where-Object { $_ -match '\]' })
$plan1Re = '\b(117|118|119|120|124|125|126|127|128|129)[-.]'
$plan1Findings = @($docFindings | Where-Object { $_ -match $plan1Re })
foreach ($l in $plan1Findings) { Write-Host "    PLAN-1 FINDING: $($l.Trim())" -ForegroundColor Yellow }
Assert ($plan1Findings.Count -eq 0) "doctor: ZERO findings against any Plan-1 artifact ($($plan1Findings.Count))"
$preExisting = @($docFindings | Where-Object { $_ -notmatch $plan1Re })
Write-Host "    (out-of-scope pre-existing findings on untouched artifacts: $($preExisting.Count))"
# `git status` shows ONLY UNCOMMITTED worktree changes. Once this session's work
# is committed - which is the state every published run is executed in - it
# reports nothing for these paths whether or not the branch changed them, so the
# assertion would pass VACUOUSLY on any clean checkout. The branch's actual
# footprint is `merge-base(origin/main, HEAD)..HEAD`; the worktree is unioned in
# so an uncommitted edit cannot slip past either. Both are NATIVE calls, whose
# nonzero exits are not terminated by $ErrorActionPreference, so each exit code
# is checked explicitly - same contract as Invoke-Bl.
# `origin/main` is NOT guaranteed to exist in the "any clone" this proof
# advertises: a source archive, a fork whose remote is not named `origin`, or a
# clone with pruned remote-tracking refs all lack it, and V10 would abort before
# the topology proof ran. Resolve a base ref in order of decreasing authority and
# let the operator override it; only fail when NONE resolves.
# NOT `@{upstream}`: for a TOPIC BRANCH the tracked upstream is the REMOTE COPY
# OF THE SAME BRANCH, so merge-base(upstream, HEAD) == HEAD and the footprint
# comes back EMPTY - making this assertion vacuous exactly as the raw
# `git status` version was. The base must be the repository's DEFAULT branch.
$baseCandidates = @()
if ($BaseRef) { $baseCandidates += $BaseRef }
else {
    $head = (git --no-pager symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($head)) { $baseCandidates += $head.Trim() }
    $baseCandidates += @('origin/main', 'origin/master', 'main', 'master')
}
$resolvedBase = $null
foreach ($c in $baseCandidates) {
    $null = (git --no-pager rev-parse --verify --quiet "$c^{commit}" 2>$null)
    if ($LASTEXITCODE -eq 0) { $resolvedBase = $c; break }
}
if (-not $resolvedBase) {
    throw "No base ref resolved (tried: $($baseCandidates -join ', ')) - pass -BaseRef <ref> to establish the branch footprint"
}
Write-Host "    (base ref: $resolvedBase)"
$mergeBase = (git --no-pager merge-base $resolvedBase HEAD)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($mergeBase)) {
    throw "git merge-base FAILED (exit $LASTEXITCODE) against '$resolvedBase' - cannot establish the branch footprint"
}
$mergeBase = $mergeBase.Trim()
# DEGENERACY GUARD - the assertion below can only prove something if the diff
# range is non-empty. If merge-base == HEAD the chosen base is an ANCESTOR-OR-SELF
# of HEAD (a self-referential upstream, or a base ref pointing at this very
# commit), the range is empty, and "no debt files touched" would pass while
# proving NOTHING. Fail loudly and make the operator supply a real base instead.
$headSha = (git --no-pager rev-parse HEAD)
if ($LASTEXITCODE -ne 0) { throw "git rev-parse HEAD FAILED (exit $LASTEXITCODE)" }
if ($mergeBase -eq $headSha.Trim()) {
    throw "Base ref '$resolvedBase' resolves to HEAD itself - the branch footprint would be EMPTY and this check VACUOUS. Pass -BaseRef <default-branch>."
}
$branchTouched = @(git --no-pager diff --name-only "$mergeBase..HEAD" -- .backlogit)
if ($LASTEXITCODE -ne 0) { throw "git diff FAILED (exit $LASTEXITCODE) - cannot prove pre-existing debt was untouched" }
$worktreeTouched = @(git --no-pager status --short -- .backlogit)
if ($LASTEXITCODE -ne 0) { throw "git status FAILED (exit $LASTEXITCODE) - cannot prove pre-existing debt was untouched" }
Write-Host "    (branch footprint vs $($mergeBase.Substring(0,8)): $($branchTouched.Count) .backlogit files; uncommitted: $($worktreeTouched.Count))"
$debtRe = '(^|[/\\])(048|003)(\.\d+)?-[FT]\.md$'
$touchedDebt = @(@($branchTouched + $worktreeTouched) | Where-Object { $_ -match $debtRe })
Assert ($touchedDebt.Count -eq 0) "doctor: none of the pre-existing flagged artifacts were modified by this BRANCH (committed + uncommitted)"

Write-Host "`n--- V11: checkpoints - zero errors / quarantine / active ---"
# NOTE: a regex over the raw listing false-positives on both the long `resume_hint`
# prose AND the summary field name `"quarantined": 0`. Assert structured fields.
$cpRaw = Invoke-Bl checkpoint list
$cp = ($cpRaw.Substring($cpRaw.IndexOf('{')) | ConvertFrom-Json)
$allCp = @($cp.checkpoints)
Write-Host "    total checkpoints: $($allCp.Count); engine quarantined count: $($cp.quarantined)"
Assert (@($allCp | Where-Object { $_.status -eq 'active' }).Count -eq 0) "ZERO active checkpoints"
Assert ([int]$cp.quarantined -eq 0) "engine-reported quarantined count is 0 (got '$($cp.quarantined)')"
Assert ([int]$cp.total -eq $allCp.Count) "engine total ($($cp.total)) == enumerated records - no dropped/unparseable record"
Assert (@($allCp | Where-Object { $_.agent -notin @('stage', 'ship') -or [string]::IsNullOrEmpty($_.status) }).Count -eq 0) "every checkpoint has a valid owner agent and status"

# ===========================================================================
# PART 2 - FIXTURE REPLAY OF THE EXACT LIVE TOPOLOGY (real close, disposable)
# ===========================================================================
Write-Host "`n########## PART 2: FIXTURE REPLAY OF THE LIVE TOPOLOGY (real ShipShipment) ##########"
# FULL GUID (not a 32-bit prefix) and no `-Force`: `-Force` silently REUSES an
# existing directory, which on a collision with a stale or concurrent fixture
# would replay this topology into a polluted workspace and prove nothing.
$fx = Join-Path ([System.IO.Path]::GetTempPath()) ("blverify-" + [guid]::NewGuid().ToString('N'))
if (Test-Path $fx) { throw "Fixture path already exists, refusing to reuse it: $fx" }
New-Item -ItemType Directory -Path $fx | Out-Null
Set-Location $fx
Invoke-Bl init | Out-Null
Write-Host "  fixture: $fx"

function New-A([string]$Type, [string]$Title, [string]$Parent) {
    if ($Parent) { $o = Invoke-Bl add --type $Type --title $Title --parent $Parent } else { $o = Invoke-Bl add --type $Type --title $Title }
    if ($o -match 'Created\s+\w+:\s+(\S+)') { return $Matches[1] }
    throw "parse failure: $o"
}
function New-S([string]$Title, [string[]]$Items) {
    $o = Invoke-Bl shipment create --title $Title --items ($Items -join ',')
    return ($o.Substring($o.IndexOf('{')) | ConvertFrom-Json).id
}

# Isomorphic rebuild: umbrella first (=117-F), then F1/F2/F3 (=118/119/120-F).
$U = New-A feature 'umbrella 117-F' $null
$F1 = New-A feature 'covering 118-F' $null
$F2 = New-A feature 'covering 119-F' $null
$F3 = New-A feature 'covering 120-F' $null
$T1 = @(); 1..7 | ForEach-Object { $T1 += New-A task "118.00$_-T" $F1 }   # 7, not 5: 118.006-T / 118.007-T added 2026-08-11
$T2 = @(); 1..6 | ForEach-Object { $T2 += New-A task "119.00$_-T" $F2 }
$T3 = @(); 1..8 | ForEach-Object { $T3 += New-A task "120.00$_-T" $F3 }

# Replay the live task DAG by DERIVING it from the SAME $expectedEdges list that
# V7 just proved equals the live edge set. Hand-maintaining a parallel index-based
# list previously allowed drift: it carried a spurious '120.004-T -> 119.002-T'
# edge that does not exist live (28 replayed vs 27 live), which the old count-only
# V7 could not detect. Deriving guarantees isomorphism by construction.
$idMap = @{}
1..7 | ForEach-Object { $idMap["118.00$_-T"] = $T1[$_ - 1] }
1..6 | ForEach-Object { $idMap["119.00$_-T"] = $T2[$_ - 1] }
1..8 | ForEach-Object { $idMap["120.00$_-T"] = $T3[$_ - 1] }

$liveEdges = @($script:expectedEdges | ForEach-Object {
        $parts = $_ -split '->'
        if (-not $idMap.ContainsKey($parts[0]) -or -not $idMap.ContainsKey($parts[1])) {
            throw "edge '$_' references an ID with no fixture counterpart - replay would not be isomorphic"
        }
        , @($idMap[$parts[0]], $idMap[$parts[1]])
    })
Assert ($liveEdges.Count -eq 30) "fixture replay derives exactly 30 edges from the verified live set ($($liveEdges.Count))"
foreach ($e in $liveEdges) { Invoke-Bl dep add $e[0] $e[1] --type blocks | Out-Null }
foreach ($f in @($F1, $F2, $F3)) { Invoke-Bl link add $U $f related_to | Out-Null }

$S1 = New-S 'S1' (@($F1) + $T1)
$S2 = New-S 'S2' (@($F2) + $T2)
$S3 = New-S 'S3' (@($F3) + $T3 + @($U))
Invoke-Bl dep add $S2 $S1 --type blocks | Out-Null
Invoke-Bl dep add $S3 $S2 --type blocks | Out-Null

function Test-Intact([string[]]$Tasks, [string]$Feat, [string]$Label) {
    $bad = 0
    foreach ($i in $Tasks) { $a = Get-Art $i; if ($a.parent_id -ne $Feat -or $a.status -ne 'queued') { $bad++ } }
    Assert ($bad -eq 0) "$Label all $($Tasks.Count) tasks keep parent_id=$Feat and status=queued ($bad deviations)"
    Assert ((Get-Art $Feat).status -eq 'queued') "$Label covering feature $Feat still queued"
}

foreach ($step in @(@($S1, 'S1'), @($S2, 'S2'), @($S3, 'S3'))) {
    $sid = $step[0]; $lbl = $step[1]
    Write-Host "`n=== CLOSE $sid ($lbl) ==="
    Invoke-Bl shipment claim $sid | Out-Null
    $r = Invoke-Bl shipment ship $sid --sha ('a' * 40)
    $res = $r.Substring($r.IndexOf('{')) | ConvertFrom-Json
    Write-Host "  returned_ids = [$($res.returned_ids -join ',')]"
    Write-Host "  archived_ids = [$($res.archived_ids -join ',')]"
    # Existence alone is not enough, and neither is @(...).Count: @($null).Count
    # is 0, so a null-valued field would satisfy a naive emptiness check and the
    # proof would be vacuous. Require present AND non-null AND zero-length.
    $has = $null -ne ($res.PSObject.Properties.Name | Where-Object { $_ -eq 'returned_ids' })
    Assert ($has -and $null -ne $res.returned_ids -and @($res.returned_ids).Count -eq 0) "$lbl close: returned_ids PRESENT, NON-NULL and EMPTY - no parent_id cleared, no cascade"
    if ($lbl -eq 'S1') {
        Test-Intact $T2 $F2 'after-S1'; Test-Intact $T3 $F3 'after-S1'
        Assert ((Get-Art $U).status -eq 'queued') 'after-S1 umbrella untouched'
        Assert ($F2 -notin $res.archived_ids -and $F3 -notin $res.archived_ids -and $U -notin $res.archived_ids) 'after-S1 no foreign feature archived'
        Assert ($F1 -in $res.archived_ids) 'after-S1 own covering feature archived'
    }
    elseif ($lbl -eq 'S2') {
        Test-Intact $T3 $F3 'after-S2'
        Assert ((Get-Art $U).status -eq 'queued') 'after-S2 umbrella untouched'
        Assert ($F3 -notin $res.archived_ids -and $U -notin $res.archived_ids) 'after-S2 no foreign feature archived'
        Assert ($F2 -in $res.archived_ids) 'after-S2 own covering feature archived'
    }
    else {
        Assert ($F3 -in $res.archived_ids) 'after-S3 own covering feature archived'
        Assert ($U -in $res.archived_ids) 'after-S3 umbrella archived by the FINAL shipment (engine-native closure)'
        Assert ((Get-Art $U).status -eq 'archived') 'after-S3 umbrella terminal'
    }
}

$leftover = @(Invoke-Sql "SELECT id FROM items WHERE status != 'archived'")
Assert ($leftover.Count -eq 0) "terminal state: ZERO non-archived residue ($($leftover.Count) left)"
$d2 = Invoke-Bl doctor
Assert ($d2 -match 'No issues found') "fixture doctor after full chain: clean"

Set-Location $repo
Write-Host "`n=== RESULT: $($script:total - $script:fail)/$($script:total) assertions passed ==="
if ($script:fail -gt 0) { Write-Host 'VERIFICATION FAILED' -ForegroundColor Red; exit 1 }
Write-Host 'VERIFICATION PASSED'
exit 0
