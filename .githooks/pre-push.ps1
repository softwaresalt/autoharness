# .githooks/pre-push.ps1
# autoharness dogfood instance of the unified CI + local-gating primitive (P-019).
# Generated from templates/scripts/pre-push-quality-gates.ps1.tmpl, resolved for
# autoharness's real toolchain: the stdlib unittest suite + markdownlint.
#
# Runs the local quality gates before a push and BLOCKS the push (exit 1) on any
# failure. markdownlint is skipped with a warning when not installed. Single
# deterministic pass — no retry loop (circuit-breaker compatible).
#
# OPT-IN activation (see .githooks/README.md). This hook is committed but NOT
# active by default; nothing in the repo sets core.hooksPath for you.

$ErrorActionPreference = 'Continue'

Set-Location (& git rev-parse --show-toplevel)

$script:Failed = $false

Write-Host "[Test] `$env:PYTHONPATH='src'; python -m unittest discover -s tests"
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "unittest suite failed — push blocked (P-019)."
    $script:Failed = $true
}

if (Get-Command markdownlint -ErrorAction SilentlyContinue) {
    Write-Host "[Docs] markdownlint '**/*.md'"
    markdownlint "**/*.md"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "markdownlint failed (P-008) — push blocked."
        $script:Failed = $true
    }
} else {
    Write-Warning "markdownlint not found — skipping Markdown lint gate."
    Write-Warning "Install with: npm install -g markdownlint-cli"
}

if ($script:Failed) {
    Write-Error "One or more quality gates failed. Fix them, or push with --no-verify to bypass."
    exit 1
}

Write-Host "All local quality gates passed."
exit 0
