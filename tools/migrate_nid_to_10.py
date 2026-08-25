"""
One-off migration helper: rewrite the seeded 11-digit NIDs to Nepal's official
10-digit NIN, and refresh the surrounding prose.

Mapping rule (uniform, deterministic, documented in every seed file):
    new_NIN = old_11_digit_NID with its LEADING digit dropped
              i.e. new = old[1:]   ->  12345678901 -> 2345678901

Every seeded NID starts with '1', so the result is always exactly 10 digits and
stays collision-free because the patients differ in their trailing digits. This
preserves the cross-service "...901 / 902 / 903 MUST match" pairings, which now
read as "...901 -> 2345678901" everywhere.

Run once from the repo root:  python tools/migrate_nid_to_10.py
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Files that carry NID literals and/or 11-digit prose.
TARGETS = [
    "national-platform/core/management/commands/bootstrap.py",
    "national-platform/core/tests.py",
    "mediciti-hospital/clinical/management/commands/seed.py",
    "norvic-hospital/clinical/management/commands/seed.py",
    "central-diagnostic-lab/lab/management/commands/seed.py",
    "pathlabs-nepal/lab/management/commands/seed.py",
    "swastha-ehr/backend/core/management/commands/seed_demo.py",
    "swastha-ehr/backend/core/test_nid.py",
    "README.md",
    "seed-all.sh",
    "data-access-guide.md",
    "demo.md",
]

# NID literals: drop the leading '1' from every 1234567890X / 12345678910.
NID_PATTERN = re.compile(r"\b1(2345678\d{3})\b")
# The unit-test placeholder NID used by national-platform/core/tests.py.
TEST_NID_PATTERN = re.compile(r"\b11112222333\b")

PROSE = [
    ("11-digit Nepal NIN", "10-digit Nepal NIN"),
    ("11-digit NIN", "10-digit NIN"),
    ("11-digit", "10-digit"),
    ("an 11-digit", "a 10-digit"),
    ("exactly 11 digits", "exactly 10 digits"),
    ("exactly 11 numeric digits", "exactly 10 numeric digits"),
    ("11 digits", "10 digits"),
    ("(12345678901, 02, 03)", "(2345678901, 02, 03)"),
]


def main():
    for rel in TARGETS:
        path = REPO / rel
        if not path.exists():
            print(f"skip (missing): {rel}")
            continue
        original = path.read_text(encoding="utf-8")
        text = NID_PATTERN.sub(r"\1", original)
        text = TEST_NID_PATTERN.sub("1112222333", text)
        for old, new in PROSE:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"rewritten: {rel}")
        else:
            print(f"unchanged: {rel}")


if __name__ == "__main__":
    main()
