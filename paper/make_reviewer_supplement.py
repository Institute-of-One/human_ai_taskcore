"""Build the blinded candidate registries offered to reviewers.

    python paper/make_reviewer_supplement.py   # -> paper/build/reviewer_supplement/

Section 4.1.2 names ``data/h2_studies.json`` and ``data/h2_studies_v2.json`` as the
record of every candidate screened and the criterion each one failed. A reader of
the published paper reaches them through the repository. A reviewer cannot: Medical
Physics has been double-anonymised since 1 July 2026 and the repository URL names
the author, so the manuscript withholds it. These files close that gap.

Supporting material must itself be blinded, so this refuses to write a file in
which any identifying string survives. The check runs on the output, not on the
input, because a substitution that silently matched nothing is exactly the failure
worth catching.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PAPER = Path(__file__).resolve().parent
REPO = PAPER.parent
DEFAULT_OUTPUT = PAPER / "build" / "reviewer_supplement"

SOURCES = (
    REPO / "data" / "h2_studies.json",
    REPO / "data" / "h2_studies_v2.json",
)

#: Every way the author's identity is spelled anywhere in this repository. The
#: replacement is deliberately not a blank: a reviewer should see that something
#: was withheld and why, rather than read a sentence with a hole in it.
IDENTIFYING = (
    (r"Yamamoto", "the author"),
    (r"Shuji", "the author"),
    (r"LISIT(?: Co\.,? Ltd\.?)?", "[affiliation withheld]"),
    (r"Institute[ -]of[ -]One", "[affiliation withheld]"),
    (r"TexelCraft(?: O[UÜ])?", "[affiliation withheld]"),
    (r"0000-0001-9211-1071", "[ORCID withheld]"),
    (r"[\w.+-]+@lisit\.jp", "[email withheld]"),
    (r"IORN-\d+[A-Z]?", "[project code withheld]"),
)

README = """\
Supplementary material for review: candidate study registries
=============================================================

These are the two registries the manuscript refers to in Section 4.1.2 and in
Appendix A. They record every study considered for the external validation of
H2, in both campaigns, together with the criterion each excluded study failed
and the page or table each admitted value was read from.

    h2_studies.json      first campaign: the pool the paper reports
    h2_studies_v2.json   second campaign: nine candidates, none admitted

They are supplied here because the manuscript withholds the repository URL and
the archive DOI, both of which identify the author, and this is the material a
reviewer would otherwise reach through them. Strings that identify the author
have been replaced in these copies; nothing else has been altered, and the full
files are in the public repository disclosed at acceptance.

The two published papers in the pool are not redistributed, and these files
contain no imaging data of any kind.
"""


def blind(text: str) -> str:
    for pattern, replacement in IDENTIFYING:
        text = re.sub(pattern, replacement, text)
    return text


def surviving(text: str) -> list[str]:
    found = []
    for pattern, _ in IDENTIFYING:
        found.extend(re.findall(pattern, text))
    return found


def build(output: Path = DEFAULT_OUTPUT) -> int:
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for source in SOURCES:
        if not source.is_file():
            raise SystemExit(f"{source} is missing")
        blinded = blind(source.read_text(encoding="utf-8"))
        left = surviving(blinded)
        if left:
            raise SystemExit(
                f"{source.name} still names {sorted(set(left))} after blinding; "
                "the supplement was not written"
            )
        target = output / source.name
        target.write_text(blinded, encoding="utf-8", newline="\n")
        written.append(target)

    readme = output / "README.txt"
    readme.write_text(README, encoding="utf-8", newline="\n")
    written.append(readme)

    for path in written:
        print(f"wrote {path} ({path.stat().st_size // 1024} KB)")
    print(f"{len(written)} files, none carrying an identifying string")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return build(parser.parse_args(argv).output)


if __name__ == "__main__":
    raise SystemExit(main())
