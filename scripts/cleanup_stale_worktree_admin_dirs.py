"""Force-remove stale .git/worktrees/<name> admin dirs on Windows.

Why:
    `git worktree prune` fails silently on Windows when admin dirs contain
    read-only files (git objects). Enumerates every admin dir under
    .git/worktrees, keeps only those whose 'gitdir' file points to a
    currently-existing worktree, and force-removes the rest with the
    chmod-onerror rmtree pattern from cleanup_merged_worktrees.py.
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


def _on_rm_error(func: Callable[[str], object], path: str, exc: BaseException) -> None:
    """Clear read-only bit and retry (Windows shutil.rmtree recipe)."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:  # noqa: BLE001
        print(f"    onerror-retry-failed: {path}: {e}", file=sys.stderr)
        raise


def force_rmtree(target: Path, retries: int = 3, sleep_s: float = 0.5) -> bool:
    """Delete a directory tree on Windows, retrying transient locks."""
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


def active_admin_names() -> set[str]:
    """Return the basename of each .git/worktrees/<name> that git considers live.

    Why:
        A worktree admin dir is live iff its 'gitdir' file inside points to
        an existing checkout directory. Parsing `git worktree list --porcelain`
        is the authoritative source.
    """
    proc = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    live: set[str] = set()
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ").strip()
            live.add(Path(path).name)
    return live


def main() -> int:
    """Enumerate admin dirs, keep live ones, force-remove the rest."""
    admin_root = REPO_ROOT / ".git" / "worktrees"
    if not admin_root.exists():
        print(f"no admin root: {admin_root}")
        return 0

    live = active_admin_names()
    # The main repo doesn't have an admin subdir, so live names are only
    # for secondary worktrees. Any admin dir NOT in live is stale.
    all_admin = {p.name for p in admin_root.iterdir() if p.is_dir()}
    stale = sorted(all_admin - live)
    print(f"admin dirs total:  {len(all_admin)}")
    print(f"admin dirs live:   {len(all_admin & live)}  -> keep")
    print(f"admin dirs stale:  {len(stale)}  -> remove")
    for name in stale:
        print(f"  - {name}")

    removed: list[str] = []
    failed: list[str] = []
    for name in stale:
        target = admin_root / name
        print(f"\n=== {target}")
        if force_rmtree(target):
            removed.append(name)
        else:
            failed.append(name)

    print("\n===== SUMMARY =====")
    print(f"stale admin dirs removed: {len(removed)}/{len(stale)}")
    if failed:
        print(f"FAILED ({len(failed)}):")
        for n in failed:
            print(f"  - {n}")

    # Sanity: make sure the live ones are still recognized.
    print("\n=== git worktree list (post-clean)")
    subprocess.run(["git", "worktree", "list"], cwd=REPO_ROOT, check=False)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
