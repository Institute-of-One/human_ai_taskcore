"""Render the built manuscript to the .docx that Medical Physics is sent.

    python paper/build_docx.py                    # -> paper/build/manuscript.docx
    python paper/build_docx.py --title-page       # -> paper/build/title_page.docx

This is a derivative. ``paper/manuscript.md`` is itself rendered from
``paper/manuscript_template.md`` by ``paper/make_figures.py``, and this reads the
rendered file, so a number cannot reach the upload without having come from
``results/``. It refuses to run if the rendered file is stale.

Two things pandoc will not do and no reference document supplies, both of which
Medical Physics returned a companion submission for wanting:

* **Continuous line numbering** down the left margin. One section property.
* **Page numbers.** A footer part carrying a PAGE field, a content-type override, a
  relationship, and a reference to it from the section: four parts, not one.

The order inside ``sectPr`` is fixed by the schema -- ``footerReference`` before
``footnotePr``, ``lnNumType`` after -- and Word rejects the part outright if they
are reversed. That is the whole reason this is written out rather than left to a
template.

References are numbered by citeproc against ``paper/references.bib`` and
``paper/style/american-medical-association.csl``, so the numbering is in order of
first citation by construction rather than by hand.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

PAPER = Path(__file__).resolve().parent
REPO = PAPER.parent
RENDERED = PAPER / "manuscript.md"
TEMPLATE = PAPER / "manuscript_template.md"
BIBLIOGRAPHY = PAPER / "references.bib"
CSL = PAPER / "style" / "american-medical-association.csl"
BUILD = PAPER / "build"
DEFAULT_OUTPUT = BUILD / "manuscript.docx"
TITLE_PAGE_OUTPUT = BUILD / "title_page.docx"

#: Medical Physics returns a submission that carries neither. Both are added here.
#: A journal whose submission system numbers the proof itself, as ScholarOne does for
#: PMB, wants LINE_NUMBERS False instead, or the reader gets two disagreeing columns.
LINE_NUMBERS = True

#: Medical Physics has been double-anonymised since 1 July 2026. Its de-identifying
#: checklist names the author's own file metadata as a place identity leaks, and
#: pandoc writes ``dc:creator`` from the operating system regardless of what the
#: document says. Nothing in the manuscript text carries the name -- the front
#: matter no longer declares an author, because identity belongs on the title page
#: and only there -- so this is the last place it could survive.
ANONYMOUS = True

#: "The running text should be spaced at 1.5 lines (vertically)." Word stores that
#: as twentieths of a point: 1.5 x 12pt = 18pt = 360.
LINE_SPACING_TWIPS = 360

_FOOTER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    "<w:r><w:t>1</w:t></w:r>"
    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    "</w:p></w:ftr>"
)
_FOOTER_PART = "word/footer1.xml"
_FOOTER_RELATIONSHIP = "rIdPageFooter"
_FOOTER_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
)

#: Every line, never restarting; ``distance`` is twentieths of a point, so 360 puts the
#: numbers a quarter inch clear of the text.
_LINE_NUMBERING = '<w:lnNumType w:countBy="1" w:restart="continuous" w:distance="360"/>'


def number_pages_and_lines(path: Path, line_numbers: bool = LINE_NUMBERS) -> Path:
    """Add page numbers, and line numbering where the journal asks for it."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        contents = {name: archive.read(name) for name in names}

    # The footer is added in every case, so its presence, and not the optional line
    # numbering, is what says the furniture is already in place.
    if _FOOTER_PART in names:
        return path

    document = contents["word/document.xml"].decode("utf-8")
    reference = f'<w:footerReference w:type="default" r:id="{_FOOTER_RELATIONSHIP}"/>'
    if "<w:sectPr>" not in document:
        raise SystemExit("the .docx has no section properties to attach the footer to")
    document = document.replace("<w:sectPr>", f"<w:sectPr>{reference}", 1)
    if line_numbers:
        if "</w:footnotePr>" in document:
            document = document.replace(
                "</w:footnotePr>", f"</w:footnotePr>{_LINE_NUMBERING}", 1
            )
        else:
            # No footnote properties in this document; the schema puts lnNumType
            # immediately after where they would have been, which is after the
            # footerReference just inserted.
            document = document.replace(reference, f"{reference}{_LINE_NUMBERING}", 1)
    contents["word/document.xml"] = document.encode("utf-8")

    rels = contents["word/_rels/document.xml.rels"].decode("utf-8")
    relationship = (
        f'<Relationship Id="{_FOOTER_RELATIONSHIP}" Type="http://schemas.openxmlformats'
        '.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
    )
    rels = rels.replace("</Relationships>", f"{relationship}</Relationships>", 1)
    contents["word/_rels/document.xml.rels"] = rels.encode("utf-8")

    types = contents["[Content_Types].xml"].decode("utf-8")
    override = f'<Override PartName="/{_FOOTER_PART}" ContentType="{_FOOTER_TYPE}"/>'
    types = types.replace("</Types>", f"{override}</Types>", 1)
    contents["[Content_Types].xml"] = types.encode("utf-8")

    contents[_FOOTER_PART] = _FOOTER_XML.encode("utf-8")

    temporary = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in [*names, _FOOTER_PART]:
            archive.writestr(name, contents[name])
    shutil.move(str(temporary), str(path))
    return path


