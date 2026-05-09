---
# Source: references/ai-skills/skills/writing-tests/SKILL.md
# License: MIT
name: writing-tests
description: 'Generic test writing discipline: test quality, real assertions, anti-patterns, and rationalization resistance. Use when writing tests, adding test coverage, or fixing failing tests for any language or framework.'
---

# Writing Tests

## Core Principle

Tests prove behavior works. A test that can't fail is worthless. A test that tests mocks instead of real code is theater.

## Writing Good Tests

### One behavior per test

Each test should verify exactly one thing. If the test name needs "and" in it, split it into two tests.

```
Good:  "creates user with valid email"
Good:  "rejects user with duplicate email"
Bad:   "creates user and sends welcome email and updates counter"
```

### Derive test cases from three sources

Build test coverage from three independent sources and verify every item maps to at least one test:

1. **User requirements** -- what was requested (spec, issue, conversation)
2. **Features implemented** -- what the code actually does (scan the diff)
3. **Claims in the response** -- what you're about to tell the user works

Anything that appears in any source but has no corresponding test is a coverage gap. This catches the common failure mode where implemented features work but aren't tested, or where claimed behavior isn't verified.

For each source, enumerate user journeys: "As a [role], I want to [action], so that [benefit]." Generate test cases from each journey -- this ensures tests cover user-visible behavior, not implementation details.

### DAMP over DRY in tests

Each test should be independently readable without chasing shared setup through helper functions. Duplication in tests is acceptable -- even desirable -- when it makes the test's intent obvious at a glance. Extract shared setup only when it genuinely reduces noise without hiding what the test does.

### Test pyramid

For API/web projects, aim for ~80% unit, ~15% integration, ~5% E2E. Adjust ratios based on project risk profile -- data pipelines may need heavier integration coverage, CLI tools may need minimal E2E.

- **Unit tests (~80%)**: fast, isolated, test one behavior per test. Run in milliseconds. No database, no network, no filesystem. These form the foundation -- cheap to write, cheap to run, fast feedback.
- **Integration tests (~15%)**: verify component boundaries -- API endpoints hitting a real test database, service layers wired to real dependencies, queue producers and consumers working together. Slower than unit tests but catch wiring bugs that mocks hide.
- **E2E tests (~5%)**: validate critical user paths end-to-end through the real system. Expensive to write, slow to run, brittle to maintain. Limit to high-value flows (signup, checkout, core workflow). Every E2E test must justify its maintenance cost.

### Name tests by expected behavior

The test name should describe what happens, not what's being called.

```
Good:  "returns 404 when user does not exist"
Bad:   "test getUserById"
Good:  "sends notification after order is placed"
Bad:   "test processOrder"
```

### Use real objects when practical

Mocks should be a last resort, not a first choice. Every mock is an assumption about behavior that may drift from reality.

| Use real objects for | Use mocks/fakes for |
|---|---|
| Database queries (use test DB) | External HTTP APIs |
| Internal services and classes | Payment gateways |
| File system operations (use temp dirs) | Email/SMS delivery |
| Business logic and transformations | Third-party SDKs with rate limits |

**Exception: framework-provided test doubles.** When a framework offers dedicated faking mechanisms, use them -- they are the idiomatic approach and maintained alongside the framework. The principle is: avoid hand-rolled mocks that drift, not framework-blessed test utilities.

### Tests expose bugs, not the reverse

If a test uncovers broken or buggy behavior, fix the source code -- never adjust the test to match incorrect behavior. A test that passes against a bug is worse than no test at all.

### Assert on outcomes, not implementation

```
Good:  assert user exists in database after create
Bad:   assert repository.save() was called once
Good:  assert response body contains expected fields
Bad:   assert serializer.serialize() was called with user
```

### Test edge cases

For every feature, consider:

- Empty input / null / undefined
- Boundary values (0, 1, max, max+1)
- Invalid types (string where number expected)
- Concurrent access (if applicable)
- Error paths (network failure, timeout, permission denied)
- Unicode and special characters in string inputs

### Silent failure coverage

Tests must detect silent failures, not just happy paths. For every code path that catches, logs, or short-circuits on error, add an assertion that proves the failure was observable. Hunt targets during test writing:

- **Empty catch blocks** — add a test that triggers the error and asserts the logging or equivalent signal was invoked
- **Swallowed rejections** — add a test that triggers the rejection and asserts the caller sees a distinguishable signal
- **Converted errors** — assert both the return value AND that the error was recorded somewhere the operator can find it
- **Missing async handling** — assert that a rejected async operation causes a surfaced failure
- **No rollback around transactional work** — assert that a failure mid-transaction leaves no partial state

## Red-Green-Refactor (When It Applies)

