<#
.SYNOPSIS
    Searches installed skills by keyword for dynamic skill discovery.
.DESCRIPTION
    Scans all SKILL.md files under .github/skills/ and returns matches where
    the keyword appears in the skill directory name or the YAML frontmatter
    description field. Enables lazy loading of skill definitions instead of
    bulk-loading every skill into the agent context.
.PARAMETER Keyword
    The search term to match against skill names and descriptions.
.EXAMPLE
    scripts/search.ps1 review
    scripts/search.ps1 "circuit breaker"
    scripts/search.ps1 build
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Keyword
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$skillsRoot = Join-Path (Get-Location) '.github' 'skills'

if (-not (Test-Path -LiteralPath $skillsRoot)) {
    Write-Error "Skills directory not found: $skillsRoot"
    exit 1
}

$results = @()

$skillDirs = Get-ChildItem -Path $skillsRoot -Directory

foreach ($dir in $skillDirs) {
    $skillFile = Join-Path $dir.FullName 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile)) {
        continue
    }

    $skillName = $dir.Name
    $description = ''

    # Extract description from YAML frontmatter
    $content = Get-Content -LiteralPath $skillFile -TotalCount 10
    $inFrontmatter = $false
    foreach ($line in $content) {
        if ($line -match '^---\s*$') {
            if ($inFrontmatter) { break }
            $inFrontmatter = $true
            continue
        }
        if ($inFrontmatter -and $line -match '^\s*description:\s*"?(.+?)"?\s*$') {
            $description = $Matches[1]
            break
        }
    }

    # Match keyword against skill name or description (case-insensitive)
    $keywordLower = $Keyword.ToLower()
    if ($skillName.ToLower().Contains($keywordLower) -or
        $description.ToLower().Contains($keywordLower)) {

        $relativePath = ".github/skills/$skillName/SKILL.md"
        $results += [PSCustomObject]@{
            Skill       = $skillName
            Description = if ($description.Length -gt 70) {
                $description.Substring(0, 67) + '...'
            } else {
                $description
            }
            Path        = $relativePath
        }
    }
}

if ($results.Count -eq 0) {
    Write-Host "No skills found matching: '$Keyword'"
    Write-Host "Try broader keywords or list all: Get-ChildItem .github/skills/ -Directory | Select-Object Name"
    exit 0
}

$results | Format-Table -AutoSize -Wrap
Write-Host "`n$($results.Count) skill(s) found. Load a skill with: Get-Content <Path>"
