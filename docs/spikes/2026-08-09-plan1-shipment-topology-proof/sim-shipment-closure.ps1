# DISPOSABLE FIXTURE SIMULATION — backlogit 1.8.0 shipment-close proof.
#
# Read-only w.r.t. the real workspace: creates throwaway backlogit workspaces
# under the system temp directory and exercises the REAL ClaimShipment/ShipShipment engine.
# Never touches C:\Source\GitHub\autoharness\.backlogit.
#
# Proves the Plan-1 structural redesign (F14 elimination):
#   * each serial shipment has its OWN ROOT covering feature,
#   * that feature is FULLY COVERED (every descendant is in the same manifest),
#   * the feature is an EXPLICIT manifest member,
#   * the product umbrella feature is CHILDLESS and listed only in the FINAL shipment.
# Expected: zero parent_id clearing, zero cross-shipment cascade, zero repair.
#
# ARM A is a CONTROL reproducing the CURRENT (pre-redesign) topology to
# demonstrate the F14 defect is real and that the redesign is what removes it.

$ErrorActionPreference = 'Stop'
$script:fail = 0
$script:total = 0

function Assert([bool]$Cond, [string]$Msg) {
    $script:total++
    if ($Cond) { Write-Host "  PASS  $Msg" }
    else { Write-Host "  FAIL  $Msg" -ForegroundColor Red; $script:fail++ }
}

function Invoke-Bl {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$BlArgs)
    $out = & backlogit --log-level error @BlArgs 2>&1
    # $ErrorActionPreference='Stop' does NOT make a NATIVE nonzero exit terminate.
    # Without this check a failed `dep add`/`link`/`claim`/`ship` would be captured
    # as ordinary output and the proof would continue against a topology that was
    # never actually created, silently invalidating every downstream assertion.
    if ($LASTEXITCODE -ne 0) {
        throw "backlogit $($BlArgs -join ' ') FAILED (exit $LASTEXITCODE): $($out | Out-String)"
    }
    return ($out | Out-String)
}

# Parses a `shipment ship` result and asserts that returned_ids EXISTS and is
# EMPTY. A negative regex is not sufficient: it also "passes" when the field is
# absent, null, or emitted in an unexpected shape, which would prove nothing.
function Assert-NoReturnedIds([string]$ShipOutput, [string]$Label) {
    $i = $ShipOutput.IndexOf('{')
    if ($i -lt 0) { Assert $false "$Label close emitted parseable JSON"; return }
    $res = $ShipOutput.Substring($i) | ConvertFrom-Json
    $has = $null -ne ($res.PSObject.Properties.Name | Where-Object { $_ -eq 'returned_ids' })
    Assert $has "$Label close result HAS a returned_ids field (field present, not merely absent)"
    if (-not $has) { return }
    # @($null).Count is 0, so counting alone would let a NULL value pass and make
    # the proof vacuous. Assert non-null explicitly before checking the length.
    Assert ($null -ne $res.returned_ids) "$Label close returned_ids is NON-NULL (null would satisfy a naive emptiness check)"
    $n = @($res.returned_ids).Count
    Assert ($null -ne $res.returned_ids -and $n -eq 0) "$Label close returned ZERO items to backlog (present, non-null, empty; count=$n)"
}

function New-Artifact([string]$Type, [string]$Title, [string]$Parent) {
    if ($Parent) { $o = Invoke-Bl add --type $Type --title $Title --parent $Parent }
    else { $o = Invoke-Bl add --type $Type --title $Title }
    if ($o -match 'Created\s+\w+:\s+(\S+)') { return $Matches[1] }
    throw "could not parse created id from: $o"
}

function New-Shipment([string]$Title, [string[]]$Items) {
    $o = Invoke-Bl shipment create --title $Title --items ($Items -join ',')
    $j = $o.Substring($o.IndexOf('{')) | ConvertFrom-Json
    return $j.id
}

