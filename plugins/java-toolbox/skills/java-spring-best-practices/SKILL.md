---
name: java-spring-best-practices
description: Java Spring Boot best practices for writing and reviewing code — covers security, Spring patterns, Java idioms, code conventions, testing, SQL migrations, and SOLID design.
disable-model-invocation: false
---

# Java Spring Boot Best Practices

Apply these rules when writing, reviewing, or refactoring Java/Spring Boot code specified in `$ARGUMENTS`. Flag violations using the severity levels below. When generating new code, follow all rules proactively.

## Severity levels

- **blocker** — Must be fixed before merge. Security vulnerabilities, data loss risks, silent test failures.
- **issue** — Should be fixed. Bugs, performance problems, missing transactions, broken contracts.
- **suggestion** — Recommend fixing. Readability, maintainability, design improvements.
- **nitpick** — Optional. Style preferences, minor polish.

---

## 1. SQL Migrations

Applies to: `**/V*.sql`, `**/db/migration/**`

| Rule | Severity | Summary |
|------|----------|---------|
| `sql-drop-table-without-backup` | blocker | Never DROP TABLE without a backup strategy (backup table, RENAME, or 2-phase deprecation) |
| `sql-not-null-without-default` | issue | Adding NOT NULL to existing column requires a DEFAULT value or a multi-step migration (add column → backfill → add constraint) |
| `sql-missing-index-on-fk` | suggestion | Always CREATE INDEX on foreign key columns before adding the FK constraint |
| `sql-large-data-migration` | issue | Mass UPDATE/INSERT must be batched (LIMIT N in a loop) to avoid table locks and redo log saturation |

---

## 2. Security (OWASP Top 10)

Applies to: `**/*.java`, `**/application*.yml`, `**/application*.properties`

| Rule | Severity | Summary |
|------|----------|---------|
| `security-sql-injection` | blocker | Never concatenate strings into SQL. Use JPA derived queries, `@Query` with named params, or `JdbcTemplate` with named params |
| `security-hardcoded-secret` | blocker | No secrets in source code. Use `@Value("${...}")`, Vault, or a secret manager |
| `security-cors-wildcard` | issue | No `origins = "*"`. Whitelist specific domains |
| `security-xss-vulnerability` | blocker | Never return raw user input in HTML. Use Thymeleaf (auto-escapes) or `org.owasp.encoder.Encode` |
| `security-insecure-deserialization` | blocker | Never use `ObjectInputStream` on untrusted data. Use Jackson with type whitelisting |

---

## 3. Spring Boot Patterns

Applies to: `**/*.java`

### `spring-field-injection` (suggestion)
Use constructor injection (or `@RequiredArgsConstructor`), not `@Autowired` on fields.

### `spring-missing-transactional` (issue)
Service methods that modify the database must be annotated `@Transactional`. Without it, partial failures leave data inconsistent and lazy-loading fails outside the session.

### `spring-n-plus-one-query` (issue)
Iterating a collection of entities and accessing a lazy relation inside the loop triggers N+1 queries. Fix with `JOIN FETCH`, `@EntityGraph`, or `@BatchSize`.

### `spring-controller-business-logic` (suggestion)
Controllers handle HTTP mapping only. Delegate all business logic to a `@Service`. This enables unit testing, reuse across interfaces, and separation of concerns.

### `spring-exception-not-handled` (issue)
Don't let RuntimeExceptions bubble into generic 500 responses. Create domain exceptions and a `@ControllerAdvice` with `@ExceptionHandler` methods that return structured error responses.

---

## 4. Java Best Practices

Applies to: `**/*.java`

### `java-null-pointer-risk` (issue)
Use `Optional` for nullable return values. Never chain method calls on a possibly-null reference without checking first. Prefer `orElseThrow()` with a domain exception.

### `java-empty-catch-block` (issue)
Never swallow exceptions silently. Catch specific exceptions, log with context, and either rethrow a domain exception or return a documented default.

### `java-raw-type-usage` (suggestion)
Always parameterize generic types: `List<User>`, not `List`.

### `java-string-concatenation-loop` (suggestion)
Use `StringBuilder` or `Collectors.joining()` instead of `+=` in loops (O(n) vs O(n^2)).

### `java-equals-hashcode-contract` (issue)
Always override both `equals()` and `hashCode()` together. Or use Lombok `@EqualsAndHashCode`.

