---
name: brag
description: Keep the user's brag book up to date — short, dated, sourced entries about what they achieved and the work facts worth remembering, written to a Notion section (or a local inbox file when Notion is unreachable) for annual reviews, interviews and memory. Works three ways — capture what was just done in the current session, document a given scope (ticket key, repo, topic, period) from a fresh session, or backfill undocumented facts by mining git commits, past Claude Code sessions, Jira tickets, Bitbucket PRs and Confluence pages — and can read the book back to prepare a review. Use whenever the user types /brag, says "brag", "add this to my brag book", "note this win", "keep track of what I did", "what did I accomplish this month", "prepare my annual review", or wraps up meaningful work they want remembered. French triggers - "ajoute ça à mon brag book", "brag ça", "note cette réussite", "garde une trace de ce que j'ai fait", "documente ce que j'ai fait sur IS-1234", "rattrape mon brag book", "qu'est-ce que j'ai accompli ce mois-ci", "prépare mon entretien annuel".
---

# Brag — keep the brag book current

A brag book is a running record of what the user achieved and of the facts worth remembering, written while they are fresh. Its reader is the user months later, in an annual review or a job interview, where any line can be challenged and there is no time to read paragraphs. So every entry must be **short, concrete, dated, sourced and true**: an inflated or unverifiable claim costs more credibility than it earns. Draft from evidence, never from imagination, and write nothing before the user approves.

## 1. Load the configuration

Read `~/.claude/brag/config.md`. Everything personal lives there so the skill stays generic:

| Key | Meaning |
|---|---|
| Notion page | URL of the page holding the brag book — the `page_id` for every edit |
| Brag book block | ID of the heading entries go under (stable even if the heading moves) |
| Notion workspace | workspace name, to pick the right connector when several are connected |
| Entry language | language entries are written in |
| Job scope | what counts; sessions and repos outside it are ignored |
| Git authors, Git roots | emails and folders for the commit scan |
| Atlassian site | Jira and Confluence site, used as `cloudId` |
| Bitbucket workspace, Bitbucket user | for PR lookups |
| Bitbucket fallback | optional command that calls the Bitbucket REST API when the connector fails |
| Last backfill | end date of the last written backfill, or `never` |

If the file is missing, ask the user for these values (propose defaults from `git config user.email` and the connected Notion workspaces) and create it. The fallback inbox sits next to it: `~/.claude/brag/inbox.md`. Both live outside any session folder, so deleting a session never deletes them.

## 2. Check the destination

Notion is the target; the inbox is the fallback, so a fact is never lost because a connector is down.

1. Find the Notion connectors: tools ending in `notion-fetch` (load deferred ones with ToolSearch). With several, call each one's `notion-get-self` and keep the one whose workspace matches the config.
2. Fetch the configured **Notion page**. Success → **Notion mode**. Read the existing entries from this page, not from a fetch of the block: a block fetch can return a stale snapshot, and its ancestor path lists toggle blocks that are not pages. If the brag book heading is not on the page, fetch the block ID to see where it moved.
3. Any failure (no connector, auth required, not found, no access) → **inbox mode**. Tell the user in one line why, and that entries go to `~/.claude/brag/inbox.md` until a later run reaches Notion.

When the inbox holds entries and Notion is reachable, add them to this run's proposal. They go through the same duplicate and objective checks (step 5) as new drafts, since the inbox could not check against Notion.

## 3. Pick the mode

| The user… | Mode | Evidence |
|---|---|---|
| runs `/brag` after real work in this session | **Capture** | this conversation, plus the commits and PRs it produced |
| states a fact (`/brag j'ai animé ma première rétro…`) | **Fact** | their words only; search a source only for a reference they name (ticket, PR, page) |
| names a scope: ticket key, repo, topic, period (`/brag FEAT-455`, `/brag live-map`, `/brag septembre`) | **Scope** | every source, filtered to that scope |
| asks to catch up (`/brag backfill`, "rattrape"), or runs a bare `/brag` in a session with no prior work | **Backfill** | every source from the period they give, else since `Last backfill`; if `never`, ask how far back |
| asks what they achieved, or to prepare a review | **Recall** | the brag book itself |

Dates the user types follow the entry language's convention (French `10/07` = 10 July); one without a year is its most recent occurrence before today. A fact with no trace anywhere gets `Sources : déclaratif` (or the entry language's equivalent).

