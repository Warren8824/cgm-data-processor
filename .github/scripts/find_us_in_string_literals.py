#!/usr/bin/env python3
"""Scan Python files for string literals that contain US-English spelling variants.

This inspects AST nodes for constant string values and f-strings (JoinedStr) and
reports occurrences of targeted US words inside them. It does NOT modify files.
"""
import ast
import re
import sys
from pathlib import Path

US_WORDS = [
    "analyze",
    "analyzing",
    "analyzed",
    "initialize",
    "initializing",
    "initialized",
    "organize",
    "organizing",
    "organized",
    "organization",
    "behavior",
    "color",
    "localize",
    "license",
    "meter",
]
WORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in US_WORDS) + r")\b", re.IGNORECASE
)


def scan_file(path: Path):
    """Scan a Python file for US-English words in string literals."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        # Can't read this file as text or I/O error — skip it
        return []
    results = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        # Python 3.8+: ast.Constant used for strings; earlier versions use ast.Str
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            m = WORD_RE.search(s)
            if m:
                results.append((node.lineno, s.strip()))
        elif isinstance(node, ast.JoinedStr):  # f-string
            # join the parts that are Str/Constant
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif isinstance(value, ast.Str):
                    parts.append(value.s)
            s = " ".join(parts)
            m = WORD_RE.search(s)
            if m:
                results.append((node.lineno, s.strip()))
        elif isinstance(node, ast.Str):  # older AST node
            s = node.s
            m = WORD_RE.search(s)
            if m:
                results.append((node.lineno, s.strip()))
    return results


def find_files(root: Path):
    """Yield Python files under root while skipping common ignored folders."""
    for p in root.rglob("*.py"):
        if any(
            part
            in {
                ".venv",
                "venv",
                "site-packages",
                "node_modules",
                "site",
                "exports",
                ".git",
            }
            for part in p.parts
        ):
            continue
        yield p


def main(argv):
    """CLI entrypoint: scan the repository and print findings.

    argv is unused; present to match typical CLI signatures.
    """
    _ = argv  # accepted but intentionally unused
    repo = Path(".").resolve()
    summary = {}
    for p in find_files(repo):
        res = scan_file(p)
        if res:
            summary[p] = res
    if not summary:
        print("No US-spelling occurrences found in string literals.")
        return 0
    for f, items in summary.items():
        print(f"\n{f}:")
        for lineno, text in items:
            print(f"  line {lineno}: {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
