---
name: pr-hitl
description: >
  Review a Bitbucket pull request *with the human in the loop* — check the PR branch out in a
  throwaway git worktree, open it in a new IntelliJ window, and walk through the change together
  step by step so the reviewer actually understands and retains the code, then optionally post the
  review comments. Use whenever the user gives a Bitbucket PR URL and wants to understand, learn,
  discuss or walk through it rather than get a verdict: "review this PR with me", "walk me through
  this PR", "let's look at this PR together", "explain this PR", "I want to understand this change",
  "open this PR in IntelliJ". French triggers: "review cette PR avec moi", "on regarde cette PR
  ensemble", "explique-moi cette PR", "je veux comprendre ce changement", "fais-moi un walkthrough
  de la PR", "ouvre cette PR dans IntelliJ". Prefer this over `pr-review` whenever the user wants to
  learn from the PR, be walked through it, or discuss it interactively — `pr-review` is the fast
  autonomous alternative. Never posts anything to Bitbucket without explicit permission.
disable-model-invocation: false
---

# PR walkthrough — human-in-the-loop review

Review the Bitbucket pull request in `$ARGUMENTS` (a PR URL, or a repo + PR number) **as a shared
reading session**, not as a report. The reviewer wants two things out of this at once: a genuine
review of the change, and durable knowledge of the code it touches. The second one is the reason
this skill exists — a verdict they didn't learn anything from is a failure even if every finding is
correct.

That goal drives every design choice below: real code in a real IDE rather than a diff, a reading
order that follows the logic rather than the alphabet, and **dialogue instead of monologue**.

> **Windows skill.** Commands use PowerShell. `git` invocations are shell-agnostic.

## Why a worktree

The reviewer is mid-feature on their own branch and must keep working. A `git worktree` gives a
second working directory backed by the same object store: their tree is never touched, no stash is
involved, and nothing is re-cloned or re-downloaded beyond a fetch.

