<#
.SYNOPSIS
    Submit the transcriber winget manifests as a PR to microsoft/winget-pkgs.

.DESCRIPTION
    Clones/updates a fork of microsoft/winget-pkgs under a sibling directory,
    copies the local winget/ manifests into the correct path, and opens a PR.

    Requires gh (authenticated) and git.

    On first run, forks microsoft/winget-pkgs to your GitHub account.
    On later runs, reuses the existing fork.

.PARAMETER Version
    Version to submit, e.g. "2.0.1". Must match the PackageVersion in the
    local manifests.

.PARAMETER ForkDir
    Where to check out the winget-pkgs fork. Defaults to ..\winget-pkgs
    (sibling of this repo).

.EXAMPLE
    .\scripts\submit-winget-pr.ps1 -Version 2.0.0
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$ForkDir
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$wingetDir = Join-Path $repoRoot 'winget'

if (-not $ForkDir) {
    $ForkDir = Join-Path (Split-Path -Parent $repoRoot) 'winget-pkgs'
}

foreach ($cmd in 'gh', 'git') {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd not found on PATH."
    }
}

# --- Sanity check: manifest PackageVersion must match $Version ---
$installerYaml = Join-Path $wingetDir 'Augchan42.Transcriber.installer.yaml'
$manifestVersion = (Select-String -Path $installerYaml -Pattern '^PackageVersion:\s*(\S+)').Matches.Groups[1].Value
if ($manifestVersion -ne $Version) {
    throw "Manifest PackageVersion is '$manifestVersion' but you passed -Version $Version. Run scripts\update-winget-manifest.ps1 first."
}

# --- Verify the release asset is actually published ---
# Stderr from gh ("release not found") is shown directly on the missing-release
# path. We branch on $LASTEXITCODE rather than redirecting stderr, because
# `2>$null` in PS 5.1 wraps stderr as NativeCommandError records that
# $ErrorActionPreference=Stop would halt on.
$tag = "v$Version"
Write-Host "Verifying GitHub release $tag exists..."
gh release view $tag --json tagName | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub release $tag not found. Publish it first with scripts\publish-release.ps1."
}
Write-Host "  OK"
Write-Host ""

# --- Clone or update the fork ---
if (-not (Test-Path $ForkDir)) {
    Write-Host "Forking microsoft/winget-pkgs and cloning to $ForkDir ..."
    # --remote is not valid when a repo arg is passed (it only makes sense
    # from inside an upstream clone). Clone into $ForkDir by passing it as a
    # git-level positional after `--` (git clone's target-directory arg).
    # gh repo fork --clone automatically sets up `upstream` pointing at the
    # parent repo, so we don't need to add it ourselves.
    gh repo fork microsoft/winget-pkgs --clone -- $ForkDir
    if ($LASTEXITCODE -ne 0) { throw "Fork/clone failed." }
}
else {
    Write-Host "Using existing fork at $ForkDir"
    Push-Location $ForkDir
    try {
        # `git fetch upstream` prints "fatal: 'upstream' does not appear to be
        # a git repository" to stderr if the remote isn't configured yet. That
        # stderr is informational and visible -- we branch on exit code.
        git fetch upstream
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  (upstream remote not set -- adding it)"
            git remote add upstream https://github.com/microsoft/winget-pkgs.git
            git fetch upstream
            if ($LASTEXITCODE -ne 0) { throw "git fetch upstream failed." }
        }
        # Try master first (winget-pkgs default), fall back to main.
        git checkout master
        if ($LASTEXITCODE -ne 0) {
            git checkout main
            if ($LASTEXITCODE -ne 0) { throw "no master/main branch in fork." }
        }
        git pull upstream HEAD
        if ($LASTEXITCODE -ne 0) { throw "git pull upstream failed." }
        git push origin HEAD
        if ($LASTEXITCODE -ne 0) { throw "git push origin failed." }
    }
    finally { Pop-Location }
}

# --- Create branch, copy manifests, commit, push, PR ---
Push-Location $ForkDir
try {
    $branch = "augchan42-transcriber-$Version"
    $destDir = "manifests\a\Augchan42\Transcriber\$Version"

    git checkout -B $branch
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
    Copy-Item -Force (Join-Path $wingetDir '*.yaml') $destDir

    git add $destDir
    git commit -m "New version: Augchan42.Transcriber version $Version"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed -- maybe nothing changed?" }

    git push -u origin $branch --force-with-lease
    if ($LASTEXITCODE -ne 0) { throw "git push failed." }

    $prTitle = "New version: Augchan42.Transcriber version $Version"
    # Build as an array joined by CRLF; avoids PS 5.1 here-string parsing quirks.
    $prBody = @(
        "Adds Augchan42.Transcriber $Version.",
        '',
        '- Portable zip with bundled ffmpeg/ffprobe',
        '- Manifests validated locally with `winget validate`',
        '- SHA256 and InstallerUrl verified against the GitHub release asset',
        '',
        'Repo: https://github.com/augchan42/transcriber',
        "Release: https://github.com/augchan42/transcriber/releases/tag/v$Version"
    ) -join "`r`n"

    gh pr create --repo microsoft/winget-pkgs `
        --base master `
        --head "$((gh api user --jq .login)):$branch" `
        --title $prTitle `
        --body $prBody
    if ($LASTEXITCODE -ne 0) { throw "gh pr create failed." }
}
finally { Pop-Location }

Write-Host ""
Write-Host "PR opened. Track it with: gh pr list --repo microsoft/winget-pkgs --author @me"
Write-Host "Automated bot validation usually completes within 5-15 minutes."
