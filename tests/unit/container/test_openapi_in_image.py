"""Guard the OpenAPI input that menu 243 reads inside the container.

Issue #3104: `.dockerignore` excluded the whole `documentation/` directory, so
the image carried no OpenAPI file and menu 243 failed on every container run.

```text
error: [Errno 2] No such file or directory: 'documentation/mist-api-openapi31json.json'
```

`OperationRegistry` calls menu 243 `safe`, so the portal lists it and an
operator can start it. An operation that the portal offers must either work or
state why it cannot.

These tests hold both halves. The packaging rule must keep the one file the
generator reads, and an absent file must produce a reason instead of a raw
errno.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mib_generator.document import OpenApiDocument
from src.mib_generator.runner import DEFAULT_OPENAPI

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCKERIGNORE = REPOSITORY_ROOT / ".dockerignore"
# Podman prefers `Containerfile` and Docker prefers `Dockerfile`. Both files
# exist here, so a copy rule that lands in one and not the other repairs only
# one build. Issue #3104 met exactly that: the `Dockerfile` edit changed
# nothing, because `podman build` read `Containerfile`.
BUILD_FILES = ("Dockerfile", "Containerfile")


def _dockerignore_lines() -> list[str]:
    """Return every rule line of the ignore file, without a comment or a blank."""
    text = DOCKERIGNORE.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


class TestTheImageCarriesTheOpenApiFile:
    """The packaging rule must keep the one file the generator reads."""

    def test_the_generator_default_still_names_that_file(self):
        """The test must guard the path the runner really reads."""
        assert DEFAULT_OPENAPI == Path("documentation") / "mist-api-openapi31json.json"

    def test_the_file_exists_in_the_repository(self):
        """A packaging rule cannot restore a file the repository does not hold."""
        assert (REPOSITORY_ROOT / DEFAULT_OPENAPI).is_file()

    def test_the_ignore_file_restores_the_openapi_file(self):
        """The negation line must name the exact file the generator reads."""
        assert f"!{DEFAULT_OPENAPI.as_posix()}" in _dockerignore_lines()

    def test_the_ignore_file_drops_the_directory_contents(self):
        """The contents form must be used, because a negation cannot escape an excluded directory."""
        lines = _dockerignore_lines()
        assert "documentation/*" in lines
        assert "documentation/" not in lines  # This form would make the negation below it useless.

    def test_the_negation_follows_the_exclusion(self):
        """Order decides the result, so the negation must come after the exclusion."""
        lines = _dockerignore_lines()
        assert lines.index("documentation/*") < lines.index(f"!{DEFAULT_OPENAPI.as_posix()}")

    def test_the_other_openapi_files_stay_out_of_the_image(self):
        """Only the file with a runtime reader may enter the image."""
        restored = [line for line in _dockerignore_lines() if line.startswith("!documentation/")]
        assert restored == [f"!{DEFAULT_OPENAPI.as_posix()}"]


class TestEveryBuildFileCopiesTheOpenApiFile:
    """Podman reads Containerfile and Docker reads Dockerfile, so both must copy it."""

    @pytest.mark.parametrize("build_file", BUILD_FILES)
    def test_build_file_exists(self, build_file):
        """The test must guard a file that the repository really holds."""
        assert (REPOSITORY_ROOT / build_file).is_file()

    @pytest.mark.parametrize("build_file", BUILD_FILES)
    def test_build_file_copies_the_openapi_file(self, build_file):
        """A copy rule in one file repairs one build only, so both must carry it."""
        text = (REPOSITORY_ROOT / build_file).read_text(encoding="utf-8")
        copy_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("COPY ")]
        assert any(
            DEFAULT_OPENAPI.name in line for line in copy_lines
        ), f"{build_file} must copy {DEFAULT_OPENAPI.name}, or menu 243 fails in a build that reads it"

    @pytest.mark.parametrize("build_file", BUILD_FILES)
    def test_build_file_copies_into_the_expected_directory(self, build_file):
        """The runner reads a relative path, so the file must land under that directory."""
        text = (REPOSITORY_ROOT / build_file).read_text(encoding="utf-8")
        line = next(line.strip() for line in text.splitlines() if DEFAULT_OPENAPI.name in line and "COPY" in line)
        assert line.endswith("./documentation/")  # The runner reads documentation/ relative to /app.


class TestAnAbsentFileNamesAnAction:
    """A raw errno tells an operator nothing, so the reason must carry an action."""

    def test_absent_file_raises_a_named_reason(self, tmp_path):
        """The message must name the path and the action that restores the file."""
        missing = tmp_path / "mist-api-openapi31json.json"
        with pytest.raises(FileNotFoundError) as caught:
            OpenApiDocument(missing).load()
        message = str(caught.value)
        assert str(missing) in message  # The operator must learn which path failed.
        assert "rebuild the image" in message  # The container action.
        assert "pull the repository again" in message  # The clone action.

    def test_the_message_is_not_a_bare_errno(self, tmp_path):
        """The reported text named no action, so that shape must not return."""
        with pytest.raises(FileNotFoundError) as caught:
            OpenApiDocument(tmp_path / "absent.json").load()
        assert "No such file or directory" not in str(caught.value)

    def test_a_present_file_still_loads(self, tmp_path):
        """The guard must not block the path that already worked."""
        path = tmp_path / "openapi.json"
        path.write_text('{"openapi": "3.1.0", "paths": {}, "components": {"schemas": {}}}', encoding="utf-8")
        document = OpenApiDocument(path).load()
        assert document.operations() == {}  # An empty document indexes no operation.

    def test_a_damaged_file_still_names_the_json_position(self, tmp_path):
        """The new guard must not hide the existing JSON error message."""
        path = tmp_path / "openapi.json"
        path.write_text('{"openapi": "3.1.0"', encoding="utf-8")  # The writer stopped mid-object.
        with pytest.raises(json.JSONDecodeError):  # Prove the body really fails to parse.
            json.loads(path.read_text(encoding="utf-8"))
        with pytest.raises(ValueError) as caught:
            OpenApiDocument(path).load()
        assert "holds no valid JSON" in str(caught.value)

    def test_an_empty_body_names_the_json_position(self, tmp_path):
        """An interrupted download leaves an empty body, which is not a missing file."""
        path = tmp_path / "openapi.json"
        path.write_bytes(b"")  # The download stopped before the first byte.
        with pytest.raises(ValueError) as caught:
            OpenApiDocument(path).load()
        assert "holds no valid JSON" in str(caught.value)  # The reason must name the content, not the path.
