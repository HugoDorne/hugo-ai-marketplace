---
name: pr-description
description: Generate a Pull Request title and description in English from the current git diff (working tree) of the directory where the skill is invoked. Use when the user asks for a PR / MR / pull request description, or types /pr-description. French triggers: "génère la description de PR", "description de la pull request", "rédige la PR", "texte pour la PR", "fais la description de ma PR". Readable prose accessible to junior developers, logically grouped changes (not a long bullet list).
---

# PR description

Generate a **PR title and description in English**, based on the **current** git diff (working tree) of the directory where the skill was invoked. The skill does **not** compare the branch to `main` / `master` / any base branch — it only describes the uncommitted / not-yet-pushed changes present right now.

> **Windows skill.** All commands below are written for **Windows / PowerShell**. The clipboard is handled with the built-in `Set-Clipboard` cmdlet (always available on Windows 11), and the temp file lives under `$env:TEMP`.

## When to use

The user asks for a PR / MR / pull request description, or types `/pr-description`. The skill does not create the PR. It does two things: (1) prints the rendered Markdown in the chat as a human-readable preview, and (2) pushes the **raw** Markdown source to the system clipboard so the user can paste it straight into the Bitbucket UI with Ctrl+V. The clipboard is the canonical paste source — never ask the user to select-copy from the terminal.

## Procedure

### 1. Verify we're inside a git repo

```powershell
git rev-parse --is-inside-work-tree
```

If this fails: tell the user the skill must be run from inside a git repo, and stop.

### 2. Collect the current diff

**Do not compare to `main` / `master` / any base branch.** The skill describes the **current diff**: staged + unstaged changes + untracked files present in the working tree, scoped to the current directory.

Always **scope to the current directory** with `-- .` — the skill describes what changes in the subfolder where it was invoked, not the whole repo.

```powershell
# overview
git status --short -- .

# full staged + unstaged diff (against HEAD)
git diff --stat HEAD -- .
git diff HEAD -- .

# untracked files inside the scope
git ls-files --others --exclude-standard -- .
```

For each untracked file listed, read it with `Read` (untracked files don't appear in `git diff`).

If `git diff HEAD -- .` and `git status --short -- .` both return nothing: there's no current change to describe — tell the user and stop (do not invent a description from past commits).

If the diff is very large, read `--stat` first, then use `Read` selectively on the most-modified files. Never invent changes that aren't visible in the diff.

### 3. Write the output

Print the Markdown **directly** in the chat — no outer wrapper, no ` ```markdown ` fence around it. The chat renderer will style it (bold, code blocks, etc.) and that's fine: this rendered version is a **preview for the human**, not the paste source. The actual paste-ready raw Markdown lands on the system clipboard in step 5.

Output exactly this — no preamble, no postscript:

```
**Title:** <short English title, ~70 chars max>

<multi-paragraph Markdown description in English>
```

The line above showing a 3-backtick fenced block is documentation inside this SKILL.md. The actual chat output should NOT be inside any wrapping fence — write `**Title:** ...` followed by the body as plain top-level Markdown.

#### Style rules

- **Title and description both in English** — title as plain text (no Markdown), description as Markdown (PR body). Neutral and professional tone for both.
- **Markdown formatting** for the description:
  - Use Markdown sparingly to aid readability: `**bold**` on key terms, `` `inline code` `` for identifiers / paths / commands, fenced code blocks (```` ``` ```` with a language hint when relevant) for snippets, sub-headings (`###`) only if the description has 4+ paragraphs and would benefit from explicit sections.
  - Do **not** use top-level `#` headings (the PR already has one — its title).
  - Links use the `[label](url)` form. Reference-style links are fine if reused.
  - Stick to plain Markdown — no HTML, no Bitbucket-specific extensions.
- **Title**: single line in English, ~70 characters, descriptive, imperative mood ("Add Redis cache…", "Fix race condition…", "Refactor user resolver"). No `feat:` / `fix:` prefix unless the repo's commits or convention already use one.
- **Short description**: aim for 3 to 6 short paragraphs, never a full page. If the diff is tiny, two sentences are enough.
- **Readable prose**, not a wall of bullets. The description should make the reviewer want to read it. A short list is tolerated when it actually helps reading (e.g. 3 key takeaways), but it must not be the backbone of the text.
- **Group by intent**, not file by file. Five files modified for the same reason = a single mention. Think themes: "API side", "front-end", "tests", "configuration", "refactor of X"…
- **Junior-friendly**: avoid obscure jargon. If a precise technical term is required (e.g. *idempotence*, *circuit breaker*), a brief parenthetical explanation is enough. Prefer simple sentences and action verbs.
- **Describe what changes**, not what the code does in the abstract. E.g. "adds an LRU cache on the user resolver" rather than "the user resolver is used to…".
- **Do not speculate** on the *why* if the diff doesn't say. If the intent shows up in commit messages or a branch name like `JIRA-123-fix-...`, use it. Otherwise stay factual.
- Mention explicitly, at the end of the description, **only if relevant**: breaking change, schema migration, new dependency, env var to add, manual deployment step. One line is enough.
- **Do not include**: "Co-Authored-By", "Generated with Claude", tool signatures.
- **Emojis**: allowed sparingly when they help reading, e.g. at the start of a paragraph to flag its theme (🔧 refactor, 🐛 fix, ✅ tests, ⚠️ heads-up, 🚀 deployment…). One emoji per paragraph max, never in the PR title, never as decoration.
- **Paragraph titles**: when a paragraph starts with a short bold "title" (e.g. `**Migrate the tests to JUnit 5.**`), the body **must go on a new paragraph after a blank line** — never inline on the same line as the title. Pattern:

  ```
  ✅ **Short paragraph title.**

  Paragraph body on the following lines…
  ```

  An emoji preceding the title is allowed and stays on the title line. A paragraph with no bold title (just plain prose, optionally led by an emoji) is fine without this split — the rule only kicks in when there is an explicit bold title.

