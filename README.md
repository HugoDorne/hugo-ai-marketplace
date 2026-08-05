# Hugo's Claude Marketplace

Personal Claude Code plugin marketplace: Java/Spring Boot development tooling, code-quality
utilities, and productivity helpers.

## Plugins

### toolbox

A single dev & productivity plugin bundling all skills:

- **`/explain`** — Explain how code works: purpose, flow diagram, step-by-step walkthrough, design decisions, and gotchas
- **`/version-check`** — Check Maven (`pom.xml`) and npm (`package.json`) dependencies for newer versions, grouped by risk, and apply only the upgrades you approve
- **`/doc`** — Generate Javadoc, OpenAPI/Swagger annotations, ADRs, or README sections
- **`/java-spring-best-practices`** — Review or write Java/Spring Boot code against best practices (security, SOLID, Spring patterns, conventions, tests, SQL migrations)
- **`/java-unit-test`** — Generate JUnit 5 unit tests with AssertJ, `@Nested` classes, Mockito, and behavioral naming
- **`/smart-compact`** — Summarize the session into a structured handoff, then trigger `/compact` with that summary so the right context survives compaction
- **`/pr-description`** — Generate a PR title and description in English from the current working-tree diff, and copy the raw Markdown to the clipboard
- **`/pr-ready`** — Pre-PR readiness check (clean tree, changelog, tests, code quality, coherent diff) returning a Pass/Fail checklist with a verdict
- **`/pr-hitl`** — Review a Bitbucket PR from its URL *with you in the loop*: checks it out in a throwaway git worktree, opens a new IntelliJ window, and walks you through the change theme by theme so you retain it. Asks before posting anything
- **`/pr-review`** — Review a Bitbucket PR from its URL autonomously: same worktree checkout for full file context, findings ranked by severity with the exact comments spelled out, and nothing posted without your approval

## Installation

```bash
# Add the marketplace
/plugin marketplace add HugoDorne/claude-marketplace

# Install the plugin
/plugin install toolbox@hugo-marketplace
```

## Local testing

```bash
# Add from local directory
/plugin marketplace add <path_to_marketplace>

# Install and test
/plugin install toolbox@hugo-marketplace
```
