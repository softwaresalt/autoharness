# Resolve global autoharness agent directory
$autoharness_home = (autoharness home 2>$null)
$global_agents_src = if ($autoharness_home) { Join-Path $autoharness_home ".github\agents" } else { $null }

# Inject global agents into .github/local-agents (non-destructive — skip files already present)
# This is the directory the CLI scans for agents alongside .github/agents.
if ($global_agents_src -and (Test-Path $global_agents_src)) {
    $local_agents = ".github\local-agents"
    New-Item -ItemType Directory -Path $local_agents -Force | Out-Null
    Get-ChildItem "$global_agents_src\*.agent.md" | ForEach-Object {
        $dest = Join-Path $local_agents $_.Name
        if (-not (Test-Path $dest)) { Copy-Item $_.FullName $dest }
    }
}

# $env:ENGRAM_DATA_DIR = ".\.engram"
$env:COPILOT_HOME = ".\.copilot"
$env:GITHUB_TOKEN = (gh auth token)
D:\Tools\ghcpcli\copilot.exe