### 4. Validate the Markdown before printing

Before sending anything to the user, re-read the description and check:

- Every fenced code block opened with `` ``` `` is closed with a matching `` ``` ``. Count the fences — the total must be **even**.
- Every `` ` `` inline-code marker is closed on the same line.
- Every `[` has a matching `]`, every `(` in a link has a matching `)`.
- Every `**bold**` / `*italic*` / `_italic_` marker is balanced.
- No stray `<` / `>` left over from a removed HTML attempt.
- Lists are consistent (same marker, proper blank line before the list starts, sub-items indented by 2 spaces).
- No trailing unfinished sentence or placeholder like `<...>`, `TODO`, `TBD`.

If anything is off, **fix it silently** — do not print broken Markdown and then a correction. Only the clean version reaches the user.

### 5. Copy the raw Markdown to the clipboard

Push the raw Markdown (title + description) to the system clipboard so the user can paste it straight into the Bitbucket UI. **This is the canonical paste source** — the rendered block in the chat is only a preview.

Write the content to a temp file first, then push it to the clipboard. Going through a file (with a single-quoted here-string) avoids any quoting issue with backticks, `$`, etc.

```powershell
# 1. Write the raw markdown to a temp file (single-quoted here-string = literal, no $ / backtick expansion)
$path = Join-Path $env:TEMP 'pr-description.md'
@'
**Title:** <english title>

<english markdown body>
'@ | Set-Content -Path $path -Encoding UTF8

# 2. Push it to the clipboard
Get-Content $path -Raw | Set-Clipboard
Write-Output "copied to clipboard"
```

> The closing `'@` of the here-string **must** sit at column 0 (no leading whitespace) on its own line, or PowerShell raises a parse error.

**On success**, tell the user verbatim:

> ✅ Description copied to the clipboard — paste it directly (Ctrl+V) into the Bitbucket description field. Don't select-copy from this terminal: the rendering above is only a preview.

**On failure** (the unlikely case where `Set-Clipboard` is unavailable, e.g. a headless / non-Windows-PowerShell session), do **not** suggest copying from the terminal. Instead, point at the temp file:

> ⚠️ Couldn't copy to the clipboard automatically. The raw markdown is available at `%TEMP%\pr-description.md`. To put it on the clipboard: `Get-Content $env:TEMP\pr-description.md -Raw | Set-Clipboard` (or open the file and copy its contents).

### 6. Stop

Do not create the PR, do not push, do not call Bitbucket. Once the rendered preview is in the chat and the clipboard message is shown, the task is done.

## Example output

What the chat displays (the renderer styles it; the same raw text — without the outer 4-backtick fence shown here for documentation — is what lands on the clipboard):

````
**Title:** Add Redis cache on the user resolver

This PR introduces a **Redis cache** in front of the user resolver, identified as a hot spot on the listing endpoints. Repeated calls for the same identifier are now served from the cache with a 5-minute TTL.

🔧 **Extract the resolver into a dedicated service.**

To wire in the cache without duplicating logic, the resolver was moved into a separate service. Existing callers go through the same interface as before, so nothing changes on the controller side.

⚙️ **New `users.cache.ttl` configuration.**

A new property was added (default value: `5m`), and the Redis connection reuses the bean already present for sessions:

```yaml
users:
  cache:
    ttl: 5m
```

✅ **Extended test coverage.**

The resolver's unit tests were completed to cover the *hit* / *miss* cases, and an integration test verifies invalidation on a user update.

⚠️ Heads-up: make sure the `REDIS_URL` variable is defined in the staging and prod environments before merging.
````

Followed in the chat (separately, after the rendered preview) by:

> ✅ Description copied to the clipboard — paste it directly (Ctrl+V) into the Bitbucket description field. Don't select-copy from this terminal: the rendering above is only a preview.
