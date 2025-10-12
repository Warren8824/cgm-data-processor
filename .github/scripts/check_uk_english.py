#!/usr/bin/env python3
"""Pre-commit hook: check for US English words in staged files (md/py/rst).

This script runs as a conservative check: it scans the file contents for a list
of common US-English spellings and exits non-zero if any are found. It is
intended as a passive guard and lists occurrences for the committer to review.

It does NOT modify files.
"""
import re
import sys
from pathlib import Path

US_WORDS = {
    "analyze": "analyse",
    "analyzing": "analysing",
    "analyzed": "analysed",
    "initialize": "initialise",
    "initializing": "initialising",
    "initialized": "initialised",
    "organize": "organise",
    "organizing": "organising",
    "organized": "organised",
    "organization": "organisation",
    "behavior": "behaviour",
    "color": "colour",
    "localize": "localise",
}

WORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in US_WORDS) + r")\b",
    re.IGNORECASE,
)


def scan_file(path: Path) -> list:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = []
    for m in WORD_RE.finditer(text):
        orig = m.group(0)
        lower = orig.lower()
        matches.append((m.start(), orig, US_WORDS.get(lower, "")))
    return matches


def main(argv):
    """CLI entrypoint.

    argv is expected to be sys.argv (not used directly beyond presence check).
    Returns 1 when any matches are found so pre-commit can fail.
    """
    if len(argv) <= 1:
        print("No files provided to check-uk-english.py")
        return 0

    had = False
    for f in argv[1:]:
        p = Path(f)
        if not p.exists():
            continue
        if p.suffix.lower() not in (".md", ".py", ".rst"):
            continue
        matches = scan_file(p)
        if matches:
            had = True
            print(f"\n{p}:")
            for pos, orig, suggestion in matches:
                print(f"  pos {pos}: '{orig}' -> prefer '{suggestion}'")

    if had:
        print(
            "\nPlease review the occurrences above. If these are false positives, you can ignore them or update the pre-commit config."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
