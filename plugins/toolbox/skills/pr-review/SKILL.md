---
name: pr-review
description: >
  Review a Bitbucket pull request autonomously from just its URL — check the PR out in a throwaway
  git worktree for full file context, review the change against dev and stack conventions, and
  present the findings plus the exact comments that would be posted, for approval before anything
  reaches Bitbucket. Use whenever the user drops a Bitbucket PR link and wants it reviewed,
  assessed or commented on: "review this PR", "what do you think of this PR", "any problems with
  this PR", "can I approve this", "review and comment on this PR". French triggers: "review cette
  PR", "relis cette PR", "qu'est-ce que tu penses de cette PR", "y a-t-il des problèmes dans cette
  PR", "commente cette PR", "je peux approuver cette PR". This is the fast autonomous mode — if the
  user wants to be walked through the PR to *understand* it, or wants it opened in IntelliJ, use
  `pr-hitl` instead. Never posts anything to Bitbucket without explicit permission.
disable-model-invocation: false
---

# PR review — autonomous

Review the Bitbucket pull request in `$ARGUMENTS` (a PR URL, or a repo + PR number) and produce a
review the user can act on: what the change does, what's wrong with it ranked by severity, and the
concrete comments that would be posted — **presented for approval, never posted unprompted.**

This is the fast lane. No IDE, no pauses, no dialogue: read the code, form a judgement, show the
work. If the user wants to learn the code rather than get a verdict, `pr-hitl` is the skill for that.

> **Windows skill.** Commands use PowerShell. `git` invocations are shell-agnostic.

## Why a worktree rather than the API diff

Bitbucket's diff endpoint returns hunks with about three lines of context, which is enough to spot
style problems and not much else. Most findings that matter — a missing transaction boundary, a null
that can now reach a caller, a test that doesn't actually assert the new behaviour — need the whole
file and its neighbours.

A `git worktree` gives that: the real tree at the PR's head, backed by the clone's existing object
store, without touching the user's working tree, without a stash, and without re-cloning. Check it
out **detached** — git refuses to check out a branch already checked out elsewhere, and the user is
often already sitting on the PR's source branch.

Never read the changed files from the user's main working tree instead. It's on a different branch,
so the content won't match the PR and the review would be about code that isn't there.

## Procedure

### 1. Resolve the PR

Parse the URL — `https://bitbucket.org/<workspace>/<repo-slug>/pull-requests/<id>` (tolerate
`http://`, a missing `/overview`, and trailing query strings):

```
bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)
```

If only a number was given, resolve the repo from the current directory's `origin` remote.

Invoke the **`is:bitbucket`** skill for metadata (`get-pr --repo <slug> --pr <id>`) rather than
calling the API directly — it owns the auth and its own script path. You need `title`,
`description`, `state`, `author`, `source.branch.name`, `destination.branch.name`.

Also fetch `list-comments`. Re-raising a point a colleague already made is noise, and an existing
thread often explains a decision that would otherwise look like a bug.

If the PR is `MERGED` or `DECLINED`, say so before reviewing — the findings may be moot.

### 1b. Read the ticket — "is this the right change?", not just "is this code correct?"

Extract the ticket key from the PR title, the source branch, or the description (`INCAS-350`,
`IS-107470` — anything matching `[A-Z][A-Z0-9]+-\d+`) and read it via the **Atlassian / Jira MCP
tools** (`getJiraIssue`, and its comments). No key, or Jira unreachable? Say so in one line and
review the code on its own terms.

Everything else in this skill checks whether the code does what it says. Only the ticket tells you
whether what it says is what was asked for — and that's a class of problem no amount of diff-reading
finds. A flawless implementation of the wrong scope still costs someone a round trip.

Read the **comments as well as the description**. Acceptance criteria get renegotiated there, and an
unanswered product question in the comments is frequently the most valuable thing you can surface.

Compare ticket against diff:

- **Unmet acceptance criteria** — an AC with no corresponding code. Name the AC.
- **Scope beyond the ticket** — often legitimate (a Figma detail, a folded-in sibling ticket), so ask
  rather than assert. "The AC only mentions X; Y came from …?" is the right shape.
