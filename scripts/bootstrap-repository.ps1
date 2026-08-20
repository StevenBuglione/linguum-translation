[CmdletBinding()]
param(
    [string]$Repository = "StevenBuglione/linguum-translation",
    [ValidateSet("public", "private")]
    [string]$Visibility = "public",
    [string]$Description = "Firefox-compatible native translation for Kotlin Multiplatform"
)

$ErrorActionPreference = "Stop"

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required"
    }
}

Assert-Command git
Assert-Command gh
& gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw "gh is not authenticated" }

if (-not (Test-Path "START_HERE.md")) { throw "Run from the extracted handoff/repository root" }
if (-not (Test-Path "architecture/LOCKED_DECISIONS.md")) { throw "Frozen architecture source is missing" }
if (-not (Test-Path "MANIFEST.sha256")) { throw "MANIFEST.sha256 is missing" }

if (-not (Test-Path ".git")) {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw "git init failed" }
}

$branch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    & git switch -c main
} elseif ($branch -ne "main") {
    throw "Initial bootstrap must run on main, not $branch"
}

$paths = @(
    "START_HERE.md",
    "README.md",
    "AGENTS.md",
    "CODEX_EXECUTION_CONTRACT.md",
    "LINGUUM_TRANSLATION_COMPLETE_CODEX_HANDOFF.md",
    "MANIFEST.sha256",
    "architecture",
    "implementation",
    "research",
    "schemas",
    "codex",
    "scripts",
    "templates"
)

& git add -- $paths
if ($LASTEXITCODE -ne 0) { throw "git add failed" }
& git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "staged diff check failed" }

& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    & git commit -m "M0-WP01: add frozen Linguum Translation handoff"
    if ($LASTEXITCODE -ne 0) { throw "initial commit failed" }
} else {
    Write-Host "No initial handoff changes to commit."
}

& gh repo view $Repository 2>$null | Out-Null
$exists = $LASTEXITCODE -eq 0
$remoteUrl = "https://github.com/$Repository.git"

if ($exists) {
    Write-Host "Repository $Repository already exists; reusing it."
    & git remote get-url origin 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $existing = (& git remote get-url origin).Trim()
        if ($existing -ne $remoteUrl -and $existing -ne "git@github.com:$Repository.git") {
            throw "origin points to $existing instead of $Repository"
        }
    } else {
        & git remote add origin $remoteUrl
    }
} else {
    $visibilityFlag = if ($Visibility -eq "public") { "--public" } else { "--private" }
    & gh repo create $Repository $visibilityFlag --source=. --remote=origin --description $Description
    if ($LASTEXITCODE -ne 0) { throw "repository creation failed" }
}

& git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "initial push failed" }
& git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "fetch verification failed" }

$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse origin/main).Trim()
if ($localSha -ne $remoteSha) {
    throw "Remote SHA $remoteSha does not match local SHA $localSha"
}

Write-Host "Repository bootstrap verified."
Write-Host "Repository: https://github.com/$Repository"
Write-Host "Commit: $localSha"
