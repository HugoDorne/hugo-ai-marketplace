# CLAUDE.md — hugo-ai-marketplace

Personal Claude Code marketplace. Each subfolder of `plugins/` is an independently versioned plugin.

## Authoring language

All authored content — plugin manifests, skill instructions, and docs — is written in **English**. A skill's *runtime output* may still be localized when that's its purpose (e.g. `pr-ready` answers in the conversation's language). Every skill `description` should carry **both English and French trigger phrases** so it fires regardless of the language the user speaks.

## Versioning rule — apply at the end of a session

If the session changed a plugin (adding/removing/editing a skill, a hook, commands, or its manifest), **bump that plugin's version before wrapping up**. An untouched plugin doesn't move. One bump covers the whole session's changes to a plugin — don't bump twice for the same session.

The version lives in **two files that must stay in sync**:

1. `plugins/<plugin>/.claude-plugin/plugin.json` → `version` field
2. `.claude-plugin/marketplace.json` → the matching entry in `plugins[].version`

Both must carry the same value after the bump.

## SemVer

- **MAJOR** (`X.0.0`): rewrite or genuinely breaking behavior change (rare on this personal marketplace).
- **MINOR** (`x.Y.0`): adding **or** removing a skill/command, or a new capability.
- **PATCH** (`x.y.Z`): fix, rewording, internal adjustment with no interface change.

The `metadata.version` in `marketplace.json` (the marketplace-wide version) is only bumped for a structural change to the marketplace itself (adding/removing a plugin, a rewrite), not on every plugin edit.

## Coherence

- Keep the plugin's `description` and `keywords` up to date in `marketplace.json` when the plugin's scope changes (e.g. a removed skill must no longer appear in the description or keywords).
