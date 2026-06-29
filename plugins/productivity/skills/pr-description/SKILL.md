---
name: pr-description
description: Generate a Pull Request title in English and a description in French from the current git diff (working tree) of the directory where the skill is invoked. Use when the user asks for a PR / MR / pull request description, or types /pr-description. Readable prose accessible to junior developers, logically grouped changes (not a long bullet list).
---

# PR description (EN title, FR body)

Generate a **PR title in English** and a **PR description in French**, based on the **current** git diff (working tree) of the directory where the skill was invoked. The skill does **not** compare the branch to `main` / `master` / any base branch — it only describes the uncommitted / not-yet-pushed changes present right now.

## When to use

The user asks for a PR / MR / pull request description, or types `/pr-description`. The skill does not create the PR. It does two things: (1) prints the rendered Markdown in the chat as a human-readable preview, and (2) pushes the **raw** Markdown source to the system clipboard so the user can paste it straight into the Bitbucket UI with Ctrl+V. The clipboard is the canonical paste source — never ask the user to select-copy from the terminal.

## Procedure

### 1. Verify we're inside a git repo

```bash
git rev-parse --is-inside-work-tree
```

If this fails: tell the user the skill must be run from inside a git repo, and stop.

### 2. Collect the current diff

**Do not compare to `main` / `master` / any base branch.** The skill describes the **current diff**: staged + unstaged changes + untracked files present in the working tree, scoped to the current directory.

Always **scope to the current directory** with `-- .` — the skill describes what changes in the subfolder where it was invoked, not the whole repo.

```bash
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

<multi-paragraph Markdown description in French>
```

The line above showing a 3-backtick fenced block is documentation inside this SKILL.md. The actual chat output should NOT be inside any wrapping fence — write `**Title:** ...` followed by the body as plain top-level Markdown.

#### Style rules

