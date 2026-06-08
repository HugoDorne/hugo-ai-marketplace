# Hugo's Claude Marketplace

Personal Claude Code plugin marketplace: Java/Spring Boot development tooling, code-quality
utilities, and productivity helpers.

## Plugins

### code

Code understanding, quality, dependency, and Java/Spring documentation & testing tools:

- **`/explain`** — Explain how code works: purpose, flow diagram, step-by-step walkthrough, design decisions, and gotchas
- **`/sonar`** — Scan for SonarQube/static-analysis/IDE issues and code smells, list them by severity, and fix the ones you pick
- **`/check-updates`** — Check Maven (`pom.xml`) and npm (`package.json`) dependencies for newer versions, grouped by risk, and apply only the upgrades you approve
- **`/doc`** — Generate Javadoc, OpenAPI/Swagger annotations, ADRs, or README sections
- **`/java-spring-best-practices`** — Review or write Java/Spring Boot code against best practices (security, SOLID, Spring patterns, conventions, tests, SQL migrations)
- **`/java-unit-test`** — Generate JUnit 5 unit tests with AssertJ, `@Nested` classes, Mockito, and behavioral naming

### productivity

- **`/smart-compact`** — Summarize the session into a structured handoff, then trigger `/compact` with that summary so the right context survives compaction

## Installation

```bash
# Add the marketplace
/plugin marketplace add HugoDorne/claude-marketplace

# Install plugins
/plugin install code@hugo-marketplace
/plugin install productivity@hugo-marketplace
```

## Local testing

```bash
# Add from local directory
/plugin marketplace add <path_to_marketplace>

# Install and test
/plugin install code@hugo-marketplace
```
