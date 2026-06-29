---
name: pr-ready
description: Check whether the current branch is ready to open a Pull Request — verifies dev & PR conventions (clean working tree, changelog updated, tests present and passing, code quality, coherent diff) and returns a Pass/Fail checklist with a global verdict. Use when the user asks "is my PR ready", "can I open the PR", "check before I push/merge", asks for a pre-PR / pre-merge review, or types /pr-ready. Report only — it never modifies the code.
---

# PR ready — pre-PR convention check

Audit the **current branch** against dev and PR conventions, and tell the user whether it is ready to open a Pull Request. The output is a **checklist with a global verdict** (`✅ ready` / `⚠️ almost` / `❌ not ready`) plus actionable recommendations.

This skill **reports only — it never edits code, never commits, never pushes, never opens the PR.** Its job is to give the developer an honest pre-flight check so review time is spent on substance, not on catching a missing changelog entry or a failing test.

> **Windows skill.** Commands are written for **Windows / PowerShell**. `git` commands are shell-agnostic; stack commands (Maven, npm, pytest) are the same on Windows.

## When to use

The user is about to open a PR / MR and wants a sanity check first, or types `/pr-ready`. Typical phrasings: "est-ce que ma PR est prête ?", "je peux push ?", "check avant la PR", "review avant merge". The skill does **not** create the PR — pair it with `pr-description` once the verdict is green.

## Output language

Write the report **in the language the user is using in the conversation** (French if they speak French, English if English…). The check names below are given in English for reference, but translate them in the output to match the conversation.

## Procedure

### 1. Require a clean working tree first

The audit reflects what will actually land in the PR — i.e. **committed** work. Uncommitted edits would make the checklist lie (a test you wrote but didn't commit isn't in the PR). So before anything else:

```powershell
git rev-parse --is-inside-work-tree
git status --short
```

- If `git rev-parse` fails → tell the user the skill must run inside a git repo, and stop.
- If `git status --short` shows **any** staged, unstaged, or untracked change → **stop and ask the user to commit (or stash) first.** Do not analyze a dirty tree. Phrase it plainly, e.g.: "Ton working-tree n'est pas propre — commit (ou stash) tes changements puis relance `/pr-ready`, pour que l'audit porte sur ce qui partira vraiment dans la PR." List the dirty files so they know what's pending. Then stop.

Only once the tree is clean do you continue.

### 2. Determine the scope (branch vs base)

A PR is the set of commits on the branch that aren't on its base. Find the base branch and the diff against it.

```powershell
# current branch
git rev-parse --abbrev-ref HEAD

# default/base branch — try origin's HEAD, then fall back to main / master
git symbolic-ref --quiet refs/remotes/origin/HEAD   # e.g. refs/remotes/origin/main
git branch -r                                        # to eyeball main vs master if the above is unset
```

Pick the base in this order: `origin/HEAD` target if set → `origin/main` → `origin/master` → `main` → `master`. If the current branch *is* the base branch (e.g. work was done directly on `main`), say so and treat the scope as "commits not yet pushed" (`git log @{u}..HEAD` if an upstream exists). If you genuinely can't determine a base, ask the user which branch to compare against rather than guessing.

Collect the PR scope (use `...` so you compare against the merge-base, not the literal tip):

```powershell
$base = "origin/main"   # the base you resolved above

git log --oneline "$base...HEAD"     # commits in this PR
git diff --stat "$base...HEAD"       # files changed, with churn
git diff "$base...HEAD"              # full diff (read selectively if large)
```

If the diff is large, read `--stat` first and `Read` the most-changed files selectively. Never invent changes you haven't seen in the diff.

### 3. Detect the stack(s)

Look at the repo root (and changed paths) to decide which toolchain commands apply. A repo can be polyglot — detect all that apply.

