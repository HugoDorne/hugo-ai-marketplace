---
name: explain
description: >
  Explain how code works — purpose, an ASCII flow/structure diagram, a step-by-step
  walkthrough, key design decisions, and gotchas. Use whenever the user wants to understand
  a file, class, method, or feature they didn't write or have forgotten: "how does this work",
  "walk me through this", "what does this do", "explain this code/function", or when onboarding
  to an unfamiliar part of a codebase.
disable-model-invocation: false
---

# Code Explainer

Explain the code specified in `$ARGUMENTS` (a file path, class name, method, or code snippet).

## Process

1. **Read the target code** thoroughly before explaining anything.
2. **Identify the scope**: is it a single method, a class, a module, or a full feature spanning multiple files? If it spans multiple files, read all relevant files.
3. **Understand the context**: what calls this code, what does it depend on, where does it fit in the architecture.

## Explanation structure

Follow this order:

### 1. Purpose (1-2 sentences)
What does this code do and why does it exist? State the business or technical goal.

### 2. Overview diagram
When appropriate, draw an ASCII diagram showing the flow, structure, or relationships. Pick the most appropriate type:

- **Sequence diagram** for request/response flows or method call chains
- **Component diagram** for class relationships and dependencies
- **Flowchart** for conditional logic or state transitions

```
Example:
  Client ──> Controller ──> Service ──> Repository ──> DB
                              |
                              v
                          Validator
```

### 3. Step-by-step walkthrough
Walk through the code in execution order. For each significant block:
- What it does
- Why it does it that way
- What data flows in and out

Use bullet points, not paragraphs. Reference line numbers when helpful.

### 4. Key design decisions
Highlight notable patterns, trade-offs, or non-obvious choices:
- Design patterns used (and why)
- Performance considerations
- Error handling strategy
- Framework-specific conventions

### 5. Gotchas and pitfalls
List things that could trip someone up:
- Non-obvious side effects
- Implicit assumptions or preconditions
- Common mistakes when modifying this code
- Thread safety or concurrency concerns

Skip this section if there are no notable gotchas.

## Rules

- **Be concise** — explain what matters, skip the obvious. Don't narrate syntax (`this is a for loop`).
- **Use the right level of detail** — adapt to the complexity of the code. A simple utility gets a short explanation; a complex algorithm gets a detailed one.
- **Use code references** — quote small snippets inline when referencing specific parts.
- **Assume the reader knows the language** — don't explain basic language constructs unless they're used in an unusual way.
- **Highlight the "why"** — the code already shows the "what"; focus on intent and reasoning.