- **Questions the ticket left open** that the code has now silently answered one way.

Put these under **open questions**, not under a severity. Scope is the author's and the PM's call,
and a reviewer who rules on it burns credibility they'll want for the real blockers.

### 2. Take the destination branch from the API, never assume `master`

**Stacked PRs are the easiest way to produce a badly wrong review.** When PR B targets PR A's branch
rather than `master`, diffing against `master` silently pulls in all of A's changes — so you review
and comment on code that isn't part of this PR, in front of the whole team.

Always diff against `destination.branch.name` as the API reports it, and when it isn't the repo's
main branch, state that in the report: *"stacked on #808 — reviewing only what #809 adds."*

### 3. Locate the clone

Match on the `origin` remote, not the directory name:

```powershell
git rev-parse --is-inside-work-tree      # current directory first
git remote get-url origin

Get-ChildItem -Path "$HOME\projects","$HOME\projects-perso" -Directory -Depth 1 -Filter "<slug>"
```

Confirm with `git -C <path> remote get-url origin` referencing `<workspace>/<slug>`. If there's no
clone, offer to clone `git@bitbucket.org:<workspace>/<slug>.git` and ask where — don't just fail.

### 4. Create the worktree

Fetch with explicit refspecs so the remote-tracking refs are certainly updated, and place the
worktree **outside** the clone (nested worktrees confuse Maven, IntelliJ and `.gitignore`):

```powershell
$clone = "<path to clone>"
$wt    = "$HOME\projects\reviews\<slug>-pr-<id>"

git -C $clone fetch origin `
  "+refs/heads/<source>:refs/remotes/origin/<source>" `
  "+refs/heads/<dest>:refs/remotes/origin/<dest>"

git -C $clone worktree add --detach $wt "origin/<source>"
```

### 5. Read the change

```powershell
git -C $wt log  --oneline "origin/<dest>..HEAD"      # the PR's commits
git -C $wt diff --stat    "origin/<dest>...HEAD"     # files + churn
git -C $wt diff           "origin/<dest>...HEAD"     # the diff
```

Use `...` so the comparison is against the **merge base** — two dots would also show everything that
landed on the destination since the PR forked, which isn't the author's work.

Then go beyond the diff, which is the whole point of having the tree: `Read` the changed files in
full where the diff is ambiguous, look at the callers of anything whose signature or contract moved,
and check whether the tests actually exercise the new behaviour rather than merely compiling against
it. Note what you verified in the tree versus what you're inferring — a review that guesses loses the
author's trust on the one finding that turns out wrong.

**Read the code; don't build it and don't run the tests.** CI already does that — Jenkins and
SonarQube run on the head commit and their verdict is on the PR page, which beats anything a local
run proves. Three more reasons it's the wrong trade:

- It costs tens of minutes on these repos, which defeats the point of the fast lane.
- **A Maven build in a linked worktree is broken anyway.** The worktree's `.git` is a file, not a
  directory, so `jgitver` and `git-commit-id` can't read it: the version degrades to
  `0.0.0-NO_WORKTREE_AND_INDEX` and dependency resolution fails. That looks exactly like a compile
  error in the PR, and reporting it as one is a phantom blocker on good code.
- **`mvn install` from a review checkout corrupts the user's `~/.m2`**, publishing those bogus
  versions into the shared local repo. The obvious workaround is worse: `-Djgitver.skip=true` falls
  back to `0.0.0-SNAPSHOT`, which already exists as a real artifact, so it silently overwrites the
  user's own jars.

Static reading answers almost every question that matters here — whether a null can reach a caller,
whether a test asserts the new behaviour, whether a contract moved. For the rest, mark the finding as
needing runtime confirmation and name what would confirm it. An honest "assumed" beats a slow guess
presented as proof.

### 6. Detect the stack and apply the right conventions

Look at the repo root and the changed paths: `pom.xml` / `build.gradle` → Java, `package.json` →
Node, `pyproject.toml` → Python. A repo can be polyglot.

