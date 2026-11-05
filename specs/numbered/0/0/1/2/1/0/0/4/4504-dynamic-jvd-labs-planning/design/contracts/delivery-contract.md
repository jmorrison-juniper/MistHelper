# Delivery Contract

1. Add the framework as a Git submodule at a host-approved path and an exact reviewed commit (D-01). Create no `.gitmodules` entry until the approved delivery change.
2. Install only the `framework/` runtime package and its packaged resources. Root-level legacy tools are never a runtime dependency.
3. Use no `sys.path` change, no full-repository copy into the wheel, and no mutable source fetch at startup.
4. Do not install the framework dev extra in production. Run framework tests in a separate environment because it pins pytest below 9.
5. The container build and the release jobs initialize the submodule. The reusable image workflow currently omits it, so T033 fixes this before the gitlink ships (D-07).
6. Report the engine source revision in the portal and in the capability result.
7. Define fresh checkout, update, access credentials, and rollback steps. A rollback keeps compatible Labs records (see the persistence contract).
8. Keep the framework `framework/tests` suite in explicit coverage because the host pytest configuration does not collect it.
9. Verify a combined dependency solve, an installed runtime, and resource loading (T100).
