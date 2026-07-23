# Engineering Standards

This document defines project-wide engineering rules for service boundaries, mocks, singletons, and tests.

These rules apply to both humans and agents.

Examples of external service boundaries include:

- HTTP APIs
- Object storage
- Message brokers

## External Service Boundaries

### Required

- Put communication with external control-plane services behind a thin adapter layer, called `Contact`.
- Keep `Contact` implementations transport-oriented. They should translate calls and data, not own higher-level policy.
- Put reconciliation, caching, orchestration, and business rules above the contact layer.
- Make callers depend on the contact boundary, not on direct SDK calls.
- A contact must expose the smallest interface that still covers all external communication needed by the package.
- Create Abstract Contact classes, to define the interface, and provide a real implementation a mock one for tests.
- Contact methods should be named in domain terms, but stay close to the underlying service operations.

### Forbidden

- Do not scatter direct calls to external services throughout application code.
- Do not put TTL state, reconciliation policy, or business rules inside a contact.
- Do not make a contact responsible for unrelated convenience behavior just because it already talks to the service.
- Do not add methods to a contact that are really local application concerns.
- Do not require tests to mock upstream SDK internals when they can mock the contact instead.
- Do not call `super()` implementations directly from high-level wrappers if the same operation is supposed to be 
  mocked through a contact.

## Mock Contact Rules

### Required

- When implementing a library, put reusable mock contacts in production code when downstream projects are expected to
  use them in their own tests. Thanks to this, downstream repos can use these mocks to implement their own tests 
  without the need to mock your whole library or learning how to mock its contact.
- Mock contacts should be placed into a clearly named test-support module.
- Make mock contacts implement the same abstract contact interface as the real contact.
- Keep mock contacts declarative.
- Allow mock contacts to be mutated during a single test.
- Record calls in a structured way so tests can assert externally visible behavior.
- Drive test scenarios by configuring the mock contact, not by patching internal helpers below the public seam.
- Cover non-happy-path behavior through the mock contact, not only happy paths.
- When a contact method returns collections or other aggregate results, include mixed-scenario tests that combine valid
  items with invalid, missing, stale, or otherwise problematic items in the same case so the test proves one bad item 
  does not break the whole result.
- Configure mocks in domain terms:
  - current listed items or records
  - current synchronized contact result
  - current externally stored state
  - upload outcome
- Mock contacts should be either stateless or be easy to reset so that leakage across tests.

### Forbidden

- Do not make downstream tests rebuild low-level transport responses when a mock contact can express the same scenario
  directly.
- Do not make mocks immutable snapshots if the production behavior depends on changing external state.
- Do not hide call history from tests.
- Do not use ad hoc fakes that bypass the package's abstract contact interface when a production mock contact exists or
  should exist.

## Contact Factory rules

### Required

- Expose contact access through module-level factory functions. It can return a singleton or not, depending on the 
  circumstances.
- Depend on the factory function at call sites.
- Patch the factory function in tests.
- Keep singleton services stateless where possible.

### Preferred Pattern

```python
_contact_instance: AbstractContact | None = None


def contact() -> AbstractContact:
    global _contact_instance
    if _contact_instance is None:
        _contact_instance = RealContact()
    return _contact_instance
```

### Forbidden

- Do not instantiate real contacts ad hoc throughout the codebase.
- Do not make tests patch deep internals when patching the singleton factory is enough.

## Public API Testing Rules

### Required

- Test behavior through public APIs.
- Mock only true external boundaries that are expensive or inappropriate to run in-process.
- This usually includes stubbing HTTP responses with `aioresponses`
- When a contact boundary exists, patch the contact factory and configure a concrete mock contact instance that
  implements the abstract contact.
- Keep internal helpers real in public-API tests when practical, including manifest builders, reconciliation helpers,
  parsers, and crypto helpers.
- Public-API tests that use mock contacts should cover both successful and unsuccessful external data in the same 
  suite, and should prefer mixed-result cases for collection reads when that is how production behavior is exercised.
- Use real certificates, keys, and realistic domain objects in tests when practical. These should be generated 
  specifically for the tests and not be copied from production values.
- Prefer asserting final public outcomes and externally visible side effects.

### Forbidden

- Do not write tests that target private or internal helper methods unless there is no reasonable public path.
- Do not write tests whose only value is checking trivial internal shapes, such as:
  - `assert isinstance(some_internal_method(...), str)`
  - direct testing of parsing helpers that are already covered through public behavior
- Do not mock internal methods just to force code through a branch when a public API test can cover it.
- Do not patch internal helper functions below the selected public seam, such as manifest builders, reconciliation
  helpers, parsing helpers, or similar domain logic, when a mock contact or other true external-boundary stub can
  express the scenario.
- Do not replace real domain objects with placeholder objects if constructing the real object is practical.
- Do not ever use production credentials or secrets in tests.

## Value Assertion Rules

### Required

- Assert concrete expected values: specific field values, specific counts, specific
  IDs/content — not just that a response has the right shape.
- When a value cannot be asserted concretely because an external service makes it 
  non-deterministic, e.g. timestamps, generated IDs,  treat that as a signal to add
  or extend a `Contact` boundary and a matching mock
  `Contact`, then configure the mock to a known value and assert exactly that value.

### Forbidden

- Do not write tests whose only assertions check shape or type, such as
  `assert "field" in response`, `assert isinstance(response, dict)`,
  `assert len(result) > 0`, without also asserting the actual expected values.
- Do not fall back to shape-only assertions as a substitute for adding the Contact
  and mock Contact needed to make a concrete value assertable.

## Testing Environment Setup

### Required

