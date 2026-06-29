---
name: java-unit-test
description: Generate Java Spring Boot JUnit 5 unit tests with AssertJ, @Nested classes, and behavioral naming. Use when the user asks to write or generate unit tests for Java/Spring code. French triggers: "écris des tests unitaires", "génère les tests JUnit", "teste cette classe", "ajoute des tests pour", "crée les tests unitaires".
disable-model-invocation: false
---

# Java Unit Test Generator

Write JUnit 5 unit tests for the class or feature specified in `$ARGUMENTS`.

## Stack

- **JUnit 5** (Jupiter) for test framework
- **AssertJ** for fluent assertions (`assertThat`)
- **Mockito** with `@ExtendWith(MockitoExtension.class)` for mocking dependencies
- **Instancio** for generating test data when complex object graphs are needed
- **Spring Boot Test** annotations only when testing Spring-specific behavior (controllers, repositories)

## Test class structure

1. **One `@Nested` inner class per public method** (or logical group of behavior) of the class under test.
   - Name the nested class after the method or behavior group: `class AddItem { ... }`, `class ConfirmCart { ... }`
2. Inside each `@Nested` class, group tests logically (happy path first, then edge cases, then error cases).

## Naming convention

Use **behavioral naming** with a `should` prefix that describes the expected outcome:

```
should<ExpectedBehavior>
should<ExpectedBehavior>When<Condition>
```

Examples:
- `shouldReturnUserWhenIdExists`
- `shouldThrowExceptionWhenEmailIsNull`
- `shouldReturnEmptyListWhenNoResults`
- `shouldPersistAndReturnOrderWhenValid`
- `shouldRejectExpiredCoupons`
- `shouldApplyDiscountForLargeCart`

Use `@DisplayName` when extra context helps (e.g., business rules with specific thresholds):
```java
@Test
@DisplayName("Should apply 10% discount when cart total exceeds 100 EUR")
void shouldApplyDiscountForLargeCart() { ... }
```

## Test anatomy (Given / When / Then)

Every test body must follow the **Given / When / Then** structure using **blank lines** to separate the three sections. **Do NOT include `// Given`, `// When`, `// Then` comments** — the structure should be self-evident from the code layout and the behavioral method name:

```java
@Test
void shouldReturnUserWhenIdExists() {
    Long userId = 1L;
    User expected = new User(userId, "Alice");
    when(userRepository.findById(userId)).thenReturn(Optional.of(expected));

    User result = userService.findById(userId);

    assertThat(result)
        .isNotNull()
        .satisfies(user -> {
            assertThat(user.getId()).isEqualTo(userId);
            assertThat(user.getName()).isEqualTo("Alice");
        });
}
```

The three blocks are:
1. **Setup** (Given) — prepare test data and mock behavior
2. **Action** (When) — call the method under test
3. **Verification** (Then) — assert the outcome

Each block is separated by a blank line. When the action and assertion are tightly coupled (e.g., exception testing), they can be combined:

```java
@Test
void shouldThrowWhenCouponIsExpired() {
    Coupon coupon = Instancio.of(Coupon.class)
        .set(field(Coupon::getExpirationDate), LocalDate.now().minusDays(1))
        .create();
    when(couponRepository.findByCode("SAVE10")).thenReturn(Optional.of(coupon));

    assertThatThrownBy(() -> couponService.apply("SAVE10"))
        .isInstanceOf(ExpiredCouponException.class);
}
```

## Assertions rules

- **Always use AssertJ** (`org.assertj.core.api.Assertions.assertThat`), never JUnit `assertEquals`/`assertTrue`/`assertFalse`/`assertNotNull`.
- Prefer specific AssertJ methods: `containsExactly`, `hasSize`, `extracting`, `satisfies`, `isInstanceOf`, `hasMessageContaining`.
- For exception testing, use `assertThatThrownBy(() -> ...)` or `assertThatExceptionOfType(...)`.
- For asserting no exception is thrown, use `assertThatCode(() -> ...).doesNotThrowAnyException()`.
- **Never use `try/catch` in tests** to assert on exceptions — this is fragile and can silently pass if `fail()` is missing.

## No magic values

Avoid unexplained magic numbers or string literals. Use named constants or descriptive inline comments:

```java
private static final int NETWORK_ID = 120;
private static final long DAYS_TO_LOOK_BACK = 500L;
private static final int EXPECTED_ORDER_COUNT = 42;

@Test
void shouldFilterRecentOrders() {
    OrderQuery query = new OrderQuery(NETWORK_ID, DAYS_TO_LOOK_BACK);

    List<Order> orders = orderService.findRecent(query);

    assertThat(orders).hasSize(EXPECTED_ORDER_COUNT);
}
```

## Mocking rules

- Use `@Mock` for dependencies and `@InjectMocks` for the class under test.
- Use `@Spy` only when you need to partially mock.
- Use `lenient()` only when strictly necessary; prefer strict stubs.
- Use `verify(...)` sparingly — only when the side effect IS the behavior being tested (e.g., verifying a notification was sent). Do NOT verify calls that are already covered by asserting the return value.
- Use `verifyNoMoreInteractions(...)` only when relevant to the test.

## Best practices to follow

- **One behavior per test** — each test should have exactly one reason to fail. Multiple `assertThat` calls on the same object are fine, but do not test unrelated behaviors in a single test.
- **No logic in tests** — no `if`, `for`, `switch`. Tests must be linear.
- **No shared mutable state** — use `@BeforeEach` for common setup but never share mutable objects across tests.
- **Test behavior, not implementation** — test what the method does, not how it does it internally.
- **Use `@ParameterizedTest`** with `@CsvSource`, `@ValueSource`, or `@MethodSource` when testing the same behavior with multiple inputs.
- **Use descriptive variable names** in tests: `expectedUser`, `invalidEmail`, `savedOrder`.
- **Do not test private methods** — test them through the public API.
- **Never use `var`** for local variables.
- Keep test classes focused: one test class per production class.

## File placement

Place the test file in the mirror `src/test/java` package matching the source class location.

## Template

```java
package com.example.service;

import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ClassUnderTestTest {

    @Mock
    private DependencyA dependencyA;

    @Mock
    private DependencyB dependencyB;

    @InjectMocks
    private ClassUnderTest classUnderTest;

    @Nested
    class MethodOne {

        @Test
        void shouldReturnExpectedResultWhenInputIsValid() {
            ...

            ...

            ...
        }

        @Test
        void shouldThrowExceptionWhenInputIsNull() {
            assertThatThrownBy(() -> classUnderTest.methodOne(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must not be null");
        }
    }

    @Nested
    class MethodTwo {
        ...
    }
}
```

## Execution

1. Read the target class to understand its public methods, dependencies, and behavior.
2. Identify all dependencies that need mocking.
3. For each public method, create a `@Nested` class.
4. Write tests covering: happy path, edge cases, error/exception cases, and boundary conditions.
5. Place the test file in the correct `src/test/java` mirror package.
