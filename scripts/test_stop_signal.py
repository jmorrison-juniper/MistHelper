"""Automated tests for ConfigUtils.check_stop_signal() in MistHelper.py.

Tests the file-based stop signal mechanism that allows users to cancel
long-running site/device iteration loops by creating stop_loop.txt.

Usage:
    python scripts/test_stop_signal.py

No API token, Mist org, or user interaction required.
"""

import os
import sys


def check_stop_signal():
    """Mirror of ConfigUtils.check_stop_signal() from MistHelper.py."""
    if os.path.exists("stop_loop.txt"):
        try:
            os.remove("stop_loop.txt")
        except OSError:
            pass
        print("  Stop signal detected. Ending operation early.")
        return True
    return False


def cleanup():
    """Remove stop_loop.txt if it exists from a failed test."""
    if os.path.exists("stop_loop.txt"):
        os.remove("stop_loop.txt")


def test_no_file_returns_false():
    """No stop file present should return False."""
    cleanup()
    result = check_stop_signal()
    assert result is False, f"expected False, got {result}"


def test_file_present_returns_true():
    """Stop file present should return True and delete the file."""
    with open("stop_loop.txt", "w") as f:
        f.write("")
    assert os.path.exists("stop_loop.txt"), "stop file was not created"

    result = check_stop_signal()
    assert result is True, f"expected True, got {result}"
    assert not os.path.exists("stop_loop.txt"), "stop file was not cleaned up"


def test_consumed_signal_returns_false():
    """After signal is consumed, next call should return False."""
    with open("stop_loop.txt", "w") as f:
        f.write("")
    check_stop_signal()

    result = check_stop_signal()
    assert result is False, f"expected False after consumption, got {result}"


def test_loop_breaks_on_signal():
    """Simulated site loop should break when stop signal is detected."""
    sites = ["site_a", "site_b", "site_c", "site_d", "site_e"]
    processed = []

    with open("stop_loop.txt", "w") as f:
        f.write("")

    for site in sites:
        if check_stop_signal():
            break
        processed.append(site)

    assert len(processed) == 0, f"expected 0 sites before stop, got {processed}"
    assert not os.path.exists("stop_loop.txt"), "stop file not cleaned up"


def test_loop_processes_until_signal():
    """Loop should process sites normally until stop file appears mid-run."""
    sites = ["site_a", "site_b", "site_c", "site_d", "site_e"]
    processed = []

    for i, site in enumerate(sites):
        if i == 3:
            with open("stop_loop.txt", "w") as f:
                f.write("")
        if check_stop_signal():
            break
        processed.append(site)

    assert processed == ["site_a", "site_b", "site_c"], (
        f"expected 3 sites, got {processed}"
    )


def main():
    tests = [
        ("No stop file returns False", test_no_file_returns_false),
        ("File present returns True and deletes", test_file_present_returns_true),
        ("Consumed signal returns False", test_consumed_signal_returns_false),
        ("Loop breaks immediately on signal", test_loop_breaks_on_signal),
        ("Loop processes until mid-run signal", test_loop_processes_until_signal),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            cleanup()
            test_func()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as error:
            print(f"  FAIL  {name}: {error}")
            failed += 1
        finally:
            cleanup()

    print()
    print(f"{passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
