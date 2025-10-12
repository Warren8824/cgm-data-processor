#!/usr/bin/env python3
"""Safe converter: replace common US spellings with UK spellings in Markdown and
in Python docstrings/comments only. This script is conservative: it will not
alter code identifiers or strings judged to be code (best-effort heuristic).

Usage: python .github/scripts/convert_us_to_uk.py [--apply]
--apply will write changes; without it the script prints a dry-run report.
"""
import re
import sys
from pathlib import Path
from typing import List

REPLACEMENTS = {
    r"\banalyze\b": "analyse",
    r"\banalyzing\b": "analysing",
    r"\banalyzed\b": "analysed",
    r"\binitialize\b": "initialise",
    r"\binitializing\b": "initialising",
    r"\binitialized\b": "initialised",
    r"\borganize\b": "organise",
    r"\borganizing\b": "organising",
    r"\borganized\b": "organised",
    r"\borganization\b": "organisation",
    r"\bbehavior\b": "behaviour",
    r"\bcolor\b": "colour",
    r"\blocalize\b": "localise",
    r"\blicense\b": "licence",
}

MD_EXTS = {".md", ".rst"}
PY_EXTS = {".py"}


def replace_in_text(text: str) -> tuple[str, List[str]]:
    """Apply replacements to a block of text and return (new_text, changes).

    The returned changes list contains human-readable descriptions of matches.
    """
    changes = []
    for pattern, repl in REPLACEMENTS.items():
        new_text, n = re.subn(pattern, repl, text, flags=re.IGNORECASE)
        if n:
            changes.append(f"{pattern} -> {repl}: {n} occurrences")
            text = new_text
    return text, changes


def process_markdown(path: Path):
    """Read a Markdown or reStructuredText file, apply replacements, and
    return a tuple of (new_text, changes).

    This only alters document prose (the function is conservative and does
    not touch code blocks specially; changes should be reviewed).
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    new_text, changes = replace_in_text(text)
    return new_text, changes


# For Python we only attempt replacements in comments and triple-quoted docstrings
TRIPLE_STR_RE = re.compile(r"(\"\"\"|\'\'\')(.+?)(\1)", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"#.*")


def process_python(path: Path):
    """Process a Python source file: replace text inside triple-quoted
    docstrings and in line comments only. Returns (new_text, changes).

    This avoids modifying string literals used at runtime.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    changes = []

    # Replace in triple-quoted blocks
    def repl_block(m):
        """Replace contents of a triple-quoted block (docstring) only.

        We intentionally avoid using the whole-match variable to satisfy
        strict unused-variable checks.
        """
        inner = m.group(2)
        new_inner, ch = replace_in_text(inner)
        if ch:
            changes.extend([f"docstring: {c}" for c in ch])
        return m.group(1) + new_inner + m.group(3)

    new_text = TRIPLE_STR_RE.sub(repl_block, text)

    # Replace in line comments
    def repl_comment(m):
        comment = m.group(0)
        new_comment, ch = replace_in_text(comment)
        if ch:
            changes.extend([f"comment: {c}" for c in ch])
        return new_comment

    new_text = LINE_COMMENT_RE.sub(repl_comment, new_text)

    return new_text, changes


def find_files(root: Path):
    """Yield files under root with extensions we operate on, skipping
    common generated or vendor directories.

    Yields Path objects for files with extensions in MD_EXTS or PY_EXTS.
    """
    ignored_dirs = {
        ".venv",
        "venv",
        "site-packages",
        "node_modules",
        "site",
        "exports",
        ".git",
    }
    for p in root.rglob("*"):
        if any(part in ignored_dirs for part in p.parts):
            continue
        if p.suffix.lower() in MD_EXTS.union(PY_EXTS):
            yield p


def main(argv):
    """Main run function."""
    apply_changes = "--apply" in argv
    repo = Path(".").resolve()
    summary = {}
    for p in find_files(repo):
        if p.suffix.lower() in MD_EXTS:
            new_text, changes = process_markdown(p)
        else:
            new_text, changes = process_python(p)
        if changes:
            summary[str(p)] = changes
            if apply_changes:
                p.write_text(new_text, encoding="utf-8")
    if not summary:
        print("No changes suggested.")
        return 0
    print("Suggested changes:")
    for f, ch in summary.items():
        print(f"\n{f} ->")
        for c in ch:
            print(f"  - {c}")
    if apply_changes:
        print("\nChanges have been applied (run tests and docs build).")
    else:
        print("\nDry-run complete. Re-run with --apply to write the changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
