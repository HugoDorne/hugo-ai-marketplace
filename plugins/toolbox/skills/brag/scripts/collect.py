#!/usr/bin/env python3
"""Evidence collector for the /brag skill: compact Markdown digests of Claude Code sessions and git commits.

Exists so the model reads a few KB of digest instead of multi-MB raw transcripts or dozens of `git log` calls.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Prompts that are harness plumbing, not something the user said.
NOISE_PREFIXES = ("<system-reminder", "<local-command", "<task-notification", "<side-sessions-event",
                  "<ci-monitor-event", "<command-message", "Caveat:", "[Request interrupted")
SKIP_DIRS = {".claude", "node_modules", "target", "build", "dist", ".idea", ".gradle", "venv", ".venv"}


def clip(text, limit):
    """Collapse whitespace and cut ``text`` to ``limit`` chars, marking the cut with an ellipsis."""
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def prompt_text(record):
    """Return what the user typed in a ``user`` record, or None for tool results and harness noise."""
    if record.get("isMeta"):
        return None
    content = record.get("message", {}).get("content")
    if isinstance(content, list):
        content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    if not content or not content.strip():
        return None
    name = re.search(r"<command-name>(.*?)</command-name>", content, re.S)
    if name:
        args = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
        return f"{name.group(1).strip()} {args.group(1).strip() if args else ''}".strip()
    return None if content.lstrip().startswith(NOISE_PREFIXES) else content


def digest_session(path, grep):
    """Parse one transcript into a summary dict; None when ``grep`` is set and the file never mentions it."""
    s = {"id": path.stem, "first": None, "last": None, "cwd": None, "branch": None, "title": None,
         "prompts": [], "turns": [], "recaps": [], "prs": [], "last_reply": None}
    matched = grep is None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not matched and grep in line.lower():
                matched = True
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("type") == "custom-title":
                s["title"] = r.get("customTitle")
            if r.get("isSidechain"):
                continue
            ts = r.get("timestamp")
            if ts and r.get("type") in ("user", "assistant"):
                s["first"] = s["first"] or ts
                s["last"] = ts
            s["cwd"] = s["cwd"] or r.get("cwd")
            s["branch"] = r.get("gitBranch") or s["branch"]
            if r.get("type") == "user":
                p = prompt_text(r)
                if p:
                    s["prompts"].append(p)
                    s["turns"].append([p, None])
            elif r.get("type") == "assistant":
                for b in r.get("message", {}).get("content", []):
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        s["last_reply"] = b["text"]
                        if s["turns"]:
                            s["turns"][-1][1] = b["text"]
                    elif b.get("type") == "tool_use":
                        name, inp = b.get("name", ""), b.get("input") or {}
                        if name.endswith("wrap_up") and inp.get("recap"):
                            s["recaps"].append(inp["recap"])
                        elif "createPullRequest" in name or "createDraftPullRequest" in name:
                            s["prs"].append(inp.get("title", "?"))
    if not (matched and s["first"]):
        return None
    # "direct" = the user or a recap named it; otherwise it only shows up in tool output (a git log, a ticket list).
    said = [s["title"] or ""] + s["prompts"] + s["recaps"]
    s["direct"] = grep is None or any(grep in t.lower() for t in said)
    return s


def print_session(s, a, detail):
    """Print one session as Markdown; ``detail`` adds every turn's final reply instead of the last one only."""
    limit = a.max_chars or (2000 if detail else 300)
    print(f"## {s['first'][:10]} → {s['last'][:10]} · {s['title'] or clip(s['prompts'][0] if s['prompts'] else '(untitled)', 80)}")
    print(f"- session `{s['id']}` · cwd `{s['cwd']}` · branch `{s['branch']}`")
    if s.get("copies"):
        print(f"- forks/copies skipped: {', '.join(s['copies'])}")
    if a.grep:
        print(f"- match: {'direct' if s['direct'] else 'tool output only'}")
    if s["recaps"]:
        print("- recaps:")
        for rc in s["recaps"] if detail else s["recaps"][-6:]:
            print(f"  - {clip(rc, limit)}")
    if s["prs"]:
        print(f"- PRs opened: {'; '.join(clip(t, 120) for t in s['prs'])}")
    if detail:
        for p, reply in s["turns"]:
            print(f"\n### > {clip(p, limit)}\n\n{clip(reply or '(no reply)', limit)}")
    else:
        prompts = s["prompts"][: a.max_prompts]
        if prompts:
            print("- prompts:")
            for p in prompts:
                print(f"  - {clip(p, limit)}")
            if len(s["prompts"]) > a.max_prompts:
                print(f"  - (+{len(s['prompts']) - a.max_prompts} more)")
        if s["last_reply"]:
            print(f"- last reply: {clip(s['last_reply'], limit * 2)}")
    print()


