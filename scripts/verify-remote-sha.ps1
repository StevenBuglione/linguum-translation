[CmdletBinding()]
param([string]$Branch = "")

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (& git branch --show-current).Trim()
}
if ([string]::IsNullOrWhiteSpace($Branch)) { throw "No branch specified" }

& git fetch origin $Branch
if ($LASTEXITCODE -ne 0) { throw "fetch failed" }
$localSha = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse "origin/$Branch").Trim()
if ($localSha -ne $remoteSha) {
    throw "Local $localSha differs from remote $remoteSha for $Branch"
}
Write-Host "$Branch $localSha"
