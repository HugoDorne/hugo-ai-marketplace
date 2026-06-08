---
name: check-updates
description: >
  Check a project's dependencies for newer available versions and apply the ones the user
  chooses. Use whenever the user asks about outdated or out-of-date dependencies, available
  upgrades, bumping/updating libraries or packages, "what can I update", "are my deps current",
  or wants to refresh Maven (pom.xml) or npm (package.json) versions. Works for Maven and
  Node/npm projects, including multi-module Maven builds. Reports updates grouped by risk and
  only edits files for the upgrades the user approves — it never bulk-upgrades silently.
disable-model-invocation: false
---

# Dependency Update Checker

Find newer versions of a project's dependencies, present them so the risk of each upgrade is
obvious, let the user pick, and apply only what they pick. The point is an informed, reversible
upgrade — not a blind "update everything", which is how builds quietly break.

## When this applies

The project has one or more `pom.xml` (Maven) and/or `package.json` (npm) files. Detect which
by looking at the project root and, for Maven, whether there are child modules. Run the matching
ecosystem section below. If both ecosystems are present, do both and present one combined list.

## Step 1 — Detect the project layout

- **Maven:** a `pom.xml` at the root. If it has a `<modules>` block it's a multi-module build —
  run commands from the root so the versions plugin walks every module in one pass.
- **npm:** a `package.json`. A `node_modules/` or lockfile (`package-lock.json`, `pnpm-lock.yaml`,
  `yarn.lock`) tells you which package manager is in use — prefer the one whose lockfile exists.

Tell the user the check needs the network and can take a minute (especially Maven, which contacts
every configured repository), so a slow command is expected, not stuck.

## Step 2 — Gather available updates

### Maven

Run the [versions plugin](https://www.mojohaus.org/versions-maven-plugin/). Use all three goals —
most well-kept projects centralise versions in `<properties>`, so dependency-level checks alone
miss them:

```
mvn versions:display-dependency-updates versions:display-plugin-updates versions:display-property-updates
```

Do **not** add `-q` here — these goals print their report at INFO level, so `-q` silences exactly
the `x.y.z -> a.b.c` lines you need and leaves you with an empty result and a wasted (slow) run.
Parse the reported `x.y.z -> a.b.c` lines. A version defined by a property must be changed at the
property, not at the dependency — `display-property-updates` is what surfaces those.

### npm

```
npm outdated --json
```

This prints a JSON object keyed by package, each with `current`, `wanted`, and `latest`. `wanted`
is the newest allowed by the existing semver range in `package.json`; `latest` is the newest
published. Surface both when they differ — jumping to `latest` may mean widening the range.

## Step 3 — Classify by risk and filter noise

For every candidate, compare current → newest and label the jump:

- **major** (first number changes, e.g. `2.x → 3.x`) — assume breaking changes; call these out.
- **minor** (middle number) — new features, usually compatible.
- **patch** (last number) — fixes, lowest risk.

**Skip pre-release versions by default** — anything with `SNAPSHOT`, `alpha`, `beta`, `rc`, `-M`,
or a build qualifier. Upgrading a stable dependency onto a pre-release is almost never what the
user wants; mention you filtered them and offer to include them if asked.

## Step 4 — Present and let the user choose

Show a compact, grouped list — patch/minor first (safe), major last (risky) — with the current and
target version and the bump type. Make major bumps visually distinct so the user doesn't approve a
breaking upgrade by reflex. For example:

```
Maven (pom.xml)
  minor   org.springframework.boot:spring-boot   3.2.1  → 3.3.0
  patch   com.fasterxml.jackson.core:jackson-databind   2.16.0 → 2.16.2
  MAJOR   com.google.guava:guava                 32.1.3 → 33.0.0   ⚠ may break

npm (package.json)
  patch   axios     1.6.2 → 1.6.8
  MAJOR   react      17.0.2 → 18.3.1  ⚠ may break

Which to apply? (e.g. "all safe", "1,2,4", "everything", "none")
```

Then ask which to apply. Accept ranges, "all", "all the safe ones / non-major", or "none". Don't
apply anything until they answer.

## Step 5 — Apply the chosen updates

Apply surgically so the diff is reviewable and the change is easy to revert.

### Maven

Prefer the versions plugin over hand-editing XML — it edits the right place (property vs inline
version) and won't corrupt formatting. Disable backup poms so you don't leave `*.versionsBackup`
files behind:

- Version held in a property:
  `mvn -q versions:set-property -Dproperty=<name> -DnewVersion=<v> -DgenerateBackupPoms=false`
- Inline dependency version:
  `mvn -q versions:use-dep-version -Dincludes=<group>:<artifact> -DdepVersion=<v> -DgenerateBackupPoms=false`

If a value can't be targeted cleanly that way, edit the `pom.xml` directly — but change only the
single version token, never reformat surrounding XML.

### npm

`npm install <pkg>@<version>` updates both `package.json` and the lockfile in one step and keeps
them consistent. Editing `package.json` by hand leaves the lockfile stale, so avoid that.

Preserve the project's existing version-pin style — changing it is an unasked-for edit the user
then has to notice and undo. If the current entry is an **exact pin** (`"1.4.0"`, no `^`/`~`), add
`--save-exact` so it stays exact; npm otherwise rewrites it to a caret range (`^1.17.0`). If the
entry already uses `^` or `~`, the default `npm install` keeps that style — leave it. Match what's
there rather than imposing a convention.

## Step 6 — Verify (offer, don't assume)

A version bump that compiles is the minimum proof it landed cleanly. Offer to verify, but ask
first — builds are slow and the user may want to batch the check:

- Maven: `mvn -q -pl <changed-modules> -am compile` (or a full `mvn -q compile` if many modules changed).
- npm: the project's build/test script (`npm run build`, `npm test`) if one exists.

If a verification fails, report exactly what broke and which upgrade likely caused it. Major bumps
are the usual culprit — offer to revert that one and keep the rest.

## Guardrails

- Never apply updates the user didn't explicitly choose.
- Don't push the changes or commit unless the user asks — leave the working tree for them to review.
- If no updates are found, say so plainly. "Everything's current" is a valid, useful result.
