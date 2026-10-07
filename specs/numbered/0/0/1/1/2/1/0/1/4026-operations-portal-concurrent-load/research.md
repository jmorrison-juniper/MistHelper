# Research: Operations Portal Concurrent Load

## Decision 1: Use one module-level primitive lock

**Decision**: Add one private `threading.Lock` in `web_portal/routes/operations.py`.

**Rationale**: The race exists inside one Python process and one route module.
A primitive lock gives mutual exclusion for the short initialization section.
The accessor does not re-enter itself, so a reentrant lock is not required.

**Alternatives considered**:

- Use `threading.RLock`. Rejected because the accessor has no recursive lock path.
- Store a lock in Flask configuration. Rejected because the requirement specifies one module-level lock.
- Initialize the executor during application startup. Rejected because the feature must preserve lazy initialization.
- Change `OperationExecutor`. Rejected because `web_portal/services/operation.py` is outside scope.

## Decision 2: Use double-checked initialization

**Decision**: Read `OPERATION_EXECUTOR` before the lock and repeat the read after lock acquisition.

**Rationale**: The first read keeps the initialized path free from lock acquisition.
The second read prevents a waiting caller from replacing the executor that the first caller stored.

**Alternatives considered**:

- Lock every accessor call. Rejected because it adds contention after initialization.
- Check only before the lock. Rejected because each waiting caller retains its stale empty result.
- Check only inside the lock. Rejected because every route call then acquires the lock.

## Decision 3: Keep construction and storage in one protected section

**Decision**: Keep the lazy import, constructor call, and configuration write inside the protected empty-state branch.

**Rationale**: No caller can observe a second construction path before the first instance is stored.
The existing constructor arguments and configuration source remain unchanged.

**Alternatives considered**:

- Construct outside the lock and store inside it. Rejected because competing callers can create unused worker pools.
- Store a placeholder before construction. Rejected because routes require a valid executor instance.
- Add a second accessor. Rejected because the specification requires `_get_executor()` as the only accessor.

## Decision 4: Force the race at the first configuration read

**Decision**: Use a controlled configuration mapping that blocks each caller on its first executor read.

**Rationale**: Each caller receives the same initial empty result before construction can start.
The unsynchronized implementation then constructs once per caller.
The synchronized implementation rechecks the stored value after it acquires the lock.

**Alternatives considered**:

- Add a barrier inside the fake constructor. Rejected because the synchronized implementation lets only one caller reach the constructor and would deadlock.
- Depend on short sleeps. Rejected because scheduler timing makes the result nondeterministic.
- Send real HTTP requests. Rejected because route transport is not required to prove the accessor race.
- Construct the real executor. Rejected because the test must not create real worker pools.

## Decision 5: Keep the test in the existing concurrency test module

**Decision**: Add the regression to `tests/unit/web_portal/test_operation_executor_concurrency.py`.

**Rationale**: The module already tests portal thread and concurrency behavior.
Using an existing file adds no child to the overfull `tests/unit/web_portal/` directory.

**Alternatives considered**:

- Add a new test file. Rejected because the directory already exceeds the constitution child limit.
- Add the test to the MSP selector module. Rejected because that module protects the PR #4065 selector contract.
- Add an end-to-end browser test. Rejected because the defect is an internal process-local race.

## Decision 6: Preserve all unrelated route behavior

**Decision**: Limit route changes to the import, lock declaration, and `_get_executor()`.

**Rationale**: PR #4065 added `list_msps` in the same route module.
The concurrency repair does not require any route, response, selector, or Mist API change.

**Alternatives considered**:

- Reformat or reorganize the route module. Rejected because it increases conflict risk and scope.
- Move the accessor to a service module. Rejected because the specification requires the current accessor and forbids service changes.

## Decision 7: Add the release note during implementation

**Decision**: Create `changelog.d/issue-4026-operation-executor-race.md` after the code and test changes.

**Rationale**: Repository policy requires one unique fragment for a user-visible repair.
The user requested planning artifacts only in this workflow.

**Alternatives considered**:

- Create the fragment during planning. Rejected by the explicit request.
- Edit `CHANGELOG.md`. Rejected by repository policy.