**Recall** writes nothing: read the entries (Notion and inbox), answer grouped by objective or category with entry dates, and if `Last backfill` is over a month old, offer a backfill first. The other modes continue below.

## 4. Collect evidence

Use what the mode needs. A source that is unavailable is skipped and named in the final report — it never blocks the run. Absence of evidence is not evidence of absence: transcripts of deleted sessions are gone, so "no session found" means "no data", not "it didn't happen".

- **Sessions** — `python <skill-dir>/scripts/collect.py sessions --since YYYY-MM-DD [--until YYYY-MM-DD] [--grep TEXT]` prints one block per past Claude Code session: title, cwd, the user's prompts, wrap-up recaps, PRs opened, last reply. With `--grep`, each block says `match: direct` (the user or a recap named it) or `match: tool output only` (it merely appeared in a git log or ticket list) — read the direct ones first. To get the numbers and decisions a digest clips, rerun with `--id <session-id>`: every prompt with its final reply. Drop sessions outside the job scope.
- **Commits** — `python <skill-dir>/scripts/collect.py commits [--since YYYY-MM-DD] --author EMAIL --root DIR [--grep REGEX]` (repeat `--author`/`--root` as needed) prints the user's commits per repo by author date, de-duplicated, with the origin remote. For a ticket or topic scope, `--grep` alone is enough. Commits made on a worktree branch that was deleted after a squash merge can be missing; the sessions usually name them.
- **Jira** — the Atlassian connector's `searchJiraIssuesUsingJql` with `fields: ["summary", "status", "parent", "resolutiondate"]` (without it, a week of tickets weighs 100 KB+): `status changed BY currentUser() AFTER "<since>" OR (reporter = currentUser() AND created >= "<since>") OR (assignee = currentUser() AND resolved >= "<since>")`. Assignment alone misses most of the work: tickets are often assigned to a PM or a teammate. For one ticket, `getJiraIssue` with `fields: ["summary", "description", "status", "parent", "resolutiondate"]` and `fieldsByKeys: true` — the `evidence` view drags in every worklog. The ticket and its parent give the *why* that commits never carry.
- **Bitbucket PRs** — for each repo with commits in range whose remote is on bitbucket.org, `getPullRequests` (state `MERGED`, `pagelen` 50); keep those authored by the configured user and updated in range. If the connector fails, use the configured fallback on `/2.0/repositories/<workspace>/<repo>/pullrequests?q=updated_on>="<since>"&state=MERGED&state=OPEN` and filter the author yourself. With neither, rely on the PR numbers in sessions and in squash-merge commit subjects (`… (pull request #N)`).
- **Confluence** — `searchConfluence` with `contributor = currentUser() AND type = page AND lastmodified >= "<since>"`: retros, sprint reviews, design notes and meeting notes. This is where facilitation and Scrum Master work leaves its trace, which code never shows. `lastmodified` is the page's last edit by anyone: check that the user's own edit (author, version history) falls in range before crediting it.

`<skill-dir>` is this skill's base directory. For a backfill over more than about a month, go month by month, or give each source to a subagent that returns candidate facts, so raw digests don't flood the context.

## 5. Turn evidence into facts

Commits and sessions are raw material, not entries. Group them into **accomplishments**: a feature shipped, a migration done, an incident resolved, a process improved, a review that changed the outcome. A ticket with twenty commits is one entry; three unrelated config tweaks are probably none.

Worth an entry:
- delivered something users or the team rely on;
- removed risk, cost or toil (upgrade, CI speed-up, log noise cut, automation);
- solved a hard problem or an incident — root cause, not just the symptom;
- leadership and collaboration: facilitation, Scrum Master duties, unblocking others, mentoring, a review that caught real bugs;
- feedback received, a decision taken, something learnt — facts the user will want to remember.

Not worth one: routine merges and branch syncs, typo fixes, reviews with no finding, work the user only watched.

