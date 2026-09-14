# Analysis: Empty pre-check targets

## Before evidence

Command:

```powershell
rtk ..\.venv\Scripts\python.exe -m pytest tests\unit\worker\test_check_tasks_empty_targets.py -q
```

Output:

```text
FAILED tests\unit\worker\test_check_tasks_empty_targets.py::test_pre_check_task_fails_closed_with_zero_targets
E       assert True is False
1 failed in 2.59s
```

## Defect confirmation

The defect is real. `PreCheckService.run_all()` returned an empty list when `target_ids` was empty. `_execute_pre_checks()` then used `all(result.passed for result in results)`. Python returns `True` for an empty iterator.

## Chosen behavior

An empty target set is an error. A safety gate that evaluates no target gives no proof. The service now returns one failed result named `target_selection`.

## After evidence

The targeted tests pass after the repair.

```text
17 passed in 1.87s
```