def _refuse_if_stale() -> None:
    """The upload must not be built from a rendered file the template has outrun.

    Rendered afresh into a temporary file and compared, which is what
    tests/test_paper.py does; a difference means paper/make_figures.py has not been
    run since the template changed.
    """
    import json  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    sys.path.insert(0, str(PAPER))
    import make_figures  # noqa: PLC0415

    sources = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in make_figures.RESULTS.items()
    }
    numbers = make_figures.collect_numbers(sources)
    with tempfile.TemporaryDirectory() as directory:
        fresh = Path(directory) / "manuscript.md"
        make_figures.render_manuscript(TEMPLATE, numbers, fresh)
        if fresh.read_text(encoding="utf-8") != RENDERED.read_text(encoding="utf-8"):
            raise SystemExit(
                "paper/manuscript.md is out of date with the template; "
                "run paper/make_figures.py first"
            )


def _rewrite_part(path: Path, part: str, transform) -> None:
    """Replace one part of a .docx in place, leaving every other part byte-identical."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        parts = {name: archive.read(name) for name in names}
    if part not in parts:
        raise SystemExit(f"{path.name} has no {part}")
    parts[part] = transform(parts[part].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, parts[name])


def set_line_spacing(path: Path, twips: int = LINE_SPACING_TWIPS) -> Path:
    """Space the running text at 1.5 lines, as the journal's file rules require."""

    def transform(styles: str) -> str:
        default = '<w:pPr>\n        <w:spacing w:after="200" />\n      </w:pPr>'
        spaced = (
            '<w:pPr><w:spacing w:after="200" '
            f'w:line="{twips}" w:lineRule="auto"/></w:pPr>'
        )
        if default not in styles:
            raise SystemExit(
                "the default paragraph properties are not where they were; "
                "line spacing would have been set on nothing"
            )
        return styles.replace(default, spaced, 1)

    _rewrite_part(path, "word/styles.xml", transform)
    return path


def strip_authorship_metadata(path: Path) -> Path:
    """Empty the document properties that name the author.

    Word and pandoc both fill ``dc:creator`` from the account that produced the
    file. A reviewer sees it under File > Properties without opening anything, so
    an anonymised manuscript that still carries it is not anonymised.
    """
    import re  # noqa: PLC0415

    def transform(core: str) -> str:
        for tag in ("dc:creator", "cp:lastModifiedBy"):
            core = re.sub(f"<{tag}>[^<]*</{tag}>", f"<{tag}></{tag}>", core)
        return core

    _rewrite_part(path, "docProps/core.xml", transform)
    return path


def build(output: Path = DEFAULT_OUTPUT, line_numbers: bool = LINE_NUMBERS) -> int:
    import pypandoc  # noqa: PLC0415

    _refuse_if_stale()
    output.parent.mkdir(parents=True, exist_ok=True)
    pypandoc.convert_file(
        str(RENDERED),
        to="docx",
        format="markdown+implicit_figures",
        outputfile=str(output),
        extra_args=[
            "--citeproc",
            f"--bibliography={BIBLIOGRAPHY}",
            f"--csl={CSL}",
            f"--resource-path={PAPER}",
        ],
    )
    number_pages_and_lines(output, line_numbers=line_numbers)
    set_line_spacing(output)
    if ANONYMOUS:
        strip_authorship_metadata(output)
    print(f"wrote {output} ({output.stat().st_size // 1024} KB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--no-line-numbers",
        action="store_true",
        help="omit line numbering, for a journal whose system numbers the proof itself",
    )
    args = parser.parse_args(argv)
    return build(args.output, line_numbers=not args.no_line_numbers)


if __name__ == "__main__":
    raise SystemExit(main())
