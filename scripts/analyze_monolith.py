"""Analyze MistHelper.py to find decomposition candidates.

Extracts all classes, methods, and top-level functions, counts their call sites,
and identifies the least-called non-core functions suitable for extraction.
"""

import re
import ast
import sys
from collections import defaultdict
from pathlib import Path


def analyze_monolith():
    src = Path("MistHelper.py").read_text(encoding="utf-8")
    lines = src.splitlines()
    total_lines = len(lines)

    # Parse AST for accurate analysis
    tree = ast.parse(src)

    # Collect all class definitions and their line ranges
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            end_line = getattr(node, "end_lineno", node.lineno)
            classes.append({
                "name": node.name,
                "start": node.lineno,
                "end": end_line,
                "size": end_line - node.lineno + 1,
                "methods": [],
            })

    # Collect methods within each class
    for cls_info in classes:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == cls_info["name"]:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        end_line = getattr(item, "end_lineno", item.lineno)
                        cls_info["methods"].append({
                            "name": item.name,
                            "start": item.lineno,
                            "end": end_line,
                            "size": end_line - item.lineno + 1,
                        })
                break

    # Collect top-level functions (not inside classes)
    top_level_funcs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            top_level_funcs.append({
                "name": node.name,
                "start": node.lineno,
                "end": end_line,
                "size": end_line - node.lineno + 1,
            })

    # Count call sites for every name
    call_counts = defaultdict(int)
    # Count attribute calls (self.method() or obj.method())
    attr_calls = defaultdict(int)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_counts[node.func.id] += 1
            elif isinstance(node.func, ast.Attribute):
                attr_calls[node.func.attr] += 1

    # Also count plain name references (not calls)
    name_refs = defaultdict(int)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name_refs[node.id] += 1

    # Print summary
    print(f"{'='*80}")
    print(f"MistHelper.py Analysis Report")
    print(f"{'='*80}")
    print(f"Total lines: {total_lines}")
    print(f"Total classes: {len(classes)}")
    print(f"Total top-level functions: {len(top_level_funcs)}")
    total_methods = sum(len(c["methods"]) for c in classes)
    print(f"Total class methods: {total_methods}")
    print()

    # Print classes sorted by size (largest first)
    print(f"{'='*80}")
    print(f"CLASSES (sorted by size, largest first)")
    print(f"{'='*80}")
    for cls in sorted(classes, key=lambda c: c["size"], reverse=True):
        ref_count = name_refs.get(cls["name"], 0)
        print(f"\n  {cls['name']} (lines {cls['start']}-{cls['end']}, "
              f"{cls['size']} lines, {len(cls['methods'])} methods, "
              f"{ref_count} references)")
        # Show methods sorted by size
        for m in sorted(cls["methods"], key=lambda x: x["size"], reverse=True):
            ac = attr_calls.get(m["name"], 0)
            cc = call_counts.get(m["name"], 0)
            total = ac + cc
            print(f"    def {m['name']}() "
                  f"[lines {m['start']}-{m['end']}, {m['size']} lines, "
                  f"{total} calls]")

    # Print top-level functions sorted by call count (least first)
    print(f"\n{'='*80}")
    print(f"TOP-LEVEL FUNCTIONS (sorted by call count, least first)")
    print(f"{'='*80}")
    for func in sorted(top_level_funcs, key=lambda f: call_counts.get(f["name"], 0)):
        cc = call_counts.get(func["name"], 0)
        print(f"  def {func['name']}() "
              f"[lines {func['start']}-{func['end']}, {func['size']} lines, "
              f"{cc} calls]")

    # Identify decomposition candidates
    # Criteria: methods/functions that are called <= 3 times, are >= 20 lines,
    # and are not core workflow (__init__, main, run, etc.)
    core_names = {
        "__init__", "__str__", "__repr__", "__enter__", "__exit__",
        "__del__", "__getattr__", "__setattr__", "__hash__", "__eq__",
        "main", "run", "setup", "teardown", "close", "cleanup",
    }

    print(f"\n{'='*80}")
    print(f"DECOMPOSITION CANDIDATES")
    print(f"(methods called <= 3 times, >= 20 lines, not dunder/core)")
    print(f"{'='*80}")

    candidates = []
    for cls in classes:
        for m in cls["methods"]:
            if m["name"] in core_names or m["name"].startswith("__"):
                continue
            ac = attr_calls.get(m["name"], 0)
            cc = call_counts.get(m["name"], 0)
            total = ac + cc
            if total <= 3 and m["size"] >= 20:
                candidates.append({
                    "class": cls["name"],
                    "name": m["name"],
                    "start": m["start"],
                    "end": m["end"],
                    "size": m["size"],
                    "calls": total,
                })

    # Also check top-level functions
    for func in top_level_funcs:
        if func["name"] in core_names or func["name"].startswith("__"):
            continue
        cc = call_counts.get(func["name"], 0)
        if cc <= 3 and func["size"] >= 20:
            candidates.append({
                "class": "(top-level)",
                "name": func["name"],
                "start": func["start"],
                "end": func["end"],
                "size": func["size"],
                "calls": cc,
            })

    # Sort by size descending (biggest extraction wins)
    candidates.sort(key=lambda c: c["size"], reverse=True)

    for c in candidates:
        print(f"\n  {c['class']}.{c['name']}()")
        print(f"    Lines: {c['start']}-{c['end']} ({c['size']} lines)")
        print(f"    Call sites: {c['calls']}")

    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(candidates)} decomposition candidates found")
    print(f"Total extractable lines: {sum(c['size'] for c in candidates)}")
    print(f"{'='*80}")

    # Now find where each candidate is actually called (line numbers)
    print(f"\n{'='*80}")
    print(f"CALL SITE DETAILS (where each candidate is invoked)")
    print(f"{'='*80}")

    for c in candidates[:50]:  # Top 50 biggest
        func_name = c["name"]
        call_lines = []
        for i, line in enumerate(lines, 1):
            # Skip the definition line itself
            if i >= c["start"] and i <= c["end"]:
                continue
            # Look for calls to this function/method
            if re.search(rf'\b{re.escape(func_name)}\s*\(', line):
                call_lines.append((i, line.strip()[:100]))
            # Also look for references without call (passed as callback etc.)
            elif re.search(rf'self\.{re.escape(func_name)}\b', line):
                if i < c["start"] or i > c["end"]:
                    call_lines.append((i, line.strip()[:100]))

        print(f"\n  {c['class']}.{c['name']}() [{c['size']} lines, "
              f"defined at line {c['start']}]")
        if call_lines:
            for ln, text in call_lines:
                print(f"    Line {ln}: {text}")
        else:
            print(f"    NO EXTERNAL CALL SITES FOUND (dead code?)")


if __name__ == "__main__":
    analyze_monolith()
