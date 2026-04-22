<#
.SYNOPSIS
    Validate the local winget manifests and optionally dry-install them.

.DESCRIPTION
    Runs `winget validate` on the manifests in winget/, then optionally
    installs from the local manifests to prove they work end-to-end
    before submitting.

.PARAMETER Install
    Also run `winget install --manifest` to test-install locally.
    Use this before submitting to catch runtime problems.

.EXAMPLE
    .\scripts\validate-winget.ps1

.EXAMPLE
    .\scripts\validate-winget.ps1 -Install
#>
param(
    [switch]$Install
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$wingetDir = Join-Path $repoRoot 'winget'

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget not found. Install 'App Installer' from the Microsoft Store."
}

Write-Host "Validating manifests in $wingetDir ..."
winget validate --manifest $wingetDir
if ($LASTEXITCODE -ne 0) {
    throw "winget validate failed. Fix the errors above before submitting."
}
Write-Host "Manifests valid."

if ($Install) {
    Write-Host ""
    Write-Host "Dry-installing from local manifest ..."
    Write-Host "(You may be prompted to enable local manifest installs -- accept if asked.)"
    winget install --manifest $wingetDir
    if ($LASTEXITCODE -ne 0) {
        throw "winget install --manifest failed."
    }
    Write-Host ""
    Write-Host "Local install succeeded. Test the app, then uninstall with:"
    Write-Host "  winget uninstall Augchan42.Transcriber"
}