Rules that keep the book credible and usable:
- **Short.** The entry is a prompt to talk from, not the story: the details live behind its sources. The title carries the outcome and its key number; each line is one or two short sentences, about 30 words at most. If a line needs more, it is two entries or the detail belongs in the sources.
- **Date** = when it was delivered (merge, release, resolution, end of the session), not today.
- **Delivered or not.** Significant work still in a draft or open PR is not an entry yet: list it under "à documenter à la livraison". Draft it only when the user asks for it (a scope naming that work counts), with `[en cours]` at the start of the title, dated at its last milestone, to be updated at delivery.
- **Numbers only from evidence** (counts, durations, before/after). When impact is unknown, state what is factual, write "à compléter" (or the entry language's equivalent), and ask — never estimate.
- **The user's own part.** Team work is fine; say what *they* did, and flag work merged under someone else's name for the user to confirm.
- **Objective.** If the page states objectives (a "Success" or "Objectifs" section), tag the entry with the one it advances — it is what a reviewer asks about.
- **Duplicates.** Compare with existing entries and the inbox by source references (ticket keys, PR numbers, commit hashes) and topic. Already covered → drop it. New progress on a covered topic → propose updating that entry instead of adding one.

## 6. Validate with the user

Show the drafts as a numbered list in the entry language — exactly as they would be written — with each draft's open questions underneath (missing impact, unclear ownership). After them, one line each for what you dropped or deferred, so the user can override. Ask which to keep, change or drop, and stop there until the user answers: a misread transcript written down as a "win" is worse than no entry. Show at most about ten drafts at a time in a big backfill. Apply their edits, then write.

## 7. Write

**Notion mode.** Entries sit right under the brag book heading, newest first, one toggle each. Use `notion-update-page` on the configured page with `update_content`, one `content_updates` item per entry:
- first entries ever: a single item replacing the heading plus its placeholder line (e.g. `### Brag book\n\nA remplir`) with the heading followed by all the entries;
- newest entry: `old_str` = the heading line, `new_str` = heading + the entry;
- in between: `old_str` = `<toggle>` + the title line of the entry the new one must precede; `new_str` = the new entry, a blank line, then that same `old_str`;
- oldest entry: `old_str` = the last entry's final line plus its `</toggle>`; append after it;
- updating an entry: replace only the lines that change.

Notion normalizes what you write — `**x**` comes back as `<b>x</b>`, backticks as `<code>`, `_` as `\_` — so copy every `old_str` from a fresh fetch, never from what you wrote. An item that returns a `no_match` warning was not applied (the others were): re-fetch and retry it. Remove pushed entries from the inbox once Notion has them.

**Inbox mode.** Append the entries, in the same toggle format, to `~/.claude/brag/inbox.md` (create it with a `# Brag inbox — pending Notion` heading).

After a backfill is written, in either mode, set `Last backfill` in the config to the end of the scanned period.

Finish with a short report: what was written and where (Notion page link or inbox path), sources skipped and why, and the "à compléter" items left.

## Entry format

````
<toggle>
{emoji} {YYYY-MM-DD} — {outcome with its key number}

- **Contexte** : {why it mattered — one sentence}
- **Action** : {what the user did — one or two sentences}
- **Résultat** : {measurable or observable outcome}
- **Compétences** : {3–5 skills shown}
- **Objectif** : {objective from the page, when one applies}
- **Sources** : {ticket links · PR links · `hash` (repo) · session title}
</toggle>
````

Labels follow the entry language (English: Context / Action / Result / Skills / Objective / Sources). Category emoji: 🚀 delivery · 🛠️ quality & tech debt · ⚙️ automation & process · 🔥 incident & debugging · 🤝 leadership & collaboration · 💬 feedback received · 📚 learning. Link tickets as `https://<atlassian-site>/browse/<KEY>` and PRs by their Bitbucket URL.

Illustrative example:

````
<toggle>
🛠️ 2026-03-12 — Service de paiement : logs divisés par 600 grâce à des compteurs

- **Contexte** : 200k lignes INFO par quart d'heure noyaient les vraies erreurs dans Kibana.
- **Action** : état des lieux des loggers ; messages répétitifs passés en DEBUG et remplacés par un compteur publié chaque minute.
- **Résultat** : ~300 lignes par quart d'heure en prod ; erreurs de nouveau visibles dans le dashboard d'astreinte.
- **Compétences** : observabilité, Spring Boot, analyse de logs
- **Objectif** : Maintenabilité des composants
- **Sources** : [PAY-412](https://example.atlassian.net/browse/PAY-412) · [PR #318](https://bitbucket.org/acme/payment/pull-requests/318) · `a1b2c3d` (payment-service)
</toggle>
````
