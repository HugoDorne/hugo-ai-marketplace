---
name: doc
description: Generate Javadoc, OpenAPI/Swagger annotations, or ADR documentation for existing Java code
disable-model-invocation: false
---

# Documentation Generator

Generate documentation for the code specified in `$ARGUMENTS` (a file, class, package, or method).

## Step 1: Analyze the target

1. Read the target code thoroughly.
2. Identify what type of code it is: controller, service, repository, entity, DTO, configuration, utility, etc.
3. Determine which documentation types are relevant.

## Step 2: Ask the user what to generate

Present the applicable documentation options and ask the user to pick one or more:

- **Javadoc** — Add `/** */` documentation to classes, methods, and fields
- **OpenAPI / Swagger** — Add `@Operation`, `@ApiResponse`, `@Schema`, `@Tag` annotations (for controllers and DTOs)
- **ADR** — Write an Architecture Decision Record for a design choice visible in the code
- **README section** — Generate a markdown section explaining the module/package purpose and usage

## Javadoc rules

When generating Javadoc:

- **Classes**: describe responsibility, when to use, and thread safety if relevant.
- **Public methods**: describe what it does, not how. Document parameters, return value, and thrown exceptions.
- **Skip the obvious** — don't add Javadoc to simple getters/setters, `toString`, `equals`, `hashCode`, or self-explanatory one-liner methods.
- **Use `@param`** for each parameter with a meaningful description (not just repeating the name).
- **Use `@return`** with what the value represents, not just the type.
- **Use `@throws`** for each checked and notable unchecked exception with the condition that triggers it.
- **Use `{@link ClassName#method}`** to reference related code.
- **Use `{@code value}`** for inline code references.
- **No filler** — never write "This method does X" or "This class is a class that...". Start directly with the verb.

Example:

```java
/**
 * Finds a user by their unique identifier.
 *
 * @param id the user's unique identifier, must not be {@code null}
 * @return the matching user
 * @throws UserNotFoundException if no user exists with the given id
 * @see UserRepository#findById(Long)
 */
public User findById(Long id) { ... }
```

## OpenAPI / Swagger rules

When generating OpenAPI annotations:

- **`@Tag`** on the controller class to group endpoints.
- **`@Operation`** on each endpoint with `summary` (short) and `description` (detailed, optional).
- **`@ApiResponse`** for each possible HTTP status code (200, 201, 400, 404, 500, etc.) with `description` and `content` schema.
- **`@Parameter`** for path variables and query params with `description`, `required`, and `example`.
- **`@Schema`** on DTO fields with `description`, `example`, and `requiredMode` where relevant.
- Use realistic `example` values, not placeholders like "string" or "0".

Example:

```java
@Tag(name = "Users", description = "User management operations")
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Operation(summary = "Get user by ID")
    @ApiResponse(responseCode = "200", description = "User found",
        content = @Content(schema = @Schema(implementation = UserResponse.class)))
    @ApiResponse(responseCode = "404", description = "User not found")
    @GetMapping("/{id}")
    public UserResponse getById(
            @Parameter(description = "User ID", example = "42")
            @PathVariable Long id) { ... }
}
```

For DTOs:

```java
@Schema(description = "User creation request")
public record CreateUserRequest(
        @Schema(description = "User's email address", example = "alice@example.com")
        String email,

        @Schema(description = "User's display name", example = "Alice Martin")
        String name
) {}
```

## ADR rules

When generating an Architecture Decision Record:

- Use the standard ADR format: Title, Status, Context, Decision, Consequences.
- Keep it factual and concise.
- Mention alternatives considered.
- Place in `docs/adr/` with a numbered filename (`0001-use-jwt-for-authentication.md`).

Template:

```markdown
# [NUMBER]. [TITLE]

**Status:** Accepted | Proposed | Deprecated | Superseded by [ADR-XXXX]

## Context
What is the problem or situation that requires a decision?

## Decision
What is the chosen approach and why?

## Alternatives considered
- **Alternative A** — why it was rejected
- **Alternative B** — why it was rejected

## Consequences
- **Positive:** what improves
- **Negative:** what trade-offs or costs are introduced
```

## General rules

- **Read before writing** — always understand the code before documenting it.
- **Match existing style** — if the project already has Javadoc or Swagger annotations, follow the same conventions.
- **Don't over-document** — documentation that restates the obvious adds noise, not clarity.
- **Keep it maintainable** — avoid documenting volatile implementation details that will drift out of sync.
