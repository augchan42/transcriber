# Releasing a new version

End-to-end checklist for cutting a new version and getting it into winget.

## One-time setup

Before your first release (v2.0.0):

- [ ] GitHub CLI installed and authenticated (`gh auth status`)
- [ ] `winget` available on the command line (comes with "App Installer")
- [ ] `ffmpeg` on PATH so `release.bat` can bundle it
- [ ] You've forked [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)
      to your GitHub account (the submit script will do this automatically on
      first run, but you can do it early via `gh repo fork microsoft/winget-pkgs`)

Optional (for future automation, see the last section):

- [ ] A GitHub PAT with `public_repo` scope, stored as the `WINGET_TOKEN`
      repo secret

---

## Cutting a release

Each release is five steps. Open **cmd.exe** (for `release.bat`) and
**PowerShell** (for the other scripts).

### 1. Build the portable zip

In **cmd.exe**:

```bat
release.bat
```

Produces `TranscriberPortable.zip` in the repo root and prints the
SHA256 at the end. You don't need to copy the SHA manually — the next
script reads it from the zip.

### 2. Bump the winget manifests

In **PowerShell**:

```powershell
.\scripts\update-winget-manifest.ps1 -Version 2.0.1
```

Rewrites `PackageVersion`, `InstallerUrl`, `InstallerSha256`, and
`ReleaseDate` across all three YAMLs in `winget/`. Review the diff:

```powershell
git diff winget/
```

Commit the bump on `main`:

```bash
git add winget/ LICENSE docs/RELEASING.md
git commit -m "Bump winget manifests to 2.0.1"
git push
```

### 3. Publish the GitHub release

In **PowerShell**:

```powershell
.\scripts\publish-release.ps1 -Version 2.0.1
```

Uses `gh release create` to tag `v2.0.1`, upload the zip as an asset,
and attach a release notes template. **Open the release on GitHub and
edit the notes to describe what's new before moving on** — winget
reviewers and users will read them.

To test the script without making it public, add `-Draft`:

```powershell
.\scripts\publish-release.ps1 -Version 2.0.1 -Draft
```

### 4. Validate the winget manifests

```powershell
.\scripts\validate-winget.ps1
```

This runs `winget validate`. Add `-Install` to also dry-install from the
local manifests (catches runtime issues the schema validator misses):

```powershell
.\scripts\validate-winget.ps1 -Install
```

If the install succeeds, uninstall with
`winget uninstall Augchan42.Transcriber` before moving on so the real
install (next step) is clean.

### 5. Submit the winget PR

```powershell
.\scripts\submit-winget-pr.ps1 -Version 2.0.1
```

This:

1. Clones (or updates) your fork of `microsoft/winget-pkgs` to
   `..\winget-pkgs\` (sibling of this repo)
2. Creates a branch `augchan42-transcriber-2.0.1`
3. Copies the three YAMLs into
   `manifests\a\Augchan42\Transcriber\2.0.1\`
4. Commits, pushes, opens the PR against `microsoft/winget-pkgs:master`

Track review with:

```powershell
gh pr list --repo microsoft/winget-pkgs --author "@me"
```

Expect:

- **Automated validation** (bot labels the PR `Validation-Completed` or
  leaves a comment with errors): **5–15 minutes**
- **Human moderator approval and merge**: **1–3 days** for new versions,
  sometimes longer for brand-new packages

Once merged, `winget install Augchan42.Transcriber` will work globally
within ~30 minutes as the source index refreshes.

---

## What can go wrong

| Symptom | Cause | Fix |
|---|---|---|
| `InstallerSha256` mismatch | You updated the zip but forgot to re-run `update-winget-manifest.ps1` | Re-run step 2, then re-push |
| `InstallerUrl` returns 404 | GitHub release wasn't published yet, or the tag has no asset | Re-run step 3; make sure `TranscriberPortable.zip` is attached to the release |
| Bot comment: "PackageVersion mismatch" | The three YAMLs disagree | Re-run `update-winget-manifest.ps1` — it keeps them in sync |
| `winget validate` fails on `ManifestVersion` | You're on an older winget client | `winget upgrade Microsoft.AppInstaller` |
| First-run SmartScreen warning | Unsigned exe | Not a winget blocker, but see the signing notes in the "Future work" section below |

---

## Future work: automated submissions

The repo ships with `.github/workflows/winget-releaser.yml`, currently
disabled via `if: false`. To enable automated winget PRs on every
GitHub release:

1. Generate a GitHub PAT:
   - Classic: `public_repo` scope
   - Fine-grained: `contents:write` + `pull-requests:write` on your fork
     of `microsoft/winget-pkgs`
2. Add it as a repo secret named `WINGET_TOKEN`
3. Remove the `if: false` line from the workflow
4. Next release: publish via `scripts\publish-release.ps1` and the
   workflow opens the winget PR automatically — you can skip steps 4 & 5
   of the manual checklist

The first release (v2.0.0) should still be submitted manually so you can
see the review flow and confirm the manifests are correct before handing
it off to automation.

---

## Code signing (not yet)

Even with winget, unsigned binaries still trigger Windows SmartScreen /
Smart App Control prompts. The real fix is code signing:

- **Free option**: [SignPath Foundation](https://signpath.org/apply) for
  qualifying OSS projects (they provide Authenticode signing via CI). Apply
  once the project has some traction.
- **Paid option**: Azure Trusted Signing (~$10/month) if you have a
  verifiable legal identity.
- **Intermediate**: Certum OSS cert (~$30/yr) — OV cert, so SmartScreen
  warning persists until reputation builds.

Once signed, add the signing step to `build.bat` before packaging and
everyone downstream (direct zip users, winget users) benefits immediately.
