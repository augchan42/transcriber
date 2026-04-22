<#
.SYNOPSIS
    Create a GitHub release for a new transcriber version.

.DESCRIPTION
    Wraps `gh release create` with the standard release notes. Uploads
    TranscriberPortable.zip from the repo root as the release asset.

    Requires the GitHub CLI (`gh`) to be installed and authenticated.

.PARAMETER Version
    The new version string, e.g. "2.0.1". No leading "v"; the tag will
    be created as "v<Version>".

.PARAMETER Draft
    Create as a draft release (not publicly visible). Useful for testing.

.EXAMPLE
    .\scripts\publish-release.ps1 -Version 2.0.0

.EXAMPLE
    .\scripts\publish-release.ps1 -Version 2.0.0 -Draft
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [switch]$Draft
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$zipPath  = Join-Path $repoRoot 'TranscriberPortable.zip'

if (-not (Test-Path $zipPath)) {
    throw "TranscriberPortable.zip not found at $zipPath. Run release.bat first."
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    throw "GitHub CLI (gh) not found. Install from https://cli.github.com/ and run 'gh auth login'."
}

$tag = "v$Version"

# Check the tag doesn't already exist on GitHub. gh prints "release not found"
# to stderr when the tag doesn't exist -- that's expected and shown to the user;
# we only branch on the exit code. Stderr is NOT redirected, because `2>$null`
# in PS 5.1 wraps stderr lines as NativeCommandError records and $ErrorActionPreference=Stop
# then halts the script on the expected "not found" path.
Write-Host "Checking whether $tag already exists on GitHub..."
gh release view $tag --json tagName | Out-Null
if ($LASTEXITCODE -eq 0) {
    throw "Release $tag already exists on GitHub. Delete it first or bump the version."
}
Write-Host "  (not found -- good, we'll create it)"
Write-Host ""

# Build notes as an array of single-quoted (fully literal) strings joined by
# CRLF. Avoids here-string parsing quirks in Windows PowerShell 5.1 and keeps
# the file ASCII-safe for default script encodings.
$notes = @(
    '## What''s new',
    '- (edit me before publishing)',
    '',
    '## Install',
    '- **Portable zip**: download `TranscriberPortable.zip` below, extract, run `transcriber.exe`',
    '- **winget**: `winget install Augchan42.Transcriber`',
    '',
    '## First-time YouTube upload setup',
    'Everything except YouTube upload works out of the box. For uploads, see',
    '`youtube-setup.md` inside the zip for a 5-minute Google OAuth setup.'
) -join "`r`n"

$notesFile = New-TemporaryFile
try {
    Set-Content -Path $notesFile -Value $notes -Encoding utf8

    Write-Host "Creating GitHub release $tag ..."
    Write-Host "  Title: Video Transcriber $tag"
    Write-Host "  Asset: $zipPath"
    if ($Draft) { Write-Host "  Draft: yes" }
    Write-Host ""

    $args = @(
        'release', 'create', $tag,
        $zipPath,
        '--title', "Video Transcriber $tag",
        '--notes-file', $notesFile
    )
    if ($Draft) { $args += '--draft' }

    & gh @args
    if ($LASTEXITCODE -ne 0) { throw "gh release create failed (exit $LASTEXITCODE)" }
}
finally {
    Remove-Item $notesFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Release published. View at: https://github.com/augchan42/transcriber/releases/tag/$tag"
Write-Host ""
Write-Host "Next: edit the release notes in the GitHub UI to describe what's new,"
Write-Host "then run scripts\submit-winget-pr.ps1 -Version $Version"
