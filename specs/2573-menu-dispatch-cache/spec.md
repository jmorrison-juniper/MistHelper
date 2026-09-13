# Specification: MistHelper menu and mode cache

## Objective

Measure a sequential Python optimization for `MistHelper.py`. Retain it only when the measured result passes the rule.

## Workload

Measure two paths. The startup path runs `MistHelper.py --help` in a new process. The repeated path prints the menu many times and dispatches synthetic mode arguments many times.

## Scope

Cache the sorted menu key order for one exact key set. Cache the main mode predicate table. Do not change dependency checks, import order, CLI flags, menu text, menu order, or handler behavior.

## Constraints

Do not add parallel work. Do not call the Mist API. Preserve public interfaces, result order, error types, and validation.

## Acceptance

Retain the change if the repeated path improves by at least 10 percent. Reject the change if the cache can serve stale menu keys.
