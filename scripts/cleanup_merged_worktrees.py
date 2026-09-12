"""Force-remove merged worktrees + branches on Windows/OneDrive.

Why:
    `git worktree remove --force` fails on Windows with "Permission denied"
    when files carry the read-only attribute (git packs objects and some
    checked-out files this way) or when OneDrive/VS Code holds transient
    handles. `shutil.rmtree` with an onerror hook that clears the read-only
    bit and retries is the standard workaround.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(r"c:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper")

# (worktree_path_relative_to_repo_or_absolute, branch_name)
# Empty branch_name skips the `git branch -D` step (use when the remote branch
# was already deleted by GitHub auto-merge with --delete-branch).
TARGETS: list[tuple[str, str]] = [
    (r".claude\worktrees\886-site-anomaly-exporter", ""),
    (r".claude\worktrees\887-pydocstyle-capture", ""),
    (r".claude\worktrees\887-pydocstyle-export", ""),
    (r".claude\worktrees\887-pydocstyle-inventory", ""),
    (r".claude\worktrees\887-pydocstyle-troubleshooting", ""),
    (r".claude\worktrees\887-pylint-narrow", ""),
]


def _on_rm_error(func: Callable[[str], object], path: str, exc: BaseException) -> None:
    """Clear read-only bit and retry, per Windows shutil.rmtree recipe.

    Why:
        Git objects and pack files are stored read-only; the default
        rmtree cannot delete them without first chmodding.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:  # noqa: BLE001
        print(f"    onerror-retry-failed: {path}: {e}", file=sys.stderr)
        raise


def force_rmtree(target: Path, retries: int = 3, sleep_s: float = 0.5) -> bool:
    """Delete a directory tree on Windows, retrying transient locks.

    Args:
        target: Directory to delete.
        retries: Attempts before giving up (handles OneDrive/AV race).
        sleep_s: Delay between retries.

    Returns:
        True if the directory is gone (or was already absent).
    """
    if not target.exists():
        return True
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            shutil.rmtree(target, onexc=_on_rm_error)
            return not target.exists()
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"    attempt {attempt}/{retries} failed: {e}", file=sys.stderr)
            time.sleep(sleep_s)
    print(f"    GIVING UP on {target}: {last_err}", file=sys.stderr)
    return False


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a shell command and capture output."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def main() -> int:
    """Remove each target worktree directory, prune metadata, delete branch."""
    os.chdir(REPO_ROOT)
    removed_dirs: list[str] = []
    failed_dirs: list[str] = []
    deleted_branches: list[str] = []
    failed_branches: list[str] = []

    for rel_path, branch in TARGETS:
        wt = (REPO_ROOT / rel_path).resolve()
        print(f"\n=== {wt}  ->  {branch}")
        ok = force_rmtree(wt)
        if ok:
            removed_dirs.append(str(wt))
        else:
            failed_dirs.append(str(wt))
            continue

    # One prune to reap all .git/worktrees/<name> admin dirs at once.
    print("\n=== git worktree prune")
    rc, out, err = run(["git", "worktree", "prune", "-v"], REPO_ROOT)
    print(out or "(no output)")
    if err:
        print(err, file=sys.stderr)

    # Now delete the branches (safe: worktree admin dirs are gone).
    # Skip entries with empty branch name — those were already deleted upstream.
    for _, branch in TARGETS:
        if not branch:
            continue
        rc, out, err = run(["git", "branch", "-D", branch], REPO_ROOT)
        if rc == 0:
            deleted_branches.append(branch)
            print(f"  branch deleted: {branch}")
        else:
            failed_branches.append(f"{branch}: {err or out}")
            print(f"  branch delete FAILED: {branch}: {err or out}", file=sys.stderr)

    print("\n===== SUMMARY =====")
    print(f"worktree dirs removed:  {len(removed_dirs)}/{len(TARGETS)}")
    print(f"worktree dirs failed:   {len(failed_dirs)}")
    for p in failed_dirs:
        print(f"  - {p}")
    branch_targets = [b for _, b in TARGETS if b]
    print(f"branches deleted:       {len(deleted_branches)}/{len(branch_targets)}")
    print(f"branches failed:        {len(failed_branches)}")
    for b in failed_branches:
        print(f"  - {b}")

    return 0 if (not failed_dirs and not failed_branches) else 1


if __name__ == "__main__":
    raise SystemExit(main())
