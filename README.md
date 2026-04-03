# Hugo's Claude Marketplace

Personal Claude Code plugin marketplace with Java/Spring Boot development tools and code quality utilities.

## Plugins

### java-toolbox

Java/Spring Boot development skills:

- **`/doc`** — Generate Javadoc, OpenAPI/Swagger annotations, or ADR documentation
- **`/java-spring-best-practices`** — Review code against Java/Spring Boot best practices (security, SOLID, conventions)
- **`/java-unit-test`** — Generate JUnit 5 unit tests with AssertJ, @Nested classes, and behavioral naming

### code-quality

Code quality tools and formatting hooks:

- **`/explain`** — Explain code with structure, diagrams, and step-by-step walkthroughs
- **`/sonar`** — Scan for SonarQube/IDE code issues, list them, and fix selected ones
- **Hooks** — Auto-format files with `.editorconfig` rules on Write/Edit operations

## Installation

```bash
# Add the marketplace
/plugin marketplace add HugoDorne/claude-marketplace

# Install plugins
/plugin install java-toolbox@hugo-marketplace
/plugin install code-quality@hugo-marketplace
```

## Local testing

```bash
# Add from local directory
/plugin marketplace add <path_to_marketplace>

# Install and test
/plugin install java-toolbox@hugo-marketplace
```
