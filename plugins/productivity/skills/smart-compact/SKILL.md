---
name: smart-compact
description: >
  Compact the conversation context while preserving what matters most. Use this skill
  whenever the user runs /smart-compact or asks to "compact", "summarize and compact",
  or "clean up the context". It generates a structured summary of the session — what
  was worked on, what changed, decisions made, and what's still pending — then triggers
  /compact with that summary as the guiding prompt so the compacted context retains
  the right information for the next session.
disable-model-invocation: false
---

# Smart Compact

Analyze the current conversation, write a structured handoff summary, display it to
the user, and then trigger `/compact` with that summary as the compaction prompt.

## Summary structure

Build the summary using this template (omit sections that are empty):

```
## Session summary

### Context
<One or two sentences: the project, feature branch, or ticket being worked on.>

### Accomplished
<Bullet list of concrete things completed: files changed, bugs fixed, features added,
decisions made. Be specific — include file paths, class names, and the nature of the
change.>

### Key decisions
<Bullet list of non-obvious choices made and the reason behind each. Skip obvious things.>

### Current state
<One sentence: where things stand right now (e.g. "Tests pass, ready to commit" or
"Mid-implementation of X, stopping at Y").>

### Next steps
<Bullet list of what remains, in order of priority. Include blockers if any.>
```

## How to write a good summary

- Be specific: "Added `UniverseNextDepartureMapper` in `mapper/` to convert BO to API
  response" is better than "Updated a mapper".
- Capture the *why* of decisions: "Chose polling over WebSocket because the mobile
  client doesn't support long-lived connections" is future-gold.
- Keep it tight — the goal is to give the next session enough context to pick up
  without re-reading everything.

## Execution

1. Read through the full conversation to extract the relevant facts.
2. Write the summary using the template above.
3. Display it clearly to the user under a `## Conversation Summary` heading.
4. Immediately after displaying, invoke `/compact` passing the summary text as the
   compaction prompt so it guides what the compactor preserves.

The summary should be the *last thing* you show the user before `/compact` runs —
this way they can see what was captured before the context is trimmed.