def cmd_sessions(a):
    """Print one Markdown block per main-thread session active in [since, until], or one session in full with --id."""
    grep = a.grep.lower() if a.grep else None
    since_ts = datetime.fromisoformat(a.since).timestamp() if a.since and not a.id else 0
    root = Path(a.root).expanduser().resolve()
    if os.name == "nt":  # project folder names are long enough to exceed MAX_PATH
        root = Path("\\\\?\\" + str(root))
    out = []
    for path in root.glob(f"*/{a.id or '*'}.jsonl"):
        if path.stat().st_mtime < since_ts:  # untouched since `since`: cannot hold activity in range
            continue
        s = digest_session(path, grep)
        if not s:
            continue
        if not a.id:
            if (a.since and s["last"][:10] < a.since) or (a.until and s["first"][:10] > a.until):
                continue
            # A session opened by /brag holds brag drafts, not new evidence.
            if s["prompts"] and re.match(r"/?[\w:-]*brag\b", s["prompts"][0]):
                continue
        out.append(s)
    # Forked or resumed sessions repeat their parent's transcript under the same title: keep the fullest copy.
    by_title = {}
    for s in out:
        key = s["title"] or s["id"]
        best = by_title.get(key)
        if best is None or len(s["turns"]) > len(best["turns"]):
            s["copies"] = (best["copies"] + [best["id"]]) if best else []
            by_title[key] = s
        else:
            best["copies"].append(s["id"])
    out = sorted(by_title.values(), key=lambda s: s["last"])
    for s in out:
        print_session(s, a, detail=bool(a.id))
    print(f"<!-- {len(out)} session(s) -->")


def find_repos(root, depth):
    """Yield git repositories under ``root`` (``.git`` directories only, so linked worktrees are skipped)."""
    root = Path(root).expanduser()
    base = len(root.parts)
    for dirpath, dirnames, _ in os.walk(root):
        if ".git" in dirnames:
            yield Path(dirpath)
            dirnames[:] = []  # a repo's own subfolders hold no other repo worth scanning
            continue
        dirnames[:] = [] if len(Path(dirpath).parts) - base >= depth else [d for d in dirnames if d not in SKIP_DIRS]


def cmd_commits(a):
    """Print the author's non-merge commits per repository, de-duplicated by subject (rebases, cherry-picks)."""
    total = 0
    for root in a.root:
        for repo in sorted(find_repos(root, a.depth)):
            # --reflog keeps commits whose branch was deleted after a squash merge.
            cmd = ["git", "-C", str(repo), "log", "--all", "--reflog", "--no-merges", "--date=short",
                   "--format=%ad%x1f%h%x1f%s"]
            if a.since:  # git filters on committer date, which is never before the author date: a safe pre-filter
                cmd.append(f"--since={a.since}")
            cmd += [f"--author={e}" for e in a.author]
            if a.grep:
                cmd += [f"--grep={a.grep}", "--regexp-ignore-case"]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            seen, rows = set(), []
            for line in res.stdout.splitlines():
                d, h, subject = line.split("\x1f", 2)
                # Author date = when the work was done; a rebase or a squash merge only moves the committer date.
                if (a.since and d < a.since) or (a.until and d > a.until):
                    continue
                if subject not in seen:
                    seen.add(subject)
                    rows.append((d, h, subject))
            if not rows:
                continue
            remote = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"],
                                    capture_output=True, text=True).stdout.strip()
            print(f"## {repo.name} — {len(rows)} commit(s)\n- path `{repo}` · remote `{remote or 'none'}`")
            for d, h, subject in sorted(rows):
                print(f"- {d} `{h}` {subject}")
            print()
            total += len(rows)
    print(f"<!-- {total} commit(s) -->")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 and mangle accents
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sessions", help="digest Claude Code transcripts")
    s.add_argument("--since", help="YYYY-MM-DD, inclusive")
    s.add_argument("--until", help="YYYY-MM-DD, inclusive")
    s.add_argument("--grep", help="keep only sessions whose transcript contains this text (case-insensitive)")
    s.add_argument("--root", default="~/.claude/projects")
    s.add_argument("--id", help="print this one session in full: every prompt with its final reply")
    s.add_argument("--max-chars", type=int, help="clip length per item (default 300, 2000 with --id)")
    s.add_argument("--max-prompts", type=int, default=8)
    s.set_defaults(func=cmd_sessions)

    c = sub.add_parser("commits", help="list the author's commits across local repositories")
    c.add_argument("--since", help="YYYY-MM-DD, inclusive (author date); omit for a --grep scope")
    c.add_argument("--until", help="YYYY-MM-DD, inclusive (author date)")
    c.add_argument("--author", action="append", required=True, help="author email; repeatable")
    c.add_argument("--root", action="append", required=True, help="folder holding repositories; repeatable")
    c.add_argument("--grep", help="keep only commits whose message matches (case-insensitive regex)")
    c.add_argument("--depth", type=int, default=4, help="max folder depth below each root")
    c.set_defaults(func=cmd_commits)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
