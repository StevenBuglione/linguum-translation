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

& python .\scripts\upstream\snapshot.py prepare
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& python -m unittest discover -s scripts\upstream\tests -v
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& python -m unittest discover -s scripts\native\tests -v
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& python -m py_compile scripts\upstream\snapshot.py scripts\upstream\tests\test_snapshot.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& python -m py_compile scripts\native\bootstrap_tools.py scripts\native\fetch_canary_model.py scripts\native\run_host_canary.py scripts\native\stage_source.py scripts\native\tests\test_native_helpers.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

@(
    "native\patches\PATCHES.yaml",
    "testing\native\fixtures\es-en-v2.0.json",
    "toolchains\native-tools.lock.json"
) | ForEach-Object {
    & python -m json.tool $_ | Out-Null
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& python .\scripts\upstream\snapshot.py verify
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Get-ChildItem scripts -Filter *.ps1 -Recurse | ForEach-Object {
    [void] [scriptblock]::Create((Get-Content $_.FullName -Raw))
}

& .\gradlew.bat architectureCheck --warning-mode=fail
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
