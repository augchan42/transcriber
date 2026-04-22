# ADR-002: PowerShell Script Encoding and Content Rules

**Date:** 2026-04-22
**Status:** Accepted

## Context

This is a Windows-targeted project. The release pipeline
(`scripts\*.ps1`) is intended to run on a fresh Windows 11 machine with
whatever PowerShell happens to ship — in practice that means **Windows
PowerShell 5.1** (`powershell.exe`), not PowerShell 7+ (`pwsh.exe`). 5.1
is still the default that double-clicking a `.ps1` invokes, and we can't
require contributors or release engineers to install pwsh.

During the first attempt to run `scripts\publish-release.ps1`, parsing
failed with confusing errors like:

```
Missing expression after unary operator '-'.
Unexpected token 'Portable' in expression or statement.
The string is missing the terminator: '.
```

These errors pointed at a here-string that was syntactically valid and
parsed fine in PowerShell 7. Investigation traced the failure to the
file containing a Unicode **em-dash** character (`—`, U+2014) encoded
as UTF-8 (`E2 80 94`), in a file saved **without a byte-order mark**.

Windows PowerShell 5.1 reads BOM-less `.ps1` files using the
system's active ANSI code page (CP1252 on most US/EU Windows installs).
The three bytes `E2 80 94` then decode to the three characters `â € "`
(plus non-breaking-space-like chars), which turn into garbage tokens the
parser can't recover from. The parser failure then cascades forward and
points at a line that is itself fine — the real fault is tens of lines
earlier.

The same trap applies to any non-ASCII character: smart quotes (`"` `"`
`'` `'`), en-dash (`–`), ellipsis (`…`), accented letters, CJK, etc.

PowerShell 7 reads `.ps1` as UTF-8 by default and does not have this
problem. Many repos work around the issue by writing scripts with a
UTF-8 BOM so both 5.1 and 7 agree on the encoding. We chose not to do
that (see Alternatives below).

## Decision

### Rule 1: PowerShell script files MUST be ASCII-only

All `.ps1` files in `scripts\` and anywhere else in the repo are
restricted to 7-bit ASCII characters. No em-dashes, no smart quotes, no
accented letters, no emoji — not in comments, not in strings, not in
error messages.

Use these ASCII substitutes:

| Don't write | Write instead |
|---|---|
| `—` (em-dash) | `--` |
| `–` (en-dash) | `-` |
| `"` `"` (curly double quotes) | `"` `"` |
| `'` `'` (curly single quotes) | `'` `'` |
| `…` (ellipsis) | `...` |
| `→` (arrow) | `->` |

### Rule 2: Avoid here-strings (`@"..."@` / `@'...'@`) in release scripts

Even when a here-string's syntax is correct, its closing delimiter
rules (must be at column 0, no trailing content) make it fragile under
IDE reformatting, copy/paste into other tools, and through our own
Edit tooling. Build multi-line strings instead from an array joined with
explicit line endings:

```powershell
$body = @(
    'first line',
    "second line with $interpolation",
    ''
) -join "`r`n"
```

This works identically in 5.1 and 7, survives every editor, and sidesteps
both the ASCII rule (single-quoted entries need no escaping for most
characters) and the here-string parser.

### Rule 3: Native commands — don't redirect stderr, branch on `$LASTEXITCODE`

Separately relevant to these scripts: in PS 5.1, redirecting a native
executable's stderr (`2>$null`, `2>&1`, etc.) wraps each stderr line as a
`NativeCommandError` ErrorRecord. Combined with
`$ErrorActionPreference = 'Stop'` this halts the script on the very thing
we were trying to ignore (e.g., `gh release view` printing "release not
found" on its expected-missing path).

The fix is to **not redirect stderr at all**. Let it print to the console
(users want to see it anyway) and decide flow-control by checking
`$LASTEXITCODE` after the call:

```powershell
gh release view $tag --json tagName | Out-Null
if ($LASTEXITCODE -eq 0) { throw "already exists" }
```

## Consequences

- All four release scripts (`publish-release.ps1`, `submit-winget-pr.ps1`,
  `validate-winget.ps1`, `update-winget-manifest.ps1`) were cleaned up
  under these rules and syntax-validated via the PowerShell parser.
- Contributor-facing docs (`docs/RELEASING.md`) can still use Unicode
  freely — the rule applies only to `.ps1` files, not markdown.
- If we ever want richer punctuation in release-notes output produced by
  a script, we can still emit Unicode *at runtime* (e.g., by reading from
  a UTF-8 `.txt` template), just not as literal characters in the `.ps1`
  source.

## Alternatives considered

### Save all `.ps1` files with UTF-8 BOM

Adding `EF BB BF` to the start of every `.ps1` would make PS 5.1 read
them as UTF-8, solving the em-dash problem at the source. Rejected
because:

- Many editors (including our Write tool) default to BOM-less UTF-8, so
  enforcing BOM requires either a pre-commit hook or a manual audit on
  every change.
- PowerShell 7, rustfmt, black, prettier, and most cross-platform tooling
  treat BOM as an anti-pattern. Mixing BOM and no-BOM files in one repo
  invites a different class of bug (some tools mis-report encoding).
- The ASCII-only rule is zero-infrastructure and visually obvious when
  reading a diff.

### Require `pwsh` (PowerShell 7+) for release scripts

PS 7 reads UTF-8 correctly and wouldn't care about em-dashes. Rejected
because PS 7 is a separate install on Windows 11 (shipped as `pwsh.exe`,
not default) and the release pipeline has to work from any
freshly-cloned checkout, including from contributors who don't have 7
installed.

### Keep Unicode, add a lint step

A pre-commit hook that greps `.ps1` for non-ASCII bytes would catch the
problem before commit. Worth revisiting if the ASCII-only rule becomes
cumbersome, but for a small scripts directory the rule is trivial to
follow by eye.

## References

- PowerShell docs on script file encoding:
  <https://learn.microsoft.com/en-us/powershell/scripting/dev-cross-plat/vscode/understanding-file-encoding>
- Microsoft's writeup of the CP1252 default in PS 5.1:
  <https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding>
- Original failure in this repo: attempt to run
  `.\scripts\publish-release.ps1 -Version 2.0.0`, 2026-04-22. Em-dashes
  in comments at lines 49 and 58, plus an em-dash in the release-notes
  here-string, broke the parser at what looked like line 66.
