param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("windows")]
    [string] $Scope
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Milestone = (Get-Content architecture/current-milestone.txt -Raw).Trim()
if ($Milestone -ne "M0") {
    throw "This scaffold check applies only to M0; found $Milestone."
}

$ForbiddenPaths = @("native/upstream", "native/runtime-build", "platform/jvm")
foreach ($Path in $ForbiddenPaths) {
    if (Test-Path $Path) {
        throw "M0 must not introduce $Path."
    }
}

Get-ChildItem scripts -Filter *.ps1 | ForEach-Object {
    [void] [scriptblock]::Create((Get-Content $_.FullName -Raw))
}

& .\gradlew.bat architectureCheck --warning-mode=fail
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