For **Java / Spring**, invoke **`java-spring-best-practices`** for the stack-specific pass rather
than re-deriving its rules here — it already encodes the conventions this team reviews against, and a
second divergent copy is worse than no copy. Use its severity taxonomy either way:

- **blocker** — must fix before merge (security, data loss, silently broken tests)
- **issue** — should fix (bugs, performance, missing transactions, broken contracts)
- **suggestion** — recommend (readability, maintainability, design)
- **nitpick** — optional (style, polish)

Regardless of stack, check: correctness and edge cases in the new logic; error handling and what
happens on the unhappy path; whether new behaviour is tested; leftover debug output, `TODO`s or
commented-out blocks introduced by this branch; hardcoded secrets or URLs; migrations, new env vars
and breaking API changes that need calling out; and whether the diff is one coherent change rather
than a feature bundled with an unrelated refactor.

Be honest about severity in both directions. Inflating nitpicks into blockers trains the author to
ignore you; softening a real blocker into a suggestion is worse. A clean PR deserves a short report
that says so.

### 7. Report, with the comments spelled out

Write the report in the conversation, in the language the user is speaking. Anchor every finding to
`file:line` — a finding nobody can locate isn't actionable, and inline comments need the position.

```
## PR #<id> — <title>
<repo> · <author> · <state>          [⚠️ stacked on #<parent> — reviewing only the delta]

**Verdict: <✅ looks good / ⚠️ changes suggested / ❌ do not merge>**

<two sentences on what the PR actually does>

### Findings
- **[blocker]** `path/File.java:42` — <what's wrong and why it matters>
- **[issue]** `path/Other.java:17` — <…>
- **[nitpick]** `path/Third.java:88` — <…>

### Open questions
- **Scope vs <TICKET-KEY>** — <unmet AC, or scope the ticket doesn't mention, phrased as a question>
- <an unanswered question from the ticket's comments that this PR settles implicitly>

### Verified / assumed
- Verified: <what you actually checked in the tree>
- Assumed: <what you inferred and would want the author to confirm>

### Comments I'd post
1. inline · `path/File.java:42` — "<exact comment text>"
2. summary — "<exact comment text>"

### TL;DR
- **What it does:** <one sentence>
- **Blocking:** <the blockers, or "nothing">
- **Worth fixing:** <the issues>
- **Needs an answer:** <open questions for the author or the PM>
```

When a finding is about **data flow across a boundary** — a value arriving from two upstream systems
into one field, a surprising call ordering — a small annotated ASCII diagram explains it far faster
than a paragraph. Use one only for that kind of structural finding; a diagram of something already
clear from two lines of code just buries the parts worth reading.

Showing the exact text before posting is the point of this step: the user is the one whose name goes
on the comment, so they get to edit the wording, drop a finding, or decide a point is better said in
person.

### 8. Ask before posting anything

**Never post as a side effect of producing the review.** Ask explicitly:

```
Post to PR #<id>?
  a) summary comment only
  b) inline comments only
  c) both
  d) nothing
```

Offer to go finding-by-finding if the list is long, and accept edits to the wording. On approval,
invoke **`is:bitbucket`** (`post-comment --body-stdin`, `post-inline-comment --file <path>
--line <n>`) and report exactly what landed, including anything that failed. Write the comments in
the language the team uses on that repo — `list-comments` from step 1 shows it.

Don't approve, merge or decline. If the user wants that, `is:bitbucket` has `approve-pr`, `merge-pr`
and `decline-pr` — hand off explicitly rather than acting implicitly on their behalf.

### 9. Clean up the worktree

The worktree is throwaway here — remove it once the review is delivered, so `projects/reviews/`
doesn't fill up with stale trees:

```powershell
git -C $clone worktree remove $wt
git -C $clone worktree prune
```

Because step 5 rules out building, nothing writes into the worktree and plain `remove` succeeds —
no `--force` needed.

Keep it only if the user asks to look at something themselves. Confirm their branch and uncommitted
work are untouched. If removal fails on a file lock, give them the command to run later rather than
leaving an unexplained directory behind.