- If Docker services are required for tests (e.g. databases) they should be configured via a docker-compose.yml file in
  the repository root and started with `docker compose up -d` (run in background) or `docker compose up` (run in 
  foreground).
- If the project already configures services with Docker compose, it is permitted to place testing-specific services
  into the development version of this configuration but never in the production version.
- Any Docker services or other resources required by tests must be started outside of the testing pipeline.

### Forbidden

- Test setup must not build, start, stop, or otherwise spawn Docker containers.
- Test-exclusive services must not be included in the production deployment.

## Real Contact Integration Testing Rules

### Required

- Every real external-service contact must have dedicated real-implementation tests. This is mandatory, not optional 
  polish.
- Those tests must live in dedicated files.
- Those tests must exercise only public contact methods.
- Those tests may be heavy integration tests.
  - If they are indeed heavy integration tests they should be opt-in locally and expected in CI. 
- When practical, those tests should create their own disposable external-service environment. Follow the setup rules
  below rather than relying on accidental fixture state.

### Forbidden

- Do not treat mock-contact coverage as a substitute for real contact integration coverage.
- Do not test private contact helpers in place of real contact behavior.
- Do not hide real contact tests inside unrelated wrapper test modules.

## Real Integration Environment Setup Rules

### Required

- Shape real integration fixtures around explicit domain roles, not around misleading names.
- Prefer fixtures that make roles concrete and inspectable.
- Use real artifacts in those environments when practical, e.g. real certificates and request payloads.
- Assert the intended environment topology during setup against the real service state, not against assumptions.
- In collection-oriented real contact tests, prefer composite scenarios that exercise multiple states in sequence or in
  one case, including mixed healthy and problematic records.
- When testing collection reads, make expected outputs include unaffected valid records as well as problematic records
  so the test proves partial failure does not poison the whole result.
- Include concrete assertions for actual returned values, not only presence checks.
- Dump returned objects to stable dict or list-of-dicts forms when that makes the full behavior easier to assert in one
  comparison.
- If a stateful real environment causes transaction collisions, nonce reuse, or other cross-test interference, isolate
  the affected test in its own disposable environment instead of weakening assertions.
- If the real service has constraints that make one mixed-state transition impossible in-place, use a second fresh real
  environment inside the same test or test module rather than replacing the scenario with mocks.

### Forbidden

- Do not use semantically misleading fixtures to stand in for a role they do not actually have.
- Do not overfit integration tests to happy-path topologies.
- Do not assert only that a record exists when the actual returned payload can be asserted concretely.
- Do not silently ignore extra actors returned by the real service; either account for them explicitly in assertions or
  reshape the fixture so the topology is unambiguous.
- Do not keep reusing a shared real environment for stateful write tests once it is clear that prior writes interfere
  with later assertions.

## Stateful Infrastructure Exception

### Required

- For stateful infrastructure such as PostgreSQL or Redis, prefer running a real test instance over mocking the client
  protocol.
- Use lightweight real instances when they are cheap to start in tests (but ensure that these instances are started in
  orchestration code and not in pytest itself).
- Reserve mocking for cases where a real instance is not practical.

### Forbidden

- Do not treat databases like HTTP APIs for unit-style response mocking if the test can run a real database instead.
- Do not over-mock persistence boundaries in ways that make behavior diverge from production semantics.

## Good And Bad Patterns

This section is a remix of the above principles, not introducing new ones, and is here to provide a useful set of
examples.

### Good

- High-level code calls a contact factory or contact accessor instead of reaching into a service SDK directly.
- Tests patch that boundary, return a concrete mock contact implementing the abstract interface, and drive public APIs
  rather than internal helpers.
- Collection-oriented tests mix healthy and unhealthy external items in one case to prove the component keeps valid
  results while excluding or handling bad ones correctly.
- HTTP-backed behavior is exercised with realistic stubs and real cryptographic material when practical.
- Mock contacts are reconfigured mid-test to simulate state changes.
- Real contact implementations have dedicated integration tests in their own test modules.
- Real integration fixtures prove their role topology against actual service state before the assertions that depend on
  it.
- Tests assert the concrete values a call produced (specific fields, IDs, counts), and reach for a mock contact
  configured to a known value when the real value would otherwise be non-deterministic.

### Bad

- High-level code talks directly to external SDKs outside the contact layer.
- Tests patch private helpers instead of the external boundary.
- Tests cover only fully happy-path contact data and never exercise mixed success/failure collection results.
- Tests assert internal helper return types instead of public behavior.
- Tests use placeholder objects when realistic domain objects are easy to build.
- Tests depend on shared real-environment write state even after collisions or interference are visible.
- Tests assert only that a field exists or has the right type, and never pin down what value it actually holds.

## Review Checklist

Before merging, check all of the following:

- External service communication is isolated behind the correct contact boundary.
- Contacts are thin and transport-focused.
- Policy and caching live above contacts.
- Singleton factory functions are the patch point in tests.
- Mock contacts implement the abstract contact interface and expose structured call history plus scenario configuration
  methods.
- Public tests mock only external boundaries.
- Public tests do not patch internal helper functions below the chosen public seam.
- Mock-contact tests cover unhappy paths and mixed-result collection scenarios, not only pure happy paths.
- Real contact integration tests exist in dedicated files for every real external-service contact.
- Real integration test fixtures prove their intended actor roles and state against the actual external service.
- No test exists only to validate an internal helper's trivial return shape.
- Databases and similar stateful systems are tested with real instances unless there is a strong reason not to.
- Tests assert concrete expected values, not just response shape; where a value is only non-deterministic because of a
  missing Contact seam, the seam and its mock were added instead of weakening the assertion.
