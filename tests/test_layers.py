"""Core is the save editing library; the CLI is built on it, never the reverse."""

import ast
from pathlib import Path

CORE = Path(__file__).parent.parent / "src" / "bcsfe" / "core"


def cli_imports(path: Path) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [a.name for a in node.names]
            if node.module.startswith("bcsfe.cli") or (
                node.module == "bcsfe" and "cli" in names
            ):
                found.append(f"{path.relative_to(CORE)}:{node.lineno}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("bcsfe.cli"):
                    found.append(f"{path.relative_to(CORE)}:{node.lineno}")
    return found


def test_core_does_not_import_the_cli() -> None:
    offenders = [hit for f in sorted(CORE.rglob("*.py")) for hit in cli_imports(f)]
    assert offenders == []
