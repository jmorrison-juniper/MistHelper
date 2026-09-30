"""Return the title guard result as the process exit code."""

from scripts.pr_title_guard import PullRequestTitleGuard

raise SystemExit(PullRequestTitleGuard().main())