- **Java / Maven** — `pom.xml`. Multi-module if the root pom has `<modules>`. Tests under `src/test/java`. Commands: `mvn`.
- **Java / Gradle** — `build.gradle` / `build.gradle.kts` → `./gradlew` (or `gradle`).
- **Node** — `package.json`. Read its `scripts` for the real `test` / `lint` / `build` commands and the package manager (lockfile: `package-lock.json` → npm, `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm). Tests usually under `test/`, `__tests__/`, or `*.spec.*` / `*.test.*`.
- **Python** — `pyproject.toml` / `setup.py` / `pytest.ini` / `tox.ini`. Tests under `tests/` or `test_*.py`. Commands: `pytest`, and a linter if configured (`ruff`, `flake8`).

If no known stack is detected, run the language-agnostic checks (changelog, coherence, hygiene) and clearly note that build/test/lint couldn't be auto-run.

### 4. Run the checks

Group findings under the categories below. For each check, assign a status:

- **✅ Pass** — convention satisfied.
- **⚠️ Warning** — not blocking, but worth the author's attention (judgment call).
- **❌ Fail** — convention violated; should be fixed before the PR.
- **➖ N/A** — doesn't apply to this repo (say why).

**Hybrid execution model:** *inspect everything*, *run the cheap checks now*, and *propose the expensive ones*. Cheap = compile + lint (seconds). Expensive = full test suite + coverage (can be minutes). Run the cheap ones automatically; for the expensive ones, run them if the user already asked for a full check, otherwise inspect statically and offer to run them ("Je peux lancer `mvn verify` si tu veux la confirmation runtime — ça prend ~2 min").

#### A. Changelog

Many repos keep a changelog (`CHANGELOG.md`, `CHANGES.md`, a `changelog/` folder, or a "Keep a Changelog" / Conventional-Commits setup). Check whether the repo has one, and if so whether this branch updated it.

- No changelog convention in the repo → ➖ N/A.
- Convention exists and the diff touches it meaningfully → ✅.
- Convention exists but the branch adds user-facing changes without a changelog entry → ❌, and point at where the entry should go.

#### B. Test coverage (presence, then optionally measured)

The cheap, reliable signal is **structural**: production code changed/added should come with test changes. Map each non-trivial source change to a test change in the same branch.

- New/changed production files **with** matching test changes → ✅.
- New public behavior (new endpoint, service method, business rule) **without** any test change → ❌, and name the untested units.
- Pure refactors, renames, config, docs → don't demand new tests; ⚠️ at most.

For a *measured* number, this is an expensive check — propose running coverage rather than forcing it: `mvn verify` (JaCoCo), `npm test -- --coverage`, `pytest --cov`. Report the figure only if you actually ran it; never fabricate a percentage.

#### C. Tests passing

- **Cheap, run now:** compile / type-check so an obviously broken branch fails fast — `mvn -q -DskipTests compile test-compile`, `tsc --noEmit` (TS) or the project's `build` script, a syntax/import check (Python).
- **Expensive, propose:** the full suite — `mvn test` (or `mvn verify`), the `test` script from `package.json`, `pytest`. If you ran it, report pass/fail and surface the first failures. If you didn't, say exactly which command the user should run.

Report the real outcome. If a command errors for environment reasons (missing DB, no network), say so — don't mark it as a code failure.

#### D. Code quality

- **Run a linter / static analysis if the repo configures one:** Checkstyle/Spotless/PMD (Maven), ESLint (`npm run lint`), Ruff/Flake8 (Python). Report the count by severity.
- **Scan the diff** for smells regardless of tooling: leftover debug (`System.out.println`, `console.log`, `print(` / `pprint`), `TODO` / `FIXME` introduced by this branch, commented-out code blocks, obviously dead code, hardcoded secrets / tokens / passwords / URLs, overly long methods, duplicated blocks.
- If the `code:sonar` skill is available and the user wants depth, mention it for a fuller scan — but don't auto-invoke it.

#### E. Dev coherence

This is the "does this hang together as one change" check — judgment, not tooling.

- The diff is **one logical change**, not several unrelated things bundled (mixing a feature + an unrelated refactor + a dependency bump is ⚠️/❌ depending on size).
- **Commit messages** follow the repo's convention (look at recent `git log` for the house style — ticket prefix, imperative mood, etc.).
- **Branch name** is consistent with the repo's convention if one is visible.
- No **merge-conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`) left in the diff.
- Naming is consistent with surrounding code; no obvious typo in public identifiers.

#### F. PR hygiene (flag only if relevant)

- New **dependency** added → note it (and whether it's pinned).
- **Schema migration**, **breaking change**, new **env var**, or manual **deploy step** → flag it, one line each.
- Large **generated/binary** files or `node_modules` / build artifacts accidentally committed → ❌.
- Accidentally committed secrets / `.env` → ❌, treat as high priority.

### 5. Write the report

Print the report **directly** in the chat (no wrapping code fence). Use this structure, translated to the conversation language:

```
## PR ready — <branch> → <base>

**Verdict : <✅ Prête / ⚠️ Presque / ❌ Pas prête>**

<one-sentence summary of why>

### Checklist
- <✅/⚠️/❌/➖> **Changelog** — <short finding>
- <✅/⚠️/❌/➖> **Couverture de test** — <short finding>
- <✅/⚠️/❌/➖> **Tests** — <short finding (ran? command?)>
- <✅/⚠️/❌/➖> **Qualité du code** — <short finding>
- <✅/⚠️/❌/➖> **Cohérence du dev** — <short finding>
- <✅/⚠️/❌/➖> **Hygiène PR** — <short finding>

### À corriger avant la PR
1. <actionable item, with file:line where useful>
2. …

### Checks lourds non lancés (optionnel)
- <e.g. "Suite complète : `mvn verify` (~2 min)"> — dis-moi si tu veux que je les lance.
```

**Verdict rule of thumb:** any ❌ → `❌ Pas prête`. No ❌ but one or more ⚠️ → `⚠️ Presque`. All ✅/➖ → `✅ Prête`. Keep the "À corriger" list ordered by impact (failures first), and tie each item to a concrete location so the fix is obvious.

Be honest and concise. The value of this skill is a trustworthy verdict — don't soften a real ❌ into a ⚠️, and don't inflate nitpicks into blockers. If everything is genuinely clean, a short green report is the right answer.

### 6. Stop

Do not edit, commit, push, or open the PR. Offer to run any expensive checks the user skipped, or to hand off to `pr-description` once the verdict is green — then stop.

## Example output (French)

```
## PR ready — feature/cache-redis → origin/main

**Verdict : ⚠️ Presque**

Le code compile et les tests passent, mais le changelog n'est pas à jour et un service public n'a pas de test.

### Checklist
- ❌ **Changelog** — `CHANGELOG.md` existe mais n'a pas d'entrée pour le cache Redis.
- ⚠️ **Couverture de test** — `UserResolver` est testé (hit/miss), mais `CacheMetricsService` (nouveau, public) n'a aucun test.
- ✅ **Tests** — `mvn test` lancé : 142 tests, 0 échec.
- ✅ **Qualité du code** — Checkstyle : 0 erreur. Aucun `System.out.println` ni TODO introduit.
- ✅ **Cohérence du dev** — diff centré sur le cache, messages de commit cohérents (`INCAS-1234 …`).
- ➖ **Hygiène PR** — pas de migration, pas de nouvelle dépendance, pas de secret.

### À corriger avant la PR
1. Ajouter une entrée dans `CHANGELOG.md` (section *Unreleased*) pour le cache Redis sur le résolveur d'utilisateurs.
2. Couvrir `CacheMetricsService` (`src/main/java/.../CacheMetricsService.java:18`) — au moins le cas nominal d'incrément des compteurs.

### Checks lourds non lancés
- Coverage mesurée : `mvn verify` (JaCoCo, ~2 min) — dis-moi si tu veux le chiffre exact.
```
