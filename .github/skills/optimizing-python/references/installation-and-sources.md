# Installation, validation, and sources

This package contains a skill entry point and four reference guides. It contains
no application optimizer, executable benchmark, runtime dependency, or measured
performance claim.

## 1. Install the complete folder

1. Choose one skill location that the target agent supports. For a repository
   shared through GitHub Copilot, use `.github/skills/optimizing-python/`.
2. Check for an existing skill with the same name. Preserve local changes instead
   of overwriting an existing installation.
3. Copy `SKILL.md` and the complete `references/` directory together. Keep the
   folder name `optimizing-python`.
4. Open the target repository in the agent host. Confirm that the host discovers
   the skill before relying on automatic invocation.
5. If discovery does not refresh, start a new chat or reload the editor. Inspect
   skill diagnostics and supported locations if the skill remains absent.

Other supported VS Code project locations include `.agents/skills/` and
`.claude/skills/`. Personal locations include `~/.copilot/skills/`,
`~/.agents/skills/`, and `~/.claude/skills/`. Each location receives the complete
`optimizing-python` folder. Check another host's Agent Skills support before
choosing a location. Do not install duplicate names in multiple active locations.

The package uses relative resource links and standard `name` and `description`
frontmatter. It needs no installer or registration in a runtime requirements
file. Keep local-authored skills separate from an external installer's lockfile
unless that installer explicitly supports them.

The skill targets Python 3.12+ methods. A target project can require a newer
version. MistHelper requires Python 3.13+, so retain that requirement when using
the skill here. Read the target project's current configuration before execution.

Installing this skill does not authorize a repository-wide optimization,
dependency installation, production request, or change to concurrency settings.

## 2. Invoke the skill

Use one of these requests:

- "Use optimizing-python to profile this export path. Retain only measured
  improvements, with no application parallelization."
- "Use optimizing-python to investigate startup latency. Report only. Do not
  change application code."
- "Use optimizing-python to compare these two implementations with existing
  fixtures. Report timing, memory, correctness, and uncertainty."

In a compatible VS Code agent, `/optimizing-python` also invokes the skill.
The description supports automatic discovery for Python performance requests.
Discovery depends on the host and its settings, not on this file alone.

Supply the objective, entry point, representative inputs, and time budget when
you know them. Otherwise, the agent must establish them before an optimization.
The skill must not manufacture representative production inputs.

## 3. Validate a copied or modified skill

1. Parse the YAML frontmatter. Check that `name` matches the directory and contains
   at most 64 lowercase letters, digits, or hyphens.
2. Check that `description` is meaningful and contains at most 1,024 characters.
   Keep performance triggers and the no-parallelization boundary explicit.
3. Resolve every relative Markdown link. Check that the whole package remains
   self-contained after relocation. Keep the entry point below 500 lines.
4. Check the measurement contract, ten optimization areas, acceptance thresholds,
   and twelve report sections. Remove claims without evidence.
5. Run the repository's Markdown and prose checks. Inspect editor diagnostics.
   Exercise the scenarios below before declaring the workflow validated.

For MistHelper, run its STE linter with the project virtual environment and
`--min-score 80` on all five Markdown files. Use the repository's command-prefix
rules. If dictionary checks are unavailable, report that limitation separately.
Do not weaken a linter configuration to accept the skill.

## 4. Behavior scenarios

These scenarios test the skill's decisions. They are not application benchmarks
and do not establish performance improvements. Record actual responses when
testing the skill with an agent.

