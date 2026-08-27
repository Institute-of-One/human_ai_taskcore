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
#: Numbers the design fixed rather than the runs produced. A threshold frozen in
#: the pre-registration is a design constant in the same sense as the 95% band:
#: it is not read from results/, so requiring it to arrive through a placeholder
#: would be requiring a provenance it does not have. 5% is the C6 digitisation
#: tolerance, alongside 0.7 for the rank-agreement threshold.
#: 0.90 and 0.99 are the two companion f_sat fractions -- configuration, not
#: result -- but a constant that may be typed can drift from the run that used
#: it, so TestDeclaredConstantsMatchTheRuns checks them against the config.
DESIGN_CONSTANTS = (
    r"95\\%", "95%", r"0\.95", r"0\.90", r"0\.99", r"0\.7", r"5%", r"\$d'=1\$"
)
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


BIB = Path("paper/references.bib")
CITATION = re.compile(r"@([a-z][a-z0-9]*\d{2,4})\b")
BIB_KEY = re.compile(r"^@\w+\s*\{\s*([^,]+),", re.M)


class TestReferences:
    """A bibliography fails in two directions and only one of them is visible.

    A citation with no entry renders as a bare marker, which anyone would notice.
    An entry that resolves to somebody else's paper renders perfectly. The DOI
    resolution check lives in tools/check_references.py because it needs the
    network; what is asserted here is everything that does not.
    """

    def _keys(self):
        return set(BIB_KEY.findall(BIB.read_text(encoding="utf-8")))

    def _cited(self):
        return set(CITATION.findall(TEMPLATE.read_text(encoding="utf-8")))

    def test_every_citation_has_an_entry(self):
        missing = sorted(self._cited() - self._keys())
        assert not missing, f"cited with no entry in references.bib: {missing}"

    def test_every_entry_is_cited(self):
        """An uncited entry is either a citation that was dropped from the text or
        padding. Both are worth catching; neither is visible in the rendered PDF."""
        orphans = sorted(self._keys() - self._cited())
        assert not orphans, f"in references.bib but never cited: {orphans}"

    def test_no_citation_survives_into_the_rendered_text_as_prose(self):
        """Author-year written by hand does not become a reference entry, and does
        not renumber if the journal wants numeric citations."""
        rendered = RENDERED.read_text(encoding="utf-8")
        body = rendered[rendered.index("# 1. Introduction") : rendered.index("# References")]
        stray = re.findall(r"\((?:[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?)\s+(?:19|20)\d\d\)", body)
        assert not stray, f"hand-written author-year citations: {set(stray)}"

    def test_the_density_is_that_of_an_original_article(self):
        """Too few references is the signal that gets a submission reclassified as a
        note. The band is a floor to notice, not a target to pad towards."""
        rendered = RENDERED.read_text(encoding="utf-8")
        body = rendered[
            rendered.index("# 1. Introduction") : rendered.index(
                "# Data and code availability"
            )
        ]
        words = len(re.sub(r"\$[^$]*\$|[*_`]", " ", body).split())
        per_thousand = len(self._keys()) / (words / 1000)
        assert per_thousand >= 2.0, (
            f"{len(self._keys())} references over {words} words is "
            f"{per_thousand:.1f} per 1000 -- low for an original article"
        )

    def test_entries_carry_a_doi_or_declare_why_not(self):
        import importlib.util as _util

        spec = _util.spec_from_file_location("check_refs", "tools/check_references.py")
        module = _util.module_from_spec(spec)
        spec.loader.exec_module(module)
        entries = module.parse_bib(BIB.read_text(encoding="utf-8"))
        assert set(entries) == self._keys()
        for key, fields in entries.items():
            if key in module.NO_DOI_EXPECTED:
                continue
            assert fields.get("doi"), f"{key} has no DOI and is not declared exempt"

    def test_the_bibliography_is_a_citeproc_target(self):
        """pandoc fills #refs. Without the div the reference list silently vanishes
        from the built document while the manuscript still looks complete."""
        template = TEMPLATE.read_text(encoding="utf-8")
        assert "::: {#refs}" in template
        assert "bibliography: references.bib" in template


