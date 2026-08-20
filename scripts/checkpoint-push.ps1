[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkPackage,

    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(Mandatory = $true)]
    [string]$GateCommand,

    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$Paths
)

$ErrorActionPreference = "Stop"

& git rev-parse --is-inside-work-tree | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Not inside a Git worktree" }

$branch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch) -or $branch -eq "main") {
    throw "Checkpoint pushes must use a work-package branch, not main"
}

Write-Host "Running checkpoint gate: $GateCommand"
& powershell -NoProfile -Command $GateCommand
if ($LASTEXITCODE -ne 0) { throw "Checkpoint gate failed" }

& git diff --check -- . ":(exclude)native/upstream/mozilla-translations/**"
if ($LASTEXITCODE -ne 0) { throw "Working-tree diff check failed" }
& git status --short

& git add -- $Paths
if ($LASTEXITCODE -ne 0) { throw "git add failed" }
if (Test-Path "native/upstream/mozilla-translations") {
    & python .\scripts\upstream\snapshot.py stage
    if ($LASTEXITCODE -ne 0) { throw "byte-exact upstream staging failed" }
}
& git diff --cached --check -- . ":(exclude)native/upstream/mozilla-translations/**"
if ($LASTEXITCODE -ne 0) { throw "Staged diff check failed" }

& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { throw "No staged changes for $WorkPackage" }

& git commit -m "${WorkPackage}: ${Message}"
if ($LASTEXITCODE -ne 0) { throw "commit failed" }
& git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw "push failed" }
& git fetch origin $branch
if ($LASTEXITCODE -ne 0) { throw "fetch failed" }

$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse "origin/$branch").Trim()
if ($localSha -ne $remoteSha) {
    throw "Local SHA $localSha differs from remote SHA $remoteSha"
}

Write-Host "Checkpoint saved remotely."
Write-Host "Branch: $branch"
Write-Host "Commit: $localSha"