### `java-resource-not-closed` (issue)
Use try-with-resources for all `AutoCloseable` resources (streams, connections, prepared statements).

### `java-reverse-equals` (issue)
Put the known non-null value on the left: `"ADMIN".equals(user.getRole())`, not `user.getRole().equals("ADMIN")`. Or use `Objects.equals()` for variable-to-variable comparison.

---

## 5. Code Conventions

Applies to: `**/*.java`, `**/*.yml`, `**/*.properties`

### `english-only` (issue)
All code, comments, and log messages must be in English. Exception: user-facing i18n strings in `messages*.properties`.

### `no-cryptic-names` (issue)
No single-letter variables (except `i`, `j`, `k` in loops, `e`/`ex` in catch, lambdas where type provides context). No generic names like `tmp`, `data`, `val`, `obj`, `res`. Use descriptive names: `userName`, `orderTotal`, `shippingAddress`.

### `always-use-braces` (issue)
All `if`, `for`, `while`, `else` blocks must have curly braces, even for single statements.

### `avoid-var-keyword` (suggestion)
Use explicit types for readability: `List<User> users = ...`, not `var users = ...`. Tolerated only when the RHS constructor makes the type obvious (`var list = new ArrayList<String>()`).

### `no-restating-comments` (nitpick)
Comments should explain *why*, not *what*. Delete comments that restate the next line of code.

### `public-method-javadoc` (suggestion)
Public methods on services, utilities, and library classes should have Javadoc. Excluded: getters/setters, `@Override`, controller endpoints (use OpenAPI annotations), test methods.

### `corporate-package-naming` (issue)
Packages must follow `com.instantsystem.<domain>.<component>`. Maven groupId must match.

---

## 6. Test Conventions

Applies to: `**/*Test.java`, `**/*IT.java`, `**/*Tests.java`

> **To generate tests**, use the `/java-unit-test` skill — it implements all the conventions below with full templates, examples, and mocking rules.

| Rule | Severity | Summary |
|------|----------|---------|
| `test-given-when-then-structure` | issue | Test body must use Given/When/Then structure separated by blank lines |
| `test-no-try-catch` | blocker | Never use try/catch for exception assertions. Use `assertThatThrownBy()`. Use `assertThatCode().doesNotThrowAnyException()` for no-throw assertions |
| `test-one-behavior-per-test` | issue | Each test verifies exactly one behavior. One reason to fail |
| `test-use-assertj` | issue | Always use AssertJ (`assertThat`), never JUnit assertions (`assertEquals`, `assertTrue`) |
| `test-no-magic-values` | suggestion | Use named constants for non-obvious values |
| `test-behavioral-naming` | suggestion | Method names describe behavior: `shouldRejectExpiredCoupons`, not `testProcessOrder` |
| `test-use-nested-classes` | suggestion | Group related tests with `@Nested` inner classes |

---

## 7. Design Conventions (SOLID)

Applies to: `**/*.java`

### `no-named-provider` (issue)
Never reference specific provider names (Conduent, AEP, Kuba, TER) in business code. Use a strategy/abstraction so providers can be added or removed without modifying business logic.

### `interface-implementation-split` (suggestion)
Services should have a corresponding interface. Consumers depend on the interface, not the concrete class. Enables mocking, swapping implementations, and proper Spring proxying.

### `law-of-demeter` (issue)
Avoid deep method chains: `order.getCustomer().getAddress().getCity()`. Delegate via domain methods: `order.getShippingCity()`.

### `god-class-srp` (issue)
A class should have one reason to change. Split classes with many unrelated responsibilities (especially "Manager", "Handler", "Processor" names) into focused services.

### `switch-to-strategy` (issue)
Replace behavioral switch/if-else chains dispatching on type or status with the Strategy pattern or a map of implementations. Tolerated for simple data-mapping switches (<3 trivial cases).

### `open-closed-principle` (issue)
Code should be open for extension, closed for modification. Use interfaces, plugin registries, or strategy maps so new behavior is added via new classes, not by editing existing ones.

### `liskov-substitution` (issue)
Implementations must honor the parent contract: accept the same inputs, don't throw unexpected exceptions, don't return hardcoded values, don't narrow preconditions.

### `interface-segregation` (suggestion)
Split fat interfaces into focused ones. Implementors should never need `throw new UnsupportedOperationException()` stubs. Each consumer depends only on the methods it uses.