class TestAbstract:
    """The abstract is the part most often read alone and quoted alone, so the
    pairing the Discussion is held to matters more here, not less."""

    def _abstract(self):
        text = RENDERED.read_text(encoding="utf-8")
        return text[text.index("**Purpose.**") : text.index("**Keywords:**")]

    def test_the_added_band_share_is_not_quoted_without_absolute_detectability(self):
        body = " ".join(self._abstract().split())
        numbers = json.loads(NUMBERS.read_text(encoding="utf-8"))["values"]
        share = numbers["small_task_added_band_percent"]
        if str(share) not in body:
            pytest.fail("the abstract no longer quotes the added-band share")
        assert "absolute detectability is lowest" in body, (
            "the added-band share inverts when quoted alone: the abstract must "
            "carry the absolute detectability beside it"
        )
        assert str(numbers["small_task_dprime_uhrct"]) in body

    def test_it_does_not_claim_resolution_is_wasted(self):
        body = " ".join(self._abstract().split()).lower()
        assert "never lowers" in body
        for forbidden in ("resolution is wasted", "resolution is unnecessary"):
            assert forbidden not in body

    def test_it_states_the_ct_narrowing(self, sources):
        assert sources["h2"]["generality_narrowed_to_ct"] is True
        assert "CT" in self._abstract()

    def test_it_keeps_the_discordant_study_visible(self):
        body = " ".join(self._abstract().split()).lower()
        assert "discordant study is retained" in body

    def test_no_todo_markers_survive(self):
        assert "TODO" not in self._abstract()


class TestLimitations:
    """The introduction to Limitations makes claims about the rest of the paper --
    which entries are bold, and that Section 5 carries the scope statement it says
    was bounded. A cross-reference to text that does not exist is the failure mode
    this guards, because it reads as true right up until a reader looks."""

    def _limitations(self):
        text = RENDERED.read_text(encoding="utf-8")
        return text[text.index("# 6. Limitations") : text.index("# 7. Conclusion")]

    def test_exactly_two_entries_are_marked_as_the_binding_ones(self):
        bold = re.findall(r"^- \*\*(.*?)\*\*", self._limitations(), re.M)
        assert len(bold) == 2, (
            "the introduction says two entries bound the work more than the rest; "
            f"the list marks {len(bold)}: {bold}"
        )
        joined = " ".join(bold).lower()
        assert "ct only" in joined and "anatomic noise" in joined

    def test_the_two_are_one_of_each_kind(self):
        body = " ".join(self._limitations().split())
        assert "a limit on the evidence" in body
        assert "a limit on the formulation" in body

    def test_the_section_5_scope_statement_it_points_at_exists(self):
        text = RENDERED.read_text(encoding="utf-8")
        discussion = " ".join(
            text[text.index("# 5. Discussion") : text.index("# 6. Limitations")].split()
        )
        assert "anatomic" in discussion.lower(), (
            "Limitations says the anatomic-noise bound narrowed the scope "
            "statement in Section 5; Section 5 does not make one"
        )
        assert "quantum and neural" in discussion


class TestDeclaredConstantsMatchTheRuns:
    """A design constant is exempt from the placeholder rule, which means the one
    class of number in this manuscript that no build step verifies. Where the
    constant is also recorded in a run's configuration, check it there."""

    def test_the_f_sat_fractions_named_in_the_text_are_the_ones_computed(
        self, sources
    ):
        recorded = sources["phase1"]["metadata"]["config"]["fractions"]
        theory = RENDERED.read_text(encoding="utf-8")
        theory = theory[theory.index("# 2. Theory") : theory.index("# 3. Methods")]
        named = {float(m) for m in re.findall(r"0\.9\d", theory)}
        assert named == set(recorded), (
            f"Theory names f_sat fractions {sorted(named)}; the run computed "
            f"{sorted(recorded)}"
        )

    def test_the_primary_fraction_is_the_one_the_results_use(self, sources):
        assert 0.95 in sources["phase1"]["metadata"]["config"]["fractions"]


