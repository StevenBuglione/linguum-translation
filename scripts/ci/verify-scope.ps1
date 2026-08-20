param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("windows")]
    [string] $Scope
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Milestone = (Get-Content architecture/current-milestone.txt -Raw).Trim()
if ($Milestone -eq "M0") {
    & .\scripts\ci\verify-m0-scope.ps1 -Scope $Scope
    exit $LASTEXITCODE
}
if ($Milestone -ne "M1") {
    throw "No Windows CI scope dispatcher is implemented for $Milestone."
}

Get-ChildItem scripts -Filter *.ps1 -Recurse | ForEach-Object {
    [void] [scriptblock]::Create((Get-Content $_.FullName -Raw))
}

& .\gradlew.bat architectureCheck --warning-mode=fail
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
