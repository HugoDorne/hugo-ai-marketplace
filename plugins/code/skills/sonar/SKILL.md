---
name: sonar
description: >
  Scan code for quality issues — SonarQube/SonarLint findings, static-analysis and IDE
  markers, common code smells, and TODO/FIXME/suppressed-warning markers — then list them by
  severity and fix the ones the user picks. Use when the user wants to find or clean up code
  smells, lint or static-analysis warnings, technical debt, or "issues/problems in" a file,
  class, or module — even when they don't name SonarQube specifically.
disable-model-invocation: false
---

# Code Issue Scanner & Fixer

Scan the code specified in `$ARGUMENTS` (a file, directory, module, or class) for quality issues and let the user pick which ones to fix.

## Step 1: Collect issues

Run the following checks in parallel where possible:

### SonarQube / SonarLint
- Look for `.scannerwork/report-task.txt` or `sonar-project.properties` to identify SonarQube configuration.
- Run `sonar-scanner` if available, or check for existing SonarQube report files.
- If SonarQube is not configured, skip and note it.

### IDE / Static analysis markers
- Search the target files for suppressed warnings and known issue markers:
  - `@SuppressWarnings` annotations
  - `// TODO`, `// FIXME`, `// HACK`, `// XXX` comments
  - `//noinspection` (IntelliJ suppression comments)
  - `@Deprecated` without replacement documentation
- Search for common Java code smells:
  - Empty catch blocks
  - Raw types (missing generics)
  - Unused imports
  - Unused private methods or fields
  - `System.out.println` / `System.err.println` instead of logger
  - String concatenation in loops (should use `StringBuilder`)
  - `== null` chains that could use `Optional`
  - Magic numbers / hardcoded strings that should be constants
  - Methods with too many parameters (> 4)
  - Classes with too many lines (> 300)
  - Overly broad exception catches (`catch (Exception e)`)
  - Missing `@Override` annotations
  - Mutable fields that could be `final`

### Compiler warnings
- If a `pom.xml` or `build.gradle` is present, check for compiler warning flags and known issues.

## Step 2: Classify and present

Group all found issues into categories with severity:

| Severity | Meaning |
|----------|---------|
| **Critical** | Bugs, security vulnerabilities, empty catch blocks hiding errors |
| **Major** | Code smells that hurt maintainability or readability significantly |
| **Minor** | Style issues, missing annotations, naming conventions |
| **Info** | TODOs, FIXMEs, suggestions for improvement |

Present the issues as a numbered todo list, grouped by file, with severity and a one-line description for each:

```
## FileA.java
1. [Critical] Empty catch block silently swallows IOException (line 42)
2. [Major] Raw type usage: List instead of List<String> (line 67)
3. [Minor] Missing @Override on equals() (line 89)

## FileB.java
4. [Major] System.out.println used instead of logger (lines 12, 34, 56)
5. [Info] TODO: refactor this method (line 23)
```

## Step 3: Ask the user

After presenting the list, ask the user which issues they want to fix. Offer these choices:
- Fix all
- Fix by severity (e.g., all Critical + Major)
- Pick specific issue numbers
- Skip

## Step 4: Fix selected issues

For each issue the user selects:
1. Read the relevant code around the issue.
2. Apply the fix following existing code conventions (formatting, naming, patterns).
3. Keep changes minimal — fix only the issue, don't refactor surrounding code.
4. For TODOs/FIXMEs: ask the user whether to resolve them or just leave them.

## Rules

- **Never auto-fix without user approval** — always present the list first and wait for selection.
- **Preserve existing code style** — match the formatting and conventions of the file.
- **One concern at a time** — each fix should be isolated and reviewable independently.
- **Don't introduce new issues** — if a fix requires touching unrelated code, flag it instead of changing it.
- **Be honest about limitations** — if an issue requires more context or a design decision, say so instead of guessing.