class TestDiscussionScope:
    """The Discussion was written against a list of claims it was allowed to make.

    The list is the thing that keeps the section from drifting into what the results
    do not support, and a list that only ever lived in a TODO comment stops working
    the moment the TODO is replaced by prose. These assert the boundaries directly.
    """

    def _discussion(self):
        text = Path("paper/manuscript.md").read_text(encoding="utf-8")
        start = text.index("# 5. Discussion")
        return text[start : text.index("# 6. Limitations")]

    def test_it_disclaims_diagnosis(self):
        body = " ".join(self._discussion().split())
        assert "detection is not diagnosis" in body, (
            "the model addresses detection; the section must say it does not "
            "address diagnosis"
        )

    def test_it_does_not_argue_that_resolution_is_wasted(self):
        body = " ".join(self._discussion().split()).lower()
        assert "sharper reconstruction never hurts" in body
        for forbidden in (
            "resolution is wasted",
            "resolution is unnecessary",
            "no benefit from higher resolution",
        ):
            assert forbidden not in body, f"out-of-scope claim: {forbidden!r}"

    def test_it_pairs_the_added_band_with_absolute_detectability(self):
        """The one number in this paper that inverts if quoted alone."""
        body = " ".join(self._discussion().split())
        assert "absolute detectability beside the relative gain" in body

    def test_it_offers_sufficiency_and_not_an_optimum(self):
        body = " ".join(self._discussion().split()).lower()
        assert "no interior optimum" in body
        assert "is enough for this task" in body
        assert "optimal magnification" not in body

    def test_it_keeps_the_validation_to_ordering(self):
        body = " ".join(self._discussion().split()).lower()
        assert "does not establish that the absolute detectability is calibrated" in body


class TestMethodsMatchTheImplementation:
    """Methods describes what the code does. Where it states a fact about the runs,
    the fact is checked against the recorded configuration rather than trusted."""

    def _methods(self):
        text = RENDERED.read_text(encoding="utf-8")
        return text[text.index("# 3. Methods") : text.index("# 4. Results")]

    def test_the_condition_set_is_the_full_factorial_it_claims(self, sources):
        config = sources["phase1"]["metadata"]["config"]
        product = 1
        for axis in (
            "diameters_mm",
            "contrasts_hu",
            "doses_relative",
            "slice_thicknesses_mm",
            "kernels",
            "zooms",
        ):
            product *= len(config[axis])
        assert product == sources["phase1"]["metadata"]["n_conditions"], (
            "Methods calls the condition set a full factorial over six axes; the "
            f"axes multiply to {product} and the run recorded "
            f"{sources['phase1']['metadata']['n_conditions']}"
        )
        assert "full factorial over six axes" in " ".join(self._methods().split())

    def test_the_h1_rule_in_the_text_is_the_rule_the_run_applied(self, sources):
        recorded = sources["uncertainty"]["metadata"]["h1_rule"]
        body = " ".join(self._methods().split())
        assert "lower bound of the 95% band" in body
        assert "lower bound of the 95% band" in recorded, (
            "the run records a different H1 rule than the manuscript states"
        )

    def test_the_h2_threshold_in_the_text_is_the_frozen_one(self, sources):
        assert sources["h2"]["success_threshold_rho"] == 0.7
        assert r"\rho \ge 0.7" in self._methods()

    def test_the_propagation_pairing_claim_is_stated(self):
        """The pairing is the part of the design a reader cannot see in a number."""
        body = " ".join(self._methods().split())
        assert "held fixed across the dose axis" in body

    def test_the_superseded_form_is_disclosed(self, sources):
        """The code carries an earlier detectability form. Methods has to say so, or
        a reader checking an intermediate value against the older draft concludes the
        implementation is broken."""
        assert "superseded" in sources["phase1"]["metadata"]["detectability_form"]
        assert "superseded" in " ".join(self._methods().split())
