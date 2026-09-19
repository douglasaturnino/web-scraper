"""Validate Google-style docstring args contain typed parameters."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from docstring_parser import Style, parse

TYPE_REQUIRED_MESSAGE = (
    "Google-style Args must include types, e.g. `name (type): description`."
)


def check_file(path: Path) -> list[str]:
    """Check a single Python file for missing docstring types."""
    issues: list[str] = []
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        issues.append(f"{path}:{exc.lineno}: syntax error: {exc.msg}")
        return issues

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node)
        if not docstring:
            continue
        parsed = parse(docstring, style=Style.GOOGLE)
        if not parsed.params:
            continue
        for param in parsed.params:
            type_name = param.type_name or ""
            if not type_name.strip():
                issues.append(
                    f"{path}:{node.lineno}: missing parameter type for `{param.arg_name}` "
                    f"in `{node.name}`"
                )
    return issues


def main(argv: list[str] | None = None) -> int:
    """Run the docstring type checker for given file paths."""
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: check_docstring_types <file>...")
        return 1

    issues: list[str] = []
    for raw_path in argv:
        path = Path(raw_path)
        if path.is_dir():
            for child in sorted(path.rglob("*.py")):
                issues.extend(check_file(child))
        elif path.exists():
            issues.extend(check_file(path))
        else:
            issues.append(f"{raw_path}: file not found")

    if issues:
        print(TYPE_REQUIRED_MESSAGE)
        for issue in issues:
            print(issue)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
