"""Enforce the structural limits for the interactive terminal feature."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import ast  # Python syntax trees provide exact structural measurements.
import re  # JavaScript class headers need a bounded local parser.
from dataclasses import dataclass  # One result object carries the printed counts.
from pathlib import Path  # Paths keep the guard portable across test hosts.

import pytest  # The bounded bad fixture must prove an assertion failure.


@dataclass
class StructureCounts:
    """Hold the source counts that the guard prints."""

    modules: int = 0  # Count each checked Python or JavaScript module.
    classes: int = 0  # Count each checked Python or JavaScript class.
    functions: int = 0  # Count Python callables and JavaScript class methods.

    def add_tree(self, tree: ast.Module) -> None:
        """Add counts from one Python syntax tree."""
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]  # Find all classes.
        callables = [  # Find functions, methods, and nested functions.
            node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.modules += 1  # Record the parsed Python module.
        self.classes += len(classes)  # Record all nested and top-level classes.
        self.functions += len(callables)  # Record functions, methods, and nested functions.

    def add_values(self, modules: int, classes: int, functions: int) -> None:
        """Add explicit source counts."""
        self.modules += modules  # Add the checked module count.
        self.classes += classes  # Add the checked class count.
        self.functions += functions  # Add the checked function count.

    @classmethod
    def combine(cls, counts: tuple[StructureCounts, ...]) -> StructureCounts:
        """Combine source counts from each language guard."""
        result = cls()  # Start one empty count result.
        for count in counts:  # Add each language result once.
            result.add_values(count.modules, count.classes, count.functions)  # Preserve each exact count.
        return result  # Give the test one printable result.


class PlanSourceInventory:
    """Resolve and read every current source below the planned feature roots."""

    def __init__(self, root: Path) -> None:
        """Read the plan and set the two feature source roots."""
        self.root = root  # Keep the repository root for all path checks.
        self.roots = self._read_plan()  # Fail before scanning when the plan is unreadable.

    def _read_plan(self) -> tuple[Path, Path]:
        """Read the plan and return its feature source roots."""
        plan, markers = self.root / "specs/3671-interactive-terminal/plan.md", (  # Set the plan and markers.
            "src/websocket_streams/live/",
            "src/websocket_streams/web/",
        )
        try:  # Convert an input read problem into an explicit guard failure.
            text = plan.read_text(encoding="utf-8")  # Read the authoritative feature path list.
        except OSError as error:  # Do not let an unreadable plan look like a clean scan.
            raise AssertionError(f"cannot read input {plan}: {error}") from error  # State the failed input.
        assert "### Source Code" in text and all(
            marker in text for marker in markers
        ), f"missing feature source paths in {plan}"
        return self.root / markers[0].rstrip("/"), self.root / markers[1].rstrip("/")  # Resolve both source roots.

    def files(self, scope: tuple[tuple[str, str], ...]) -> list[Path]:
        """Return readable files from the exact task path scope."""
        files: list[Path] = []  # Collect every mapped source and replacement leaf.
        for original, replacement in scope:  # Resolve each original and replacement pair.
            old, current = self.root / original, self.root / replacement  # Build both repository paths.
            assert current.exists(), f"cannot read input {current}"  # Require each current replacement.
            assert old == current or not old.exists(), f"obsolete source path remains: {old}"  # Reject wrappers.
            files.extend(current.rglob("*") if current.is_dir() else [current])  # Expand replacement packages.
        files = sorted({path for path in files if path.is_file()})  # Remove duplicate files from shared parents.
        for path in files:  # Prove that every planned source input opens.
            try:  # Convert a file read problem into an explicit guard failure.
                path.read_bytes()  # Read the complete input so partial access cannot pass.
            except OSError as error:  # Do not skip an unreadable source file.
                raise AssertionError(f"cannot read input {path}: {error}") from error  # State the failed input.
        return files  # Give each language guard the same verified inventory.

    def directory_errors(self, scope: tuple[tuple[str, str], ...]) -> list[str]:
        """Return scoped directories that have more than five child items."""
        errors: list[str] = []  # Collect all directory failures for one report.
        directories: set[Path] = set()  # Keep each owned hierarchy level once.
        for _original, replacement in scope:  # Resolve every mapped replacement path.
            current = self.root / replacement  # Build the current source path.
            directories.add(current if current.is_dir() else current.parent)  # Check the direct owner.
            if current.is_dir():  # Replacement packages own their nested directories.
                directories.update(item for item in current.rglob("*") if item.is_dir())  # Add nested levels.
        for directory in sorted(directories):  # Measure each owned directory once.
            children = [item for item in directory.iterdir() if item.name != "__pycache__"]  # Ignore generated caches.
            if len(children) > 5:  # Enforce the package hierarchy limit.
                errors.append(f"directory {directory} has {len(children)} child items")  # Report the exact count.
        return errors  # Let one assertion report all directory failures.


class PythonStructureGuard:
    """Measure Python modules, classes, functions, methods, and blocks."""

    def inspect(self, paths: list[Path]) -> StructureCounts:
        """Assert all Python limits and return exact checked counts."""
        counts, errors = StructureCounts(), []  # Keep counts and failures for one bounded scan.
        for path in paths:  # Parse each current Python feature module.
            tree = ast.parse(  # Parse one verified Python source input.
                path.read_text(encoding="utf-8"), filename=str(path)
            )  # Fail on unreadable or invalid input.
            counts.add_tree(tree)  # Add exact module, class, and callable counts.
            errors.extend(  # Add module, class, function, and method failures.
                self._hierarchy_errors(path, tree) + self._function_errors(path, tree)
            )  # Check every Python level.
        assert not errors, "\n".join(errors)  # Fail with every measured structural violation.
        return counts  # Print these counts from the passing contract test.

    def _hierarchy_errors(self, path: Path, tree: ast.Module) -> list[str]:
        """Return module and class hierarchy failures."""
        kinds = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)  # Count direct callable constructs.
        children = [node for node in tree.body if isinstance(node, kinds)]  # Measure direct module children only.
        errors = [f"module {path} has {len(children)} child items"] if len(children) > 5 else []  # Check the module.
        for node in (item for item in ast.walk(tree) if isinstance(item, ast.ClassDef)):  # Measure each class.
            methods = [  # Count direct class methods only.
                item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]  # Count methods.
            if len(methods) > 5:  # Enforce the class hierarchy limit.
                errors.append(f"class {path}:{node.name} has {len(methods)} methods")  # Report the exact count.
        return errors  # Return all hierarchy failures from this module.

    def _function_errors(self, path: Path, tree: ast.Module) -> list[str]:
        """Return each callable metric failure."""
        errors: list[str] = []  # Collect all callable failures for this module.
        for node in (  # Measure each Python function and method.
            item for item in ast.walk(tree) if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]  # Read declared parameters.
            implicit = bool(parameters and parameters[0].arg in {"self", "cls"})  # Exclude the bound receiver.
            counted = len(parameters) - implicit + bool(node.args.vararg) + bool(node.args.kwarg)  # Count inputs.
            logical_blocks, operations = self._callable_metrics(node)  # Measure controls and expression work.
            line_count = (node.end_lineno or node.lineno) - node.lineno + 1  # Satisfy typed optional AST metadata.
            names, values, limits = (  # Keep metric names, results, and limits aligned.
                ("lines", "parameters", "logical blocks", "operations"),
                (line_count, counted, logical_blocks, operations),
                (25, 5, 5, 5),
            )
            for name, value, limit in zip(names, values, limits, strict=True):  # Compare each named metric once.
                if value > limit:  # Report only a measured violation.
                    errors.append(f"function {path}:{node.name} has {value} {name}")  # State the exact result.
        return errors  # Return every line, parameter, block, and operation failure.

    def _callable_metrics(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]:
        """Return logical-block and statement-operation maxima."""
        controls = (ast.If, ast.For, ast.AsyncFor, ast.While) + (  # Define each logical control block.
            ast.With,
            ast.AsyncWith,
            ast.Try,
            ast.Match,
        )  # Define blocks.
        if_nodes = [item for item in ast.walk(node) if isinstance(item, ast.If)]  # Find each conditional chain.
        elif_nodes = {  # Join each elif branch to its first if block.
            id(item.orelse[0]) for item in if_nodes if item.orelse and isinstance(item.orelse[0], ast.If)
        }  # Identify continuations of one if block.
        logical_blocks = sum(  # Count each complete control chain once.
            isinstance(item, controls) and id(item) not in elif_nodes for item in ast.walk(node)
        )  # Merge elif chains.
        statements = [  # Find each executable statement in the callable.
            item for item in ast.walk(node) if isinstance(item, ast.stmt) and item is not node
        ]  # Find statements.
        operations = max(  # Keep the largest single-statement operation count.
            (self._statement_operations(statement) for statement in statements), default=0
        )  # Measure expressions.
        return logical_blocks, operations  # The caller applies the repository limits.

    def _statement_operations(self, statement: ast.stmt) -> int:
        """Count expression operations in one Python statement."""
        skipped = {"body", "orelse", "finalbody", "handlers", "cases"}  # Exclude nested statement blocks.
        roots = [  # Normalize scalar and list fields into expression roots.
            item
            for name, value in ast.iter_fields(statement)
            if name not in skipped
            for item in (value if isinstance(value, list) else [value])
            if isinstance(item, ast.AST)
        ]
        kinds: tuple[type[ast.AST], ...] = (ast.Call, ast.BinOp, ast.BoolOp, ast.Compare, ast.IfExp)  # Set operations.
        kinds += (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)  # Add comprehension operations.
        candidates = [  # Keep the bounded expression operations from one statement level.
            item for root in roots for item in (root, *ast.iter_child_nodes(root)) if isinstance(item, kinds)
        ]
        parents = {  # Exclude a container operation when its direct child performs the work.
            id(parent)
            for parent in candidates
            if any(isinstance(child, kinds) for child in ast.iter_child_nodes(parent))
        }
        return sum(id(item) not in parents for item in candidates)  # Count independent leaf operations only.


class JavaScriptStructureGuard:
    """Measure first-party JavaScript modules, classes, and class methods."""

    def inspect(self, paths: list[Path]) -> StructureCounts:
        """Assert JavaScript module and class limits."""
        counts, errors = StructureCounts(), []  # Keep exact counts and failures together.
        for path in paths:  # Inspect each first-party JavaScript module.
            source = self._clean(path.read_text(encoding="utf-8"))  # Remove strings and comments before brace scans.
            classes = self._class_ranges(source)  # Find each class and its bounded body.
            methods = {name: self._method_count(body) for name, body in classes}  # Count direct methods only.
            counts.add_values(1, len(classes), sum(methods.values()))  # Add this module and its class methods.
            errors.extend(  # Add a JavaScript module hierarchy failure.
                [f"module {path} has {len(classes)} class items"] if len(classes) > 5 else []
            )
            errors.extend(  # Add each JavaScript class method failure.
                f"class {path}:{name} has {count} methods" for name, count in methods.items() if count > 5
            )
        assert not errors, "\n".join(errors)  # Fail with every JavaScript hierarchy violation.
        return counts  # Include JavaScript in the printed feature counts.

    def _clean(self, source: str) -> str:
        """Remove text that can contain non-structural braces."""
        pattern = (  # Match JavaScript comments and string literals.
            r"/\*.*?\*/|//[^\n]*|'(?:\\.|[^'\\])*'|" r"\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`"
        )  # Match comments and strings.
        return re.sub(  # Preserve line positions while removing non-structural text.
            pattern, lambda match: "\n" * match.group(0).count("\n"), source, flags=re.DOTALL
        )  # Preserve line breaks.

    def _class_ranges(self, source: str) -> list[tuple[str, str]]:
        """Return each JavaScript class name and body."""
        classes: list[tuple[str, str]] = []  # Keep direct class measurements for one module.
        for match in re.finditer(r"\bclass\s+([A-Za-z_$][\w$]*)\s*\{", source):  # Find class declarations.
            end = self._matching_brace(source, match.end() - 1)  # Find the class closing brace.
            if end is None:  # Invalid source must fail instead of passing an incomplete scan.
                raise AssertionError(f"unclosed JavaScript class {match.group(1)}")  # State the invalid class.
            classes.append((match.group(1), source[match.end() : end]))  # Keep the class body without its braces.
        return classes  # The caller checks module and method counts.

    def _method_count(self, body: str) -> int:
        """Count direct JavaScript class methods."""
        pattern = (  # Match direct JavaScript class method headers.
            r"(?m)^\s*(?:async\s+)?(?:get\s+|set\s+)?" r"(?:constructor|[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"
        )  # Match methods.
        matches = re.finditer(pattern, body)  # Find method-like headers at all body depths.
        return sum(  # Keep only method headers at the class-body depth.
            body[: match.start()].count("{") == body[: match.start()].count("}") for match in matches
        )  # Keep direct methods.

    def _matching_brace(self, source: str, start: int) -> int | None:
        """Return the closing brace index for one opening brace."""
        depth = 0  # Start before the opening brace changes the depth.
        for index in range(start, len(source)):  # Scan only the bounded source suffix.
            if source[index] == "{":  # Enter one nested brace range.
                depth += 1  # Record the new nesting level.
            elif source[index] == "}":  # Leave one nested brace range.
                depth -= 1  # Record the completed range.
            if depth == 0:  # The matching brace closes the requested range.
                return index  # Give the caller the exact closing position.
        return None  # An incomplete source file has no matching brace.


class TestWebSocketFeatureStructure:
    """Prove the guard fails for bad code and passes for current feature code."""

    ANALYSIS_SCOPE = (  # Map all 25 Python paths from the final structural analysis.
        ("src/websocket_streams/catalog/registry.py", "src/websocket_streams/catalog/registry"),
        ("src/websocket_streams/catalog/utilities.py", "src/websocket_streams/catalog/utilities"),
        ("src/websocket_streams/intake/fields.py", "src/websocket_streams/intake/fields"),
        ("src/websocket_streams/intake/identifiers.py", "src/websocket_streams/intake/identifiers"),
        ("src/websocket_streams/intake/pickers.py", "src/websocket_streams/intake/pickers"),
        ("src/websocket_streams/intake/start_request.py", "src/websocket_streams/intake/start_request"),
        ("src/websocket_streams/live/runners/channel.py", "src/websocket_streams/live/runners/channel"),
        ("src/websocket_streams/live/runners/shell.py", "src/websocket_streams/live/runners/shell"),
        ("src/websocket_streams/live/runners/text.py", "src/websocket_streams/live/runners/text"),
        (
            "src/websocket_streams/live/runners/utility/filters.py",
            "src/websocket_streams/live/runners/utility/filters",
        ),
        (
            "src/websocket_streams/live/runners/utility/runner.py",
            "src/websocket_streams/live/runners/utility/runner",
        ),
        (
            "src/websocket_streams/live/runners/utility/triggers.py",
            "src/websocket_streams/live/runners/utility/triggers",
        ),
        ("src/websocket_streams/live/sessions/buffer.py", "src/websocket_streams/live/sessions/buffer"),
        ("src/websocket_streams/live/sessions/manager.py", "src/websocket_streams/live/sessions/manager"),
        ("src/websocket_streams/live/sessions/record.py", "src/websocket_streams/live/sessions/record"),
        (
            "src/websocket_streams/live/terminal/byte_history.py",
            "src/websocket_streams/live/terminal/byte_history.py",
        ),
        ("src/websocket_streams/live/terminal/gateway.py", "src/websocket_streams/live/terminal/gateway.py"),
        (
            "src/websocket_streams/live/terminal/input_queue.py",
            "src/websocket_streams/live/terminal/input_queue.py",
        ),
        ("src/websocket_streams/live/terminal/state.py", "src/websocket_streams/live/terminal/state"),
        ("src/websocket_streams/live/transport/endpoint.py", "src/websocket_streams/live/transport/endpoint.py"),
        ("src/websocket_streams/live/transport/frames.py", "src/websocket_streams/live/transport/runtime"),
        (
            "src/websocket_streams/live/transport/stream_client.py",
            "src/websocket_streams/live/transport/stream_client.py",
        ),
        (
            "src/websocket_streams/live/transport/shell_client.py",
            "src/websocket_streams/live/transport/shell_client.py",
        ),
        ("src/websocket_streams/web/blueprint.py", "src/websocket_streams/web/blueprint"),
        ("src/websocket_streams/web/services.py", "src/websocket_streams/web/services"),
    )
    SUPPORT_SCOPE = (  # Keep the moved screen runner in the replacement proof.
        (
            "src/websocket_streams/live/runners/utility/screen.py",
            "src/websocket_streams/live/runners/shell/runners.py",
        ),
    )
    JAVASCRIPT_SCOPE = (  # Map the original terminal script to every split leaf script.
        ("src/websocket_streams/web/static/websockets_terminal.js", "src/websocket_streams/web/static/terminal"),
    )
    REPORTED_CLASSES = 28  # Preserve the final analysis class coverage floor.
    REPORTED_FUNCTIONS = 19  # Preserve the final analysis function coverage floor.

    def _bad_root(self, tmp_path: Path) -> Path:
        """Build one bounded source fixture with six module children."""
        root, live, web, plan = (  # Set all bounded fixture paths together.
            tmp_path / "bad-feature",
            tmp_path / "bad-feature/src/websocket_streams/live",
            tmp_path / "bad-feature/src/websocket_streams/web",
            tmp_path / "bad-feature/specs/3671-interactive-terminal/plan.md",
        )
        for directory in (live, web, plan.parent):  # Create the bounded source and plan folders.
            directory.mkdir(parents=True)  # Keep the fixture isolated from production files.
        plan.write_text(  # Write the two authoritative source roots.
            "### Source Code\nsrc/websocket_streams/live/\nsrc/websocket_streams/web/\n", encoding="utf-8"
        )  # Name both roots.
        live.joinpath("bad.py").write_text(  # Write six bounded module children.
            "\n".join(f"def item_{index}():\n    return {index}" for index in range(6)), encoding="utf-8"
        )  # Add six children.
        return root  # The red-path test scans only this temporary tree.

    def _measure_feature(self, root: Path) -> tuple[StructureCounts, tuple[tuple[str, str], ...]]:
        """Measure the complete T091 structural source scope."""
        inventory, directory_errors = PlanSourceInventory(root), []  # Resolve source roots before any scan.
        scope = self.ANALYSIS_SCOPE + self.SUPPORT_SCOPE + self.JAVASCRIPT_SCOPE  # Load every required mapping.
        assert len(self.ANALYSIS_SCOPE) == 25, "final analysis path count changed"  # Pin the reported path count.
        directory_errors.extend(inventory.directory_errors(scope))  # Measure only owned source directories.
        assert not directory_errors, "\n".join(directory_errors)  # Fail with every directory count.
        files = inventory.files(scope)  # Read every original replacement and each leaf module.
        python_files = [path for path in files if path.suffix == ".py"]  # Select scoped Python modules.
        javascript_files = [path for path in files if path.suffix == ".js"]  # Select scoped JavaScript modules.
        python_counts = PythonStructureGuard().inspect(python_files)  # Check each Python replacement leaf.
        javascript_counts = JavaScriptStructureGuard().inspect(javascript_files)  # Check each split script.
        assert python_counts.classes >= self.REPORTED_CLASSES, "reported class coverage decreased"  # Check classes.
        assert (
            python_counts.functions >= self.REPORTED_FUNCTIONS
        ), "reported function coverage decreased"  # Check functions.
        counts = (python_counts, javascript_counts)  # Keep both language results for exact aggregation.
        return StructureCounts.combine(counts), scope  # Return exact counts and the printed path scope.

    def test_bounded_bad_fixture_fails(self, tmp_path: Path) -> None:
        """Prove that six module children fail without production edits."""
        inventory = PlanSourceInventory(self._bad_root(tmp_path))  # Resolve only the temporary bad fixture.
        scope = (("src/websocket_streams/live/bad.py", "src/websocket_streams/live/bad.py"),)  # Set one bad path.
        with pytest.raises(AssertionError, match=r"module .* has 6 child items") as caught:  # Require the red path.
            PythonStructureGuard().inspect(  # Run the guard against the bounded bad module.
                [path for path in inventory.files(scope) if path.suffix == ".py"]
            )  # Run the guard.
        print(f"red-path proof: {caught.value}")  # Print the exact bounded failure evidence.

    def test_unreadable_input_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prove that an unreadable mapped source fails the guard."""
        root = self._bad_root(tmp_path)  # Build one isolated source tree with a valid plan.
        source = root / "src/websocket_streams/live/bad.py"  # Select the mapped source input.
        original = Path.read_bytes  # Preserve normal reads for every other path.

        def denied(path: Path) -> bytes:
            """Reject only the selected source input."""
            if path == source:  # Simulate an unreadable mapped source.
                raise PermissionError("test denied access")  # Trigger the explicit input failure.
            return original(path)  # Preserve all unrelated reads.

        monkeypatch.setattr(Path, "read_bytes", denied)  # Apply the bounded read failure.
        inventory = PlanSourceInventory(root)  # Read the plan before the source inventory.
        scope = (("src/websocket_streams/live/bad.py", "src/websocket_streams/live/bad.py"),)  # Map one input.
        with pytest.raises(AssertionError, match=r"cannot read input .*bad\.py") as caught:  # Require failure.
            inventory.files(scope)  # Read the mapped input through the guarded inventory.
        print(f"unreadable-input proof: {caught.value}")  # Print the exact read failure evidence.

    def test_current_feature_obeys_structural_limits(self) -> None:
        """Prove that the current feature implementation meets every limit."""
        root = Path(__file__).resolve().parents[6]  # Resolve the worktree root from this test location.
        PythonStructureGuard().inspect([Path(__file__)])  # Keep this guard within the same structural limits.
        counts, scope = self._measure_feature(root)  # Run checks against the complete T091 mapping table.
        assert counts == StructureCounts(145, 204, 622)  # Pin the complete feature measurement to known values.
        print("T091 mapping scope: " + " | ".join(f"{old} -> {new}" for old, new in scope))  # Print every mapping.
        print(  # Print the exact checked source counts.
            f"checked mappings={len(scope)} paths={len(self.ANALYSIS_SCOPE)} modules={counts.modules} "
            f"classes={counts.classes} functions={counts.functions}"
        )  # Print exact counts.