| ID | Request or condition | Expected decision |
| --- | --- | --- |
| S01 | Optimize a list scan with no workload or timing evidence. | Establish the contract, representative benchmark, and profile. Keep the idea a hypothesis. |
| S02 | Improve throughput with threads, asyncio tasks, or extra workers. | Exclude parallelization. Continue with sequential work reduction only. |
| S03 | pyperf uses several measurement processes. | Explain sequential isolation. Use in-process measurements if policy also prohibits subprocesses. |
| S04 | Benchmark a firmware upgrade against live production devices. | Do not repeat the destructive operation. Use a safe replay or isolated test workload. |
| S05 | A complicated rewrite shows a 2% gain inside measurement noise. | Reject or revert it. Preserve the raw results and other contributors' edits. |
| S06 | Cache authorization decisions or a current operational reading. | Reject unsafe caching. Preserve authorization and freshness. |
| S07 | A tracemalloc snapshot delta claims total allocation churn or RSS. | Correct the metric. Require suitable allocation or process-memory evidence. |
| S08 | Correctness tests pass but no benchmark can run. | Report the blocker and exact next benchmark. Make no speed claim. |
| S09 | The task concerns startup but a warm loop benchmark improves. | Measure fresh process startup and first-use costs. Do not substitute the loop result. |
| S10 | A native library silently starts parallel kernels. | Exclude that execution mode. Verify documented sequential execution before comparison. |
| S11 | A faster serializer changes Unicode or numeric error behavior. | Reject the incompatible change regardless of timing gain. |
| S12 | pyperf or a sampling profiler is unavailable. | Use supported standard-library measurements and state limits. Do not invent tool output. |
| S13 | The target repository requires Python 3.13 or newer. | Keep its minimum version. Do not downgrade it to match the skill title. |
| S14 | Removing required action logs meets a timing threshold. | Reject the logging change. Benchmark with the required production logging behavior. |

## 5. Source references

The source review date is **2026-09-09**. The user's supplied playbook defines
the scope and default acceptance thresholds. The references below support tool
behavior and technical cautions. They do not prove a gain in a target project.

Read documentation for the installed version before using optional flags or
native compilation. A `latest` page can describe a development version.
Follow links only when they resolve a relevant question. The packaged workflow
remains usable when external documentation is unavailable.

### Python measurement tools

- [Debugging and profiling](https://docs.python.org/3.12/library/debug.html)
  lists the standard-library tools.
- [Python profilers](https://docs.python.org/3.12/library/profile.html)
  explains deterministic profiling, timers, and limitations.
- [timeit](https://docs.python.org/3.12/library/timeit.html)
  explains repeats, setup exclusions, and the default GC suspension.
- [tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html)
  explains snapshots, traced memory peaks, and tracing overhead.

### Repeatable benchmarks

- [pyperf overview](https://pyperf.readthedocs.io/)
  describes the toolkit and stored benchmark results.
- [Run a benchmark](https://pyperf.readthedocs.io/en/latest/run_benchmark.html)
  explains calibration, warmups, loops, and sequential measurement processes.
- [Analyze results](https://pyperf.readthedocs.io/en/latest/analyze.html)
  explains distributions, medians, spread, and comparisons.
- [CLI reference](https://pyperf.readthedocs.io/en/latest/cli.html),
  [Runner CLI](https://pyperf.readthedocs.io/en/latest/runner.html), and
  [API reference](https://pyperf.readthedocs.io/en/latest/api.html)
  define commands, timing callbacks, and memory modes.
- [System tuning](https://pyperf.readthedocs.io/en/latest/system.html)
  describes environmental noise. It does not authorize changes to a shared host.

### Language and cache behavior

- [Python 3.12 documentation](https://docs.python.org/3.12/contents.html)
  indexes the versioned language and library references.
- [Python 3.12 changes](https://docs.python.org/3.12/whatsnew/3.12.html)
  explains comprehension inlining and interpreter changes.
- [functools](https://docs.python.org/3.12/library/functools.html)
  defines unbounded caches, LRU caches, and cached properties.

### Native compilation

- [Cython pure Python mode](https://cython.readthedocs.io/en/latest/src/tutorial/pure.html)
  explains `.py` integration and differences from interpreted execution.
- [Cython static typing](https://cython.readthedocs.io/en/latest/src/quickstart/cythonize.html)
  explains typed regions, conversion costs, and numeric behavior.
- [mypyc project](https://github.com/mypyc/mypyc) and
  [performance guidance](https://mypyc.readthedocs.io/en/latest/performance_tips_and_tricks.html)
  explain compilation scope and the need to profile first.
- [mypyc introduction](https://mypyc.readthedocs.io/en/latest/introduction.html) and
  [Python differences](https://mypyc.readthedocs.io/en/latest/differences_from_python.html)
  describe maturity and semantic restrictions. Recheck them before production use.

### Optional profiling and skill discovery

- [Scalene project](https://github.com/plasma-umass/scalene) and
  [Scalene package](https://pypi.org/project/scalene/)
  describe Python, native, system, memory, and copying attribution.
  Check installed-version support instead of assuming Windows is CPU-only.
- [VS Code Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
  defines skill discovery, supported locations, and frontmatter.
