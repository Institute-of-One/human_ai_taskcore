"""Design principle no. 2: no hand-typed numbers in the manuscript."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "make_figures", Path("paper/make_figures.py")
)
make_figures = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(make_figures)

TEMPLATE = Path("paper/manuscript_template.md")
RENDERED = Path("paper/manuscript.md")
NUMBERS = Path("paper/numbers.json")

# Numbers fixed by the protocol rather than measured may be typed: the band
# coverage, H2's rank threshold and the f_sat definition's fraction.
DESIGN_CONSTANTS = (r"95\\%", "95%", r"0\.95", r"0\.7", r"\$d'=1\$")
STRUCTURAL = (
    (re.compile(r"Section \d+(\.\d+)?"), "Section"),
    (re.compile(r"PS3\.14"), "PS"),
    (re.compile(r"\^\{?\d\}?"), ""),            # exponents in math
    (re.compile(r"H[123]\b"), "H"),
    (re.compile(r"fig\d[a-z0-9_]*\.png"), "figure.png"),
    (re.compile(r"(19|20)\d\d"), "year"),        # citation years
)
HEADING_OR_FRONT_MATTER = re.compile(r"^(#{1,3}\s|---$|[a-z_]+:\s)")
# what a hand-typed *result* looks like: a decimal, a number with a unit, or a
# count of conditions
RESULT_LITERAL = re.compile(
    r"\d+\.\d+|\d+(\.\d+)?\s*(lp/mm|mm|%|cd/m|HU)|\b\d{3,}\b"
)


@pytest.fixture(scope="module")
def sources():
    return {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in make_figures.RESULTS.items()
    }


class TestNumbers:
    def test_every_quantity_carries_its_provenance(self, sources):
        numbers = make_figures.collect_numbers(sources)
        assert set(numbers.values) == set(numbers.provenance)
        for key, origin in numbers.provenance.items():
            assert origin.startswith("results/") or origin.startswith(
                "derived by"
            ), key

    def test_read_quantities_point_at_a_real_path(self, sources):
        numbers = make_figures.collect_numbers(sources)
        for key, origin in numbers.provenance.items():
            if origin.startswith("derived by"):
                continue
            source, path = origin.split(":", 1)
            name = next(
                n for n, p in make_figures.RESULTS.items()
                if p.as_posix() == source
            )
            make_figures._dig(sources[name], path)  # raises if it moved

    def test_the_committed_numbers_file_matches_the_results(self, sources):
        numbers = make_figures.collect_numbers(sources)
        committed = json.loads(NUMBERS.read_text(encoding="utf-8"))
        assert committed == numbers.payload(), (
            "paper/numbers.json is stale: re-run paper/make_figures.py"
        )


class TestTemplate:
    def test_every_placeholder_resolves(self, sources):
        numbers = make_figures.collect_numbers(sources)
        asked = set(
            make_figures.PLACEHOLDER.findall(
                TEMPLATE.read_text(encoding="utf-8")
            )
        )
        assert asked <= set(numbers.values)
        assert asked, "the template should quote results, not nothing"

    def test_the_rendered_manuscript_has_no_placeholders_left(self):
        rendered = RENDERED.read_text(encoding="utf-8")
        assert not make_figures.PLACEHOLDER.search(rendered)

    def test_the_rendered_manuscript_is_current(self, sources, tmp_path):
        numbers = make_figures.collect_numbers(sources)
        out = tmp_path / "manuscript.md"
        make_figures.render_manuscript(TEMPLATE, numbers, out)
        assert out.read_text(encoding="utf-8") == RENDERED.read_text(
            encoding="utf-8"
        ), "paper/manuscript.md is stale: re-run paper/make_figures.py"

    def test_no_hand_typed_results_in_the_template(self):
        offenders = []
        for line_number, line in enumerate(
            TEMPLATE.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if HEADING_OR_FRONT_MATTER.match(line):
                continue
            stripped = make_figures.PLACEHOLDER.sub("X", line)
            for pattern, replacement in STRUCTURAL:
                stripped = pattern.sub(replacement, stripped)
            for constant in DESIGN_CONSTANTS:
                stripped = re.sub(constant, "", stripped)
            if RESULT_LITERAL.search(stripped):
                offenders.append(f"{line_number}: {line.strip()}")
        assert not offenders, (
            "results must come from results/*.json through a {{placeholder}}:\n"
            + "\n".join(offenders)
        )

    def test_the_guard_would_catch_a_hand_typed_result(self):
        # the check above is only worth having if it fails on the thing it is
        # meant to stop
        smuggled = "the median was 0.335 lp/mm across conditions"
        stripped = make_figures.PLACEHOLDER.sub("X", smuggled)
        assert RESULT_LITERAL.search(stripped)
        proper = "the median was {{f_sat_median_lpmm}} lp/mm across conditions"
        assert not RESULT_LITERAL.search(
            make_figures.PLACEHOLDER.sub("X", proper)
        )

    def test_the_pandoc_trap_is_not_reintroduced(self):
        # implicit_figures turns alt text into a duplicate caption; the images
        # here carry their captions in the alt text on purpose
        template = TEMPLATE.read_text(encoding="utf-8")
        for match in re.finditer(r"!\[(.*?)\]\((.*?)\)", template, re.S):
            assert match.group(1).strip(), (
                f"figure {match.group(2)} has no caption in its alt text"
            )


class TestFigures:
    def test_every_figure_exists_and_is_referenced(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        figures = sorted(Path("paper/figures").glob("fig*.png"))
        assert len(figures) == 6
        for figure in figures:
            assert figure.stat().st_size > 0
            assert f"figures/{figure.name}" in template
