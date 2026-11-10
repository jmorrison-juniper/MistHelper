# Dependency Export Research

## Decisions

### Package updates

**Decision**: Use the reviewed compatible update preview. Keep all existing package constraints.

**Rationale**: The issue requests `importlib-metadata` 10.2.0, `openai` 3.48.0, and `pypdfium2` 5.15.2. A broader update needs review before it enters the lock.

**Alternative considered**: Update only the three named packages. This would omit the compatible updates in the reviewed preview.

Re-run `uv lock --upgrade --dry-run --upgrade-package 'openai==3.48.0'` after rebasing this branch onto current `main`. Treat that preview as the update set. Review all package changes before changing the lock.

### Lock and exports

**Decision**: Update `uv.lock`, then generate both exports with `uv export --locked`.

**Rationale**: `--locked` prevents export from changing the lock. The existing export guard compares each generated file with its locked output.

**Alternative considered**: Use `pip freeze` from one environment. This method can omit packages for other platforms and does not preserve the universal export.

Use the existing export shapes:

- Runtime: `uv export --locked --no-hashes --no-emit-project --output-file requirements.txt`
- Development: `uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt`

### Platform markers

**Decision**: Preserve all 11 runtime markers and validate the generated exports against the existing declarations.

**Rationale**: UV creates a universal lock. Its exports retain environment markers for evaluation on the target system. The exporting host does not define the complete platform set.

**Alternative considered**: Generate a platform-specific requirements file. This would remove support for other target systems.

### Security audit coverage

**Decision**: Run the audit on both exports and report its platform scope. Identify each dependency source that the audit cannot inspect.

**Rationale**: Each `pip-audit` run resolves requirements for the current Python and platform. The two runs do not audit every marker combination.

**Alternative considered**: Treat one host audit as proof for all platforms. This would overstate the result.

The development export can contain a Git dependency. Report that source as unaudited if the audit cannot resolve and check it.

## Evidence

- Issue #4727 names the required package versions, marker preservation, exports, release note, and checks.

- A preview on the older branch resolved 200 packages, selected 24 upgrades, and added one package. The branch predates current `main`, so this result is historical only.

- The repository has three guardrail tests. They check declarations, the lock, and the exports.

## Sources

- [UV lock command](https://docs.astral.sh/uv/reference/cli/#uv-lock)
- [UV export command](https://docs.astral.sh/uv/reference/cli/#uv-export)
- [UV universal resolution](https://docs.astral.sh/uv/concepts/resolution/#universal-resolution)
- [UV project sync](https://docs.astral.sh/uv/concepts/projects/sync/)
- [pip-audit documentation](https://pypi.org/project/pip-audit/)
- [pip-audit requirement handling](https://github.com/pypa/pip-audit/blob/721b0b04b9e287ec5db8f5a812656c6c4ee260ef/pip_audit/_dependency_source/requirement.py)
- [pip-audit requirement tests](https://github.com/pypa/pip-audit/blob/b93d61fbf8f113b21ddf154a96e905d81b13fdaa/test/dependency_source/test_requirement.py)
