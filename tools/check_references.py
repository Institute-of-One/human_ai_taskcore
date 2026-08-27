"""Resolve every DOI in paper/references.bib and compare what it returns.

A wrong DOI is invisible in a manuscript and obvious to a reviewer, and a DOI
typed from memory resolves to somebody else's paper rather than to nothing --
which is the failure that a spot check misses. This asks doi.org for each one
and prints the title it resolves to, so that the comparison is with the actual
registered record rather than with the entry that produced it.

Usage::

    python tools/check_references.py            # resolve and compare
    python tools/check_references.py --offline  # structure only, no network

Exit status is non-zero if any DOI fails to resolve or returns a title that does
not match the entry.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper" / "references.bib"

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)
FIELD = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*(?:,|\s*$)", re.S)

#: Entries that legitimately carry no DOI: standards and reports that were never
#: registered with one. Listed here so that a missing DOI is a decision rather
#: than an omission nobody noticed.
NO_DOI_EXPECTED = {"dicomps314", "icrp87"}


def _normalise(text: str) -> str:
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for _kind, key, body in ENTRY.findall(text):
        fields = {}
        for name, value in FIELD.findall(body):
            fields[name.lower()] = re.sub(r"\s+", " ", value).strip()
        entries[key.strip()] = fields
    return entries


def resolve(doi: str) -> dict:
    request = urllib.request.Request(
        f"https://doi.org/{doi}",
        headers={
            "Accept": "application/vnd.citationstyles.csl+json",
            "User-Agent": "IORN-009A reference check (yamamoto@lisit.jp)",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    print(f"{len(entries)} entries in {BIB.relative_to(REPO)}\n")

    failures = []
    for key, fields in sorted(entries.items()):
        doi = fields.get("doi")
        if not doi:
            if key in NO_DOI_EXPECTED:
                print(f"  {key:16} no DOI (expected: standard or report)")
            else:
                print(f"  {key:16} NO DOI")
                failures.append(f"{key}: no DOI and not declared as expecting none")
            continue
        if args.offline:
            print(f"  {key:16} {doi}")
            continue

        try:
            record = resolve(doi)
        except urllib.error.HTTPError as error:
            print(f"  {key:16} UNRESOLVED ({error.code})  {doi}")
            failures.append(f"{key}: {doi} does not resolve ({error.code})")
            continue
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"  {key:16} network error: {error}")
            failures.append(f"{key}: network error")
            continue

        registered = record.get("title") or ""
        if isinstance(registered, list):
            registered = registered[0]
        ours = fields.get("title", "")
        ratio = difflib.SequenceMatcher(
            None, _normalise(ours), _normalise(registered)
        ).ratio()
        year = str((record.get("issued", {}).get("date-parts") or [[None]])[0][0])
        year_ok = year == fields.get("year")

        # Crossref records for pre-1990 articles often stop at the colon, so a
        # registered title that is a prefix of ours is the same paper with its
        # subtitle dropped -- not a mismatch. Requiring a prefix rather than a
        # substring keeps this from excusing an unrelated record.
        truncated = _normalise(ours).startswith(_normalise(registered)) and len(
            _normalise(registered)
        ) >= 20

        if (ratio >= 0.85 or truncated) and year_ok:
            note = "  (registered title truncated)" if truncated and ratio < 0.85 else ""
            print(f"  {key:16} ok    {doi}{note}")
        else:
            print(f"  {key:16} MISMATCH  {doi}")
            print(f"      ours:       {ours}")
            print(f"      registered: {registered}")
            if not year_ok:
                print(f"      year: bib {fields.get('year')} vs registered {year}")
            failures.append(f"{key}: resolves to a different record")

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("\nall entries check out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