Check the worktree out **detached** (`--detach`). Git refuses to check out a branch that is already
checked out in another worktree, and the reviewer is often already sitting on the PR's source branch
(their own PR, or a colleague's branch they pulled). Detached HEAD sidesteps that entirely and keeps
the review naturally read-only.

## Procedure

### 1. Resolve the PR

Parse the URL — `https://bitbucket.org/<workspace>/<repo-slug>/pull-requests/<id>` (tolerate
`http://`, a missing `/overview`, and trailing query strings):

```
bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)
```

If the user gave only a number, resolve the repo from the current directory's `origin` remote.

Then invoke the **`is:bitbucket`** skill to fetch the PR metadata (`get-pr --repo <slug> --pr <id>`).
Use that skill rather than calling the API yourself — it owns the auth and the script path. You need
`title`, `description`, `state`, `author`, `source.branch.name` and `destination.branch.name`.

Also pull `list-comments` — an existing discussion tells you what has already been raised, and
repeating a point a colleague already made wastes everyone's time.

If the PR is `MERGED` or `DECLINED`, say so and ask whether to continue (a walkthrough of merged
code is still perfectly useful for learning; a review of it is mostly moot).

### 1b. Read the ticket — it's the intent the code is meant to serve

Pull the ticket key out of the PR title, the source branch, or the description (`INCAS-350`,
`IS-107470` — anything matching `[A-Z][A-Z0-9]+-\d+`) and read it through the **Atlassian / Jira MCP
tools** (`getJiraIssue`, plus its comments). If there's no key, or Jira isn't reachable, say so in one
line and carry on — the walkthrough still works, you just can't speak to intent.

This matters more for a learning session than for a verdict. Understanding *why* a change exists
starts with the problem someone was asked to solve, and the ticket is where that lives — along with
the domain vocabulary the code assumes you already know. Reading the code first and the ticket never
is how you end up understanding the mechanics of a change but not its purpose.

Read the **comments too**, not just the description. Acceptance criteria get renegotiated in
comments, and an unanswered product question there is often the most useful thing in the whole PR.

Then hold the ticket and the diff side by side:

- **Does the PR satisfy the acceptance criteria?** If an AC has no corresponding code, name it.
- **Does it do more than the ticket asks?** Extra scope isn't automatically wrong — it's frequently
  a Figma detail or a sibling ticket the author folded in — but it should be a conscious choice, so
  raise it as a question rather than a finding.
- **Is anything in the ticket still unresolved?** An open PM question that the code has quietly
  answered one way is worth surfacing before it ships.

Scope belongs to the author and the PM, never to you. Frame these as questions, and put them in the
open-questions part of the TL;DR rather than in the severity list.

### 2. Take the destination branch from the API, never assume `master`

**Stacked PRs are common here** and are the single easiest way to produce a badly wrong review. When
PR B targets PR A's branch instead of `master`, diffing against `master` silently includes all of
A's changes — so you explain and comment on code that isn't in this PR at all.

Always diff against `destination.branch.name` as reported by the API. When that destination is not
the repo's main branch, say so up front: *"this PR targets `feature/INCAS-349-…`, not `master` — it's
stacked on PR #808, so we're only looking at what #809 adds on top."* That framing matters for
learning too: it tells the reviewer where the boundary of the change is.

### 3. Locate the clone

The worktree has to come from an existing clone. Find it by matching the `origin` remote, not just
the directory name:

```powershell
# current directory first — often already the right repo
git rev-parse --is-inside-work-tree
git remote get-url origin

# otherwise look under the usual roots
Get-ChildItem -Path "$HOME\projects","$HOME\projects-perso" -Directory -Depth 1 -Filter "<slug>"
```

Confirm a candidate with `git -C <path> remote get-url origin` — it must reference
`<workspace>/<slug>`. If no clone exists, offer to clone it
(`git@bitbucket.org:<workspace>/<slug>.git`) rather than failing; ask where to put it.

### 4. Fetch the two branches and create the worktree

Fetch with explicit refspecs so the remote-tracking refs are definitely updated, then branch off a
throwaway worktree **outside** the clone (a worktree nested inside the repo confuses Maven, IntelliJ
and `.gitignore`):

```powershell
$clone = "<path to clone>"
$wt    = "$HOME\projects\reviews\<slug>-pr-<id>"

git -C $clone fetch origin `
  "+refs/heads/<source>:refs/remotes/origin/<source>" `
  "+refs/heads/<dest>:refs/remotes/origin/<dest>"

git -C $clone worktree add --detach $wt "origin/<source>"
```

Tell the reviewer the path and that their own tree is untouched — they are trusting you with a repo
they have uncommitted work in, so make the safety visible rather than implied.

### 5. Establish the scope before explaining anything

```powershell
git -C $wt log  --oneline "origin/<dest>..HEAD"      # the PR's commits
git -C $wt diff --stat    "origin/<dest>...HEAD"     # files + churn
```

Use `...` (three dots) so you diff against the **merge base**. With two dots you also see everything
that landed on the destination branch since the PR forked, which is not the author's work.

Read the full diff yourself now (`git -C $wt diff "origin/<dest>...HEAD"`). You need the whole
picture before you can choose a good reading order — but do **not** paste it at the reviewer.

### 6. Choose a reading order that follows the logic

This is where a walkthrough earns its keep over reading the diff in Bitbucket. Bitbucket shows files
alphabetically; understanding rarely flows that way. Order the discussion so each step makes the next
one make sense — typically:

1. **The intent** — the ticket / PR description, and the domain problem being solved.
2. **The entry point** — the controller, listener, scheduled job or public API that the change hangs off.
3. **The core logic** — where the actual behaviour lives, the interesting decisions.
4. **The supporting cast** — DTOs, mappers, config, migrations, only as far as they matter.
5. **The tests** — what the author decided was worth pinning down, and what they left uncovered.

Group related files into a handful of **themes** rather than marching through 30 files. If the PR is
large, say so and propose a scope: *"there are 24 files; 6 carry the real logic and the rest are
generated mappers — want the deep pass on those 6?"*

### 7. Open a new IntelliJ window on the worktree

Open the worktree as its own project — a **new window**, separate from whatever the reviewer is
working in. Files opened outside a project get no reliable Go-to-Declaration, which defeats the
purpose of using an IDE for learning.

```powershell
$idea = Get-ChildItem "C:\Program Files\JetBrains\IntelliJ IDEA*\bin\idea64.exe" |
        Sort-Object FullName -Descending | Select-Object -First 1
Start-Process $idea -ArgumentList $wt
```

Glob the versioned path so an IDE upgrade doesn't break the skill. Then open the important files —
the ones the walkthrough will actually cover, in the reading order from step 6:

```powershell
Start-Process $idea -ArgumentList "--line",42,"$wt\src\main\java\...\FooService.java"
```

Because IntelliJ routes a file to the window whose project contains it, these land in the review
window rather than the reviewer's work window. Warn them that a fresh worktree means a fresh index,
so navigation may lag for a minute on a big repo — then start with the intent (step 6.1), which
needs no IDE, and let indexing happen in the background.

### 8. Walk through it — one theme at a time, then stop

The failure mode of this skill is a wall of text: five themes, forty findings, no interaction. That
produces no learning and the reviewer skims it. So for **each theme**:

- Say what this part does and **why it exists** — the design pressure behind it, not a paraphrase of
  the code. The code is on screen; they can read it.
- Point at the specific file and line, and open it in the IDE if it isn't already.
- Flag anything review-worthy as you go, with a severity (see step 9). Findings are a by-product of
  understanding, not a separate pass.
- Surface what's genuinely non-obvious: an implicit contract, a transaction boundary, a subtle
  ordering dependency, something that will bite in six months.
- **Then stop and hand back.** Ask something real — whether the trade-off makes sense to them,
  whether they'd have done it differently, or whether they want to go deeper here. Then wait.

Follow where the reviewer takes it. If they ask "why not just do X?", that tangent *is* the value —
chase it, and use the IDE to show the answer (the caller that would break, the test that pins the
behaviour). If they say "yeah, next", move on without ceremony. For a deeper single-file
explanation, the `explain` skill is the right tool to reach for.

Match the conversation's language — French question, French answer.

### 8b. Draw a diagram when the shape is the hard part

Some things are genuinely hard to hold in your head from prose: a value travelling across two
upstream systems into one field, a call chain with a surprising ordering, a state machine. A small
ASCII diagram lands those in one look, and this is a learning session — the picture is often what
the reviewer still remembers next week.

Use one when the difficulty is **structural** (flow, ordering, or who-reads-what across a boundary),
and skip it otherwise. A diagram of something already obvious from two lines of code is noise that
buries the parts worth reading. Annotate the interesting points rather than drawing everything:

```
┌─ core trip planner ─────────────────────┐
│  JourneysPathResponse                   │
│    bikePark.bikePark: WsBikePark     ◄──┼── (1) read here
│    arrivalBikePark                ✗ NOT │
└──────────────────┬──────────────────────┘
                   ▼  PathMapper.mapExtraData()
        extraData.setStands(sanitize(capacity))
```

Marking what is *not* used (`✗ NOT`) is often as informative as marking what is. The `explain`
skill covers diagram types in more depth if a walkthrough needs a sequence or component view.

### 9. Collect findings with a severity as you go

Reuse the taxonomy from **`java-spring-best-practices`** so severities mean the same thing across the
toolbox: **blocker** (must fix before merge), **issue** (should fix), **suggestion** (recommend),
**nitpick** (optional). For a Java/Spring PR, invoke that skill for the stack-specific pass instead
of re-deriving its rules here — it already encodes the conventions this team reviews against.

Anchor every finding to `file:line` in the PR's diff. A finding you can't point at isn't actionable,
and inline comments need the exact location anyway.

**Don't build the project and don't run tests.** CI already does it — Jenkins and SonarQube run on
the PR's head commit and their verdict is on the PR page, which is more authoritative than anything
a local run proves. Three further reasons it's a bad trade here:

- It costs tens of minutes on these repos and the reviewer is sitting there waiting.
- **A Maven build in a linked worktree is broken anyway.** The worktree's `.git` is a file, not a
  directory; `jgitver` and `git-commit-id` can't read it, so the version degrades to
  `0.0.0-NO_WORKTREE_AND_INDEX` and dependency resolution fails. That failure looks exactly like a
  compile error in the PR — the trap is reporting a phantom blocker on perfectly good code.
- **`mvn install` from a review checkout corrupts the reviewer's `~/.m2`.** It publishes those
  bogus versions into the shared local repo, and the obvious workaround is worse: with
  `-Djgitver.skip=true` the version falls back to `0.0.0-SNAPSHOT`, which already exists as a real
  artifact — so it silently overwrites the reviewer's own jars.

So read the code, not the build output. When a finding genuinely needs runtime confirmation, say so
and name what would confirm it — that's an honest finding, and far better than a slow guess dressed
up as proof.

### 10. Close with a TL;DR, then ask before posting anything

A walkthrough is long by design, and the reviewer has just absorbed a lot in pieces. End with a
**TL;DR** that makes it stick — the point of the session was retention, and a recap is where the
scattered themes become one mental model:

```
## TL;DR
- **What it does:** <one or two sentences>
- **Where the logic lives:** <the 2-3 files that matter, with paths>
- **What to remember:** <the non-obvious things — the implicit contract, the guard in another
  class, the ordering dependency>
- **Findings:** <n blockers, n issues, n suggestions> — <the one that matters most>
- **Open questions:** <anything for the author or the PM>
```

Put it at the **end**, not the top: it's a recap of a shared reading session, not an abstract to
skim instead of doing the reading.

Then ask — **always ask, and never post as a side effect of anything above**:

```
Want me to post any of this to PR #<id>?
  a) a summary comment
  b) inline comments on the findings
  c) both
  d) nothing
```

The reviewer may want a subset — offer to go finding-by-finding if the list is long. Posting is
visible to the whole team the moment it lands, and some findings only made sense as conversation, so
default to nothing and let them choose. If they approve, invoke **`is:bitbucket`**
(`post-comment --body-stdin`, `post-inline-comment --file <path> --line <n>`) and report exactly what
was posted. Write comments in the language the team uses on that repo — check `list-comments` from
step 1.

### 11. Clean up

Ask before removing the worktree — they may want to keep poking at it, and the IntelliJ window is
still pointing there.

```powershell
git -C $clone worktree remove $wt      # --force only if something wrote into the worktree
git -C $clone worktree prune
```

Since step 9 rules out building, the worktree stays clean and plain `remove` succeeds. `--force` is
only needed if the reviewer edited files there or a build left `target/` behind.

Confirm their own branch and uncommitted work are exactly as they were. If `worktree remove` fails
because the IDE holds a file lock, say so and give them the command to run once they close the
window — don't leave them guessing why a directory is still there.

## What this skill does not do

It doesn't approve, merge or decline the PR, and it doesn't edit the code — this is a reading session
and a review, and acting on the PR is the reviewer's call. If they want to act, `is:bitbucket` has
`approve-pr`, `merge-pr` and `decline-pr`; hand off explicitly rather than doing it implicitly.

## Example opening

```
## PR #809 — INCAS-350 : Picto et capacité du parking à vélo sécurisé
backend-for-frontend · Hugo DORNE · OPEN

⚠️ Stacked: targets `feature/INCAS-349-bike-park-capacite-et-picto`, not `master`.
   We're looking only at what #809 adds on top of #808.

Worktree: ~/projects/reviews/backend-for-frontend-pr-809 (detached at origin/feature/INCAS-350-…)
Your tree: still on feature/INCAS-350-secure-bike-park-picto, nothing stashed.
IntelliJ: new window opening — indexing for a minute or so.

7 commits, 9 files (+184 / −22). Three themes:
  1. the picto resolution itself (BikeParkPictoResolver + its enum)
  2. how capacity reaches the step DTO
  3. the tests

Let's start with the intent while IntelliJ indexes. The ticket is about showing a *secure* bike
park differently from an ordinary one in the journey step… <explanation>

Does that framing match what you understood from the ticket, or should I dig into the domain first?
```