function Get-Art([string]$Id) {
    $o = Invoke-Bl get $Id --format json
    return ($o.Substring($o.IndexOf('{')) | ConvertFrom-Json)
}

function New-Fixture([string]$Tag) {
    $r = Join-Path ([System.IO.Path]::GetTempPath()) ("blsim-$Tag-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
    Remove-Item -Recurse -Force $r -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $r | Out-Null
    Set-Location $r
    Invoke-Bl init | Out-Null
    Write-Host "  fixture: $r"
}

$origin = Get-Location

# ===========================================================================
# ARM A - CONTROL: current topology (one covering feature, task-only manifests)
# ===========================================================================
Write-Host "`n########## ARM A (CONTROL): current topology - 1 covering feature, task-only manifests ##########"
New-Fixture 'control'

$cF = New-Artifact feature 'Covering feature (all 19 children)' $null
$cA = @(); 1..5 | ForEach-Object { $cA += New-Artifact task "S1 task $_" $cF }
$cB = @(); 1..6 | ForEach-Object { $cB += New-Artifact task "S2 task $_" $cF }
$cC = @(); 1..8 | ForEach-Object { $cC += New-Artifact task "S3 task $_" $cF }

$cS1 = New-Shipment 'CONTROL S1' $cA
$cS2 = New-Shipment 'CONTROL S2' $cB
$cS3 = New-Shipment 'CONTROL S3' $cC
Write-Host "  control shipments: $cS1 $cS2 $cS3"

Invoke-Bl shipment claim $cS1 | Out-Null
$shipOut = Invoke-Bl shipment ship $cS1 --sha '1111111111111111111111111111111111111111'
Write-Host $shipOut.Trim()

$orphaned = @()
foreach ($i in ($cB + $cC)) { $a = Get-Art $i; if (-not $a.parent_id) { $orphaned += $i } }
Write-Host "  CONTROL: $($orphaned.Count) of 14 downstream tasks had parent_id CLEARED by closing S1"
Assert ($orphaned.Count -eq 14) "CONTROL arm reproduces F14: all 14 S2/S3 tasks orphaned from '$cF' (defect is REAL)"

Set-Location $origin

# ===========================================================================
# ARM B - REDESIGN: per-shipment ROOT covering feature, fully covered, member
# ===========================================================================
Write-Host "`n########## ARM B (REDESIGN): per-shipment ROOT covering feature, fully covered + explicit member ##########"
New-Fixture 'redesign'

# Childless product umbrella (mirrors 117-F post-redesign).
$U = New-Artifact feature 'UMBRELLA Plan-1 product grouping (childless)' $null
# Three ROOT per-shipment covering features (mirror 118-F / 119-F / 120-F,
# the covering features of 127-S / 128-S / 129-S respectively).
$F1 = New-Artifact feature 'S1 safety contracts + characterization baseline' $null
$F2 = New-Artifact feature 'S2 supervision core library (unwired)' $null
$F3 = New-Artifact feature 'S3 application services + adapters + migration' $null

$T1 = @(); 1..5 | ForEach-Object { $T1 += New-Artifact task "S1 task $_" $F1 }
$T2 = @(); 1..6 | ForEach-Object { $T2 += New-Artifact task "S2 task $_" $F2 }
$T3 = @(); 1..8 | ForEach-Object { $T3 += New-Artifact task "S3 task $_" $F3 }

# Cross-feature task blocks edges (H1 characterize-before-migrate spans shipments).
Invoke-Bl dep add $T3[0] $T1[0] --type blocks | Out-Null
Invoke-Bl dep add $T2[0] $T1[1] --type blocks | Out-Null
# Product grouping preserved by NON-hierarchical semantic links
# (item_links are NOT traversed by featureScopeRoots, which walks parent_id only).
foreach ($f in @($F1, $F2, $F3)) { Invoke-Bl link add $U $f related_to | Out-Null }

# Manifests: covering feature FIRST, then its own tasks. FULLY COVERED.
$S1 = New-Shipment 'REDESIGN S1' (@($F1) + $T1)
$S2 = New-Shipment 'REDESIGN S2' (@($F2) + $T2)
$S3 = New-Shipment 'REDESIGN S3' (@($F3) + $T3 + @($U))   # umbrella closes with the final shipment
Write-Host "  redesign shipments: $S1 $S2 $S3"

Invoke-Bl dep add $S2 $S1 --type blocks | Out-Null
Invoke-Bl dep add $S3 $S2 --type blocks | Out-Null

function Test-Untouched([string[]]$Tasks, [string]$Feat, [string]$Label) {
    foreach ($i in $Tasks) {
        $a = Get-Art $i
        Assert ($a.parent_id -eq $Feat) "$Label $i parent_id preserved = '$($a.parent_id)'"
        Assert ($a.status -eq 'queued') "$Label $i status still queued = '$($a.status)'"
    }
    $f = Get-Art $Feat
    Assert ($f.status -eq 'queued') "$Label covering feature $Feat still queued = '$($f.status)'"
}

# ---- CLOSE S1 ----
Write-Host "`n=== CLOSE $S1 (S1) ==="
Invoke-Bl shipment claim $S1 | Out-Null
$r1 = Invoke-Bl shipment ship $S1 --sha '2222222222222222222222222222222222222222'
Write-Host $r1.Trim()
Assert-NoReturnedIds $r1 'S1'
Test-Untouched $T2 $F2 'after-S1'
Test-Untouched $T3 $F3 'after-S1'
$ua = Get-Art $U; Assert ($ua.status -eq 'queued') "after-S1 umbrella $U untouched = '$($ua.status)'"
$f1 = Get-Art $F1; Assert ($f1.status -eq 'archived') "after-S1 own feature $F1 archived cleanly = '$($f1.status)'"

# ---- CLOSE S2 ----
Write-Host "`n=== CLOSE $S2 (S2) ==="
Invoke-Bl shipment claim $S2 | Out-Null
$r2 = Invoke-Bl shipment ship $S2 --sha '3333333333333333333333333333333333333333'
Write-Host $r2.Trim()
Assert-NoReturnedIds $r2 'S2'
Test-Untouched $T3 $F3 'after-S2'
$ua = Get-Art $U; Assert ($ua.status -eq 'queued') "after-S2 umbrella $U untouched = '$($ua.status)'"
$f2 = Get-Art $F2; Assert ($f2.status -eq 'archived') "after-S2 own feature $F2 archived cleanly = '$($f2.status)'"

# ---- CLOSE S3 ----
Write-Host "`n=== CLOSE $S3 (S3) ==="
Invoke-Bl shipment claim $S3 | Out-Null
$r3 = Invoke-Bl shipment ship $S3 --sha '4444444444444444444444444444444444444444'
Write-Host $r3.Trim()
Assert-NoReturnedIds $r3 'S3'
$f3 = Get-Art $F3; Assert ($f3.status -eq 'archived') "after-S3 own feature $F3 archived cleanly = '$($f3.status)'"
$ua = Get-Art $U; Assert ($ua.status -eq 'archived') "after-S3 umbrella $U archived by the FINAL shipment = '$($ua.status)'"

Write-Host "`n=== DOCTOR (redesign fixture, terminal state) ==="
$d = Invoke-Bl doctor
Write-Host $d.Trim()
# ASSERT, do not merely PRINT. `backlogit doctor` exits 0 while REPORTING
# findings (V10 of the verifier relies on exactly that behaviour), so echoing
# its output would let this 64/64 proof pass against a DIRTY terminal fixture.
Assert ($d -match 'No issues found') 'terminal fixture doctor: clean (asserted, not merely printed)'

Set-Location $origin
Write-Host "`n=== RESULT: $($script:total - $script:fail)/$($script:total) assertions passed ==="
if ($script:fail -gt 0) { Write-Host "SIMULATION FAILED" -ForegroundColor Red; exit 1 }
Write-Host "SIMULATION PASSED"
exit 0
