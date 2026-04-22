<#
.SYNOPSIS
    Bump the three winget manifest files to a new version.

.DESCRIPTION
    Reads TranscriberPortable.zip in the repo root, computes its SHA256,
    and rewrites PackageVersion, InstallerUrl, InstallerSha256, and
    ReleaseDate across the installer / locale / version YAMLs under
    winget/.

    Run AFTER release.bat has produced the fresh zip.

.PARAMETER Version
    The new version string, e.g. "2.0.1". No leading "v".

.EXAMPLE
    .\scripts\update-winget-manifest.ps1 -Version 2.0.1
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$zipPath  = Join-Path $repoRoot 'TranscriberPortable.zip'
$wingetDir = Join-Path $repoRoot 'winget'

if (-not (Test-Path $zipPath)) {
    throw "TranscriberPortable.zip not found at $zipPath. Run release.bat first."
}

$sha = (Get-FileHash -Algorithm SHA256 $zipPath).Hash.ToUpper()
$today = (Get-Date).ToString('yyyy-MM-dd')
$installerUrl = "https://github.com/augchan42/transcriber/releases/download/v$Version/TranscriberPortable.zip"

Write-Host "Bumping winget manifests:"
Write-Host "  Version:  $Version"
Write-Host "  SHA256:   $sha"
Write-Host "  Date:     $today"
Write-Host "  URL:      $installerUrl"
Write-Host ""

$files = @(
    'Augchan42.Transcriber.yaml',
    'Augchan42.Transcriber.installer.yaml',
    'Augchan42.Transcriber.locale.en-US.yaml'
) | ForEach-Object { Join-Path $wingetDir $_ }

foreach ($f in $files) {
    if (-not (Test-Path $f)) { throw "Missing manifest file: $f" }
    $text = Get-Content $f -Raw

    $text = $text -replace '(?m)^(PackageVersion:\s*).*$', "`${1}$Version"
    $text = $text -replace '(?m)^(InstallerSha256:\s*).*$', "`${1}$sha"
    $text = $text -replace '(?m)^(\s*InstallerUrl:\s*).*$', "`${1}$installerUrl"
    $text = $text -replace '(?m)^(ReleaseDate:\s*).*$', "`${1}$today"

    Set-Content -Path $f -Value $text -Encoding utf8 -NoNewline
    Write-Host "  Updated: $([IO.Path]::GetFileName($f))"
}

Write-Host ""
Write-Host "Done. Review the diff with: git diff winget/"