Tests-first answer "what should this do?" Tests-after answer "what does this do?" The distinction matters: tests written after implementation are biased toward verifying what you built, not what's required.

For bug fixes, writing the failing test first is genuinely valuable -- it proves the bug exists and proves the fix works. For new features, the order is less critical than the quality.

### Bug fixes: prove-it pattern

The failing test is proof the bug exists. The passing test is proof the fix works. Without both halves, there is no proof -- just coincidence.

1. Write a test that reproduces the bug
2. **Run it and watch it fail** -- confirm it fails for the right reason. A test that fails due to a typo or import error hasn't captured the bug. The failure message should describe the buggy behavior.
3. Apply the fix
4. **Run it and watch it pass** -- confirm the fix addresses the specific failure AND other tests still pass. A fix that breaks something else isn't a fix.
5. If the test passes immediately without a fix, the test is verifying existing behavior, not the bug. Go back to step 1.

This is non-negotiable for bugs -- a fix without a regression test is a fix that will break again.

### New features: test alongside

Write tests as you build, not after. "I'll add tests later" means "I won't add tests."

The goal: by the time the feature is done, tests exist and pass. Whether you wrote the test 5 minutes before or 5 minutes after the code matters less than whether the test exists and is good.

**Minimum viability during green phase:** When making a test pass, write the simplest code that satisfies it. Not the abstraction you think is "right," not the feature you imagine you'll need next. The simplest thing. Refactor only after the test is green.

## Anti-Patterns

### Testing mock behavior instead of real behavior

**Symptom:** Test passes but production breaks. Tests assert that mocks were called correctly, not that the actual system works.

**Fix:** Replace mocks with real objects for internal code. Only mock at system boundaries (external APIs, email, payment).

### Test-only methods in production code

**Symptom:** Methods like `reset()`, `clearState()`, `setTestMode()` that exist only because tests need them.

**Fix:** If tests need to reset state, the code has a design problem. Refactor to make state explicit and injectable.

### Snapshot tests as the only test

**Symptom:** All tests are snapshots that get bulk-updated whenever anything changes.

**Fix:** Snapshots catch unintended changes but don't verify correctness. Add behavioral assertions alongside snapshots.

### Testing the framework

**Symptom:** Tests verify that the ORM saves records, the router routes requests, or the framework does what its docs say.

**Fix:** Trust the framework. Test YOUR logic -- the business rules, transformations, and decisions your code makes.

### Incomplete mocks

**Symptom:** Mock only includes the fields the test author knows about. Downstream code consumes other fields and gets undefined.

**Fix:** Mock the COMPLETE data structure as it exists in reality, not just the fields the immediate test uses. Use real objects or factory-generated fixtures with all fields populated. If you must mock, generate from the real type/schema.

### AI-generated test smells

Tests written by LLMs tend to produce a specific class of failures. Scan for these before committing:

- **Mock of the system under test** — mocking the very function being tested, so the test asserts what the mock returned. Always a mistake. Delete the mock; call the real function.
- **Circular assertion** — computing the expected value the same way the code computes the actual value. The test passes even when both are wrong. Replace with a hand-computed expected value or a known fixture.
- **Snapshot of unreviewed output** — first-run snapshot committed without reading it. The snapshot enshrines whatever the code happened to emit, bugs included. Hand-write the first snapshot or diff it line by line before accepting.
- **Assertion-free exercise** — test calls the function, checks nothing, passes because nothing threw. Every test needs at least one assertion tied to the behavior under test.
- **Over-broad matchers** — using a matcher that accepts too many values. Pin to the specific expected shape.
- **Implementation-echo assertions** — asserting on call counts when the real contract is an observable outcome. Assert on outcomes, not call counts.

## When Stuck

| Stuck on... | Do this |
|---|---|
| Don't know how to test | Write the assertion first (desired outcome), then build the test around it |
| Test too complicated | Simplify the interface being tested |
| Must mock everything | Code is too coupled -- use dependency injection |
| Test setup too large | Extract helpers that reduce noise without hiding test intent (see DAMP). Still complex? Simplify the design |

## Verify

Before considering tests complete:

- [ ] Every new public function/endpoint has at least one test
- [ ] Each test has a descriptive name stating expected behavior
- [ ] Tests use real objects where possible (mocks only at system boundaries)
- [ ] Edge cases covered (empty, null, boundary, error paths)
- [ ] Tests assert on outcomes, not implementation details
- [ ] Tests are independent -- no shared mutable state between tests. If tests pass individually but fail together, use bisection to find the polluter
- [ ] Tests run fast enough to run frequently (< 30 seconds for unit suite)
- [ ] Bug fix tests reproduce the original bug

Generated by autoharness | Template: community/skills/writing-tests/SKILL.md.tmpl