- **Title in English** (plain text, no Markdown), **description in French as Markdown** (PR body), neutral and professional tone for both.
- **Markdown formatting** for the description:
  - Use Markdown sparingly to aid readability: `**bold**` on key terms, `` `inline code` `` for identifiers / paths / commands, fenced code blocks (```` ``` ```` with a language hint when relevant) for snippets, sub-headings (`###`) only if the description has 4+ paragraphs and would benefit from explicit sections.
  - Do **not** use top-level `#` headings (the PR already has one — its title).
  - Links use the `[label](url)` form. Reference-style links are fine if reused.
  - Stick to plain Markdown — no HTML, no Bitbucket-specific extensions.
- **Title**: single line in English, ~70 characters, descriptive, imperative mood ("Add Redis cache…", "Fix race condition…", "Refactor user resolver"). No `feat:` / `fix:` prefix unless the repo's commits or convention already use one.
- **Short description**: aim for 3 to 6 short paragraphs, never a full page. If the diff is tiny, two sentences are enough.
- **Readable prose**, not a wall of bullets. The description should make the reviewer want to read it. A short list is tolerated when it actually helps reading (e.g. 3 key takeaways), but it must not be the backbone of the text.
- **Group by intent**, not file by file. Five files modified for the same reason = a single mention. Think themes: "côté API", "côté front", "tests", "configuration", "refactor de X"…
- **Junior-friendly** (in French): avoid obscure jargon. If a precise technical term is required (e.g. *idempotence*, *circuit breaker*), a brief parenthetical explanation is enough. Prefer simple sentences and action verbs.
- **Describe what changes**, not what the code does in the abstract. E.g. "ajoute un cache LRU sur le résolveur d'utilisateurs" rather than "le résolveur d'utilisateurs sert à…".
- **Do not speculate** on the *why* if the diff doesn't say. If the intent shows up in commit messages or a branch name like `JIRA-123-fix-...`, use it. Otherwise stay factual.
- Mention explicitly, at the end of the description, **only if relevant**: breaking change, schema migration, new dependency, env var to add, manual deployment step. One line is enough.
- **Do not include**: "Co-Authored-By", "Generated with Claude", tool signatures.
- **Emojis**: allowed sparingly when they help reading, e.g. at the start of a paragraph to flag its theme (🔧 refactor, 🐛 fix, ✅ tests, ⚠️ point d'attention, 🚀 déploiement…). One emoji per paragraph max, never in the PR title, never as decoration.
- **Paragraph titles**: when a paragraph starts with a short bold "title" (e.g. `**Migration des tests vers JUnit 5.**`), the body **must go on a new paragraph after a blank line** — never inline on the same line as the title. Pattern:

  ```
  ✅ **Titre court du paragraphe.**

  Corps du paragraphe sur les lignes suivantes…
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

Write the content to a temp file first, then pipe it. This avoids shell-quoting issues with backticks, `$`, etc.

```bash
# 1. Write the raw markdown to a temp file
cat > /tmp/pr-description.md <<'PR_DESC_EOF'
**Title:** <english title>

<french markdown body>
PR_DESC_EOF

# 2. Push it to the clipboard, trying tools in order
if command -v wl-copy >/dev/null 2>&1 && [ -n "$WAYLAND_DISPLAY" ]; then
  wl-copy < /tmp/pr-description.md && echo "copied via wl-copy"
elif command -v xclip >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
  xclip -selection clipboard < /tmp/pr-description.md && echo "copied via xclip"
elif command -v xsel >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
  xsel --clipboard --input < /tmp/pr-description.md && echo "copied via xsel"
elif command -v pbcopy >/dev/null 2>&1; then
  pbcopy < /tmp/pr-description.md && echo "copied via pbcopy"
else
  echo "no clipboard tool found"
fi
```

**On success**, tell the user verbatim (in French):

> ✅ Description copiée dans le presse-papiers — colle directement (Ctrl+V) dans le champ description de Bitbucket. Ne sélectionne-copie pas depuis ce terminal : le rendu ci-dessus n'est qu'une prévisualisation.

**On failure** (no clipboard tool, headless session, etc.), do **not** suggest copying from the terminal. Instead, point at the temp file:

> ⚠️ Impossible de copier dans le presse-papiers automatiquement. Le markdown brut est dispo dans `/tmp/pr-description.md`. Pour le mettre au presse-papiers : `cat /tmp/pr-description.md | xclip -selection clipboard` (installe `xclip` ou `wl-clipboard` si nécessaire).

### 6. Stop

Do not create the PR, do not push, do not call Bitbucket. Once the rendered preview is in the chat and the clipboard message is shown, the task is done.

## Example output

What the chat displays (the renderer styles it; the same raw text — without the outer 4-backtick fence shown here for documentation — is what lands on the clipboard):

````
**Title:** Add Redis cache on the user resolver

Cette PR introduit un **cache Redis** devant le résolveur d'utilisateurs, identifié comme un point chaud sur les endpoints de listing. Les appels répétés au même identifiant sont désormais servis depuis le cache avec une TTL de 5 minutes.

🔧 **Extraction du résolveur dans un service dédié.**

Pour pouvoir brancher le cache sans dupliquer la logique, le résolveur a été déplacé dans un service à part. Les appelants existants passent par la même interface qu'avant, donc rien à changer côté contrôleurs.

⚙️ **Nouvelle configuration `users.cache.ttl`.**

Une nouvelle propriété a été ajoutée (valeur par défaut : `5m`), et la connexion Redis réutilise le bean déjà présent pour les sessions :

```yaml
users:
  cache:
    ttl: 5m
```

✅ **Couverture de tests étendue.**

Les tests unitaires du résolveur ont été complétés pour couvrir les cas *hit* / *miss*, et un test d'intégration vérifie l'invalidation lors d'une mise à jour utilisateur.

⚠️ À noter : pensez à vérifier que la variable `REDIS_URL` est bien définie dans les environnements de staging et prod avant le merge.
````

Followed in the chat (separately, after the rendered preview) by:

> ✅ Description copiée dans le presse-papiers — colle directement (Ctrl+V) dans le champ description de Bitbucket. Ne sélectionne-copie pas depuis ce terminal : le rendu ci-dessus n'est qu'une prévisualisation.
