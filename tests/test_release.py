"""Release identity, and the one claim in the paper a reader can check for himself.

The availability statement tells a reader to run ``git merge-base --is-ancestor``
on two commits to confirm that the H2 inclusion criteria were frozen before the
literature search. That instruction is worth only as much as the commits are: if
either SHA is wrong, or the ancestry does not hold, the paper has invited a check
it fails. So the check the paper offers is run here against this repository.
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

RELEASE = Path("results/release.json")

SPEC = importlib.util.spec_from_file_location(
    "presubmission_check", Path("tools/presubmission_check.py")
)
presubmission = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(presubmission)


@pytest.fixture(scope="module")
def release():
    return json.loads(RELEASE.read_text(encoding="utf-8"))


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


class TestTheFreezeIsCheckable:
    def test_both_commits_exist(self, release):
        for field in ("h2_criteria_frozen_commit", "h2_first_search_commit"):
            sha = release[field]
            assert not _git("cat-file", "-e", f"{sha}^{{commit}}").returncode, (
                f"{field} {sha[:7]} is not a commit in this repository"
            )

    def test_the_freeze_precedes_the_search(self, release):
        """The exact command the availability statement asks a reader to run."""
        frozen = release["h2_criteria_frozen_commit"]
        search = release["h2_first_search_commit"]
        assert not _git("merge-base", "--is-ancestor", frozen, search).returncode, (
            "the paper claims the criteria were frozen before the literature "
            "search, and the recorded commits do not bear that out"
        )

    def test_the_recorded_timestamps_are_the_commits_own(self, release):
        for sha_field, time_field in (
            ("h2_criteria_frozen_commit", "h2_criteria_frozen_at"),
            ("h2_first_search_commit", "h2_first_search_at"),
        ):
            recorded = _git(
                "log", "-1", "--format=%aI", release[sha_field]
            ).stdout.strip()
            assert recorded == release[time_field], (
                f"{time_field} says {release[time_field]}, git says {recorded}"
            )

    def test_the_commits_are_different(self, release):
        assert (
            release["h2_criteria_frozen_commit"] != release["h2_first_search_commit"]
        )


class TestUnsetFieldsCannotPassAsValues:
    """A release tag and a version DOI do not exist until the release is cut. The
    build renders them, so the question is only whether an unfilled one can reach
    a document that looks finished."""

    def test_the_manuscript_shows_unset_fields_loudly(self, release):
        rendered = Path("paper/manuscript.md").read_text(encoding="utf-8")
        for field in presubmission.REQUIRED_RELEASE_FIELDS:
            if release.get(field) is None:
                assert f"[UNSET: {field}" in rendered, (
                    f"{field} is unset but the manuscript does not say so"
                )

    def test_the_presubmission_check_refuses_while_anything_is_unset(self, release):
        unset = [f for f in presubmission.REQUIRED_RELEASE_FIELDS if release.get(f) is None]
        problems = presubmission.check()
        if unset:
            assert problems, (
                f"{unset} are unset and the check passed anyway"
            )
            for field in unset:
                assert any(field in problem for problem in problems), field

    def test_the_check_names_a_tag_that_points_somewhere_else(self, tmp_path):
        """The defect an unset field cannot produce: a tag typed in by hand that
        was never cut, or cut against a different commit."""
        head = _git("rev-parse", "HEAD").stdout.strip()
        payload = json.loads(RELEASE.read_text(encoding="utf-8"))
        payload.update(
            version_tag="v0.0.0-not-cut",
            release_commit=head,
            zenodo_version_doi="10.5281/zenodo.0000000",
        )
        backup = RELEASE.read_text(encoding="utf-8")
        RELEASE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        try:
            problems = presubmission.check()
        finally:
            RELEASE.write_text(backup, encoding="utf-8")
        assert any("v0.0.0-not-cut" in problem for problem in problems), problems


class TestReadmeMatchesTheResults:
    """A release freezes whatever the repository says, README included.

    The manuscript cannot carry a hand-typed number, but the README can, and it is
    the first thing a reader arriving from the archived DOI sees. These check the
    claims it makes against the run they describe.
    """

    def _readme(self):
        return Path("README.md").read_text(encoding="utf-8")

    def _h2(self):
        return json.loads(Path("results/h2.json").read_text(encoding="utf-8"))

    def test_every_correlation_it_quotes_is_the_one_that_was_computed(self):
        h2 = self._h2()
        readme = self._readme()
        for study_id, value in h2["per_study"].items():
            quoted = f"{value['spearman_rho']:+.3f}"
            assert quoted in readme, (
                f"README does not quote {study_id}'s correlation {quoted}"
            )
        pooled = f"{h2['pools']['v1_2']['pooled_rho']:+.3f}"
        assert pooled in readme, f"README does not quote the pooled {pooled}"
        assert str(h2["success_threshold_rho"]) in readme

    def test_it_reports_the_same_count_as_the_run(self):
        h2 = self._h2()
        meeting = sum(1 for v in h2["per_study"].values() if v["meets_threshold"])
        total = len(h2["per_study"])
        assert (meeting, total) == (2, 3), (
            "the README says two of the three studies meet the threshold; the run "
            f"says {meeting} of {total}"
        )

    def test_it_states_the_ct_narrowing_rather_than_the_general_claim(self):
        assert self._h2()["generality_narrowed_to_ct"] is True
        body = " ".join(self._readme().split())
        assert "generality claim narrows to CT" in body
        assert "validated here on CT alone" in body

    def test_it_does_not_still_describe_h2_as_outstanding(self):
        """The state the repository was in while the work was being done, and the
        state it must not be frozen in."""
        body = " ".join(self._readme().split())
        for stale in (
            "is the remaining M3 item",
            "Milestone **M2**",
            "Milestone M2",
        ):
            assert stale not in body, f"README still says: {stale!r}"

    def test_the_ordering_command_it_prints_actually_succeeds(self):
        """The README invites the reader to run this. It has to pass."""
        import re as _re

        body = self._readme()
        match = _re.search(
            r"git merge-base --is-ancestor ([0-9a-f]{7,40}) ([0-9a-f]{7,40})", body
        )
        assert match, "the README no longer shows the ordering check"
        assert not _git("merge-base", "--is-ancestor", *match.groups()).returncode

    def test_the_documented_pandoc_call_resolves_citations(self):
        """Without --citeproc the citations render as literal markers and the
        reference list is empty, in a document that otherwise looks finished.

        Asserted against the command itself, not against the README as a whole:
        the prose below the block also says ``--citeproc``, so a whole-file search
        passes even after the flag is dropped from the command it describes.
        """
        import re as _re

        commands = [
            " ".join(block.replace("\\\n", " ").split())
            for block in _re.findall(r"```bash\n(.*?)```", self._readme(), _re.S)
            if "pandoc" in block
        ]
        assert len(commands) == 1, f"expected one pandoc command, found {len(commands)}"
        command = commands[0]
        assert "--citeproc" in command, f"pandoc call has no --citeproc: {command}"
        assert "--bibliography=paper/references.bib" in command, command
        assert "markdown-implicit_figures" in command, command

    def test_it_does_not_point_at_files_that_are_not_there(self):
        """The README used to pass --reference-doc=paper/reference.docx, which does
        not exist in this repository.

        Only inputs are checked. A path the documented command *writes* need not
        exist yet, so anything named as an ``-o`` target is excluded rather than
        the check being loosened for everything.
        """
        import re as _re

        body = self._readme()
        outputs = set(_re.findall(r"-o\s+([\w./-]+)", body))
        named = set(_re.findall(r"[\w./-]*paper/[\w./-]+\.(?:docx|bib|py|md)", body))
        for path in sorted(named - outputs):
            assert Path(path).exists(), f"README names a file that is not here: {path}"


class TestTheDoiGuidanceIsRecorded:
    def test_the_file_says_which_doi_to_cite(self, release):
        """Version, not concept. The badge on the Zenodo settings page is the
        version DOI, and a paper has to pin the snapshot its numbers came from."""
        note = release["doi_note"].lower()
        assert "version doi" in note and "concept doi" in note

    def test_the_manuscript_says_the_same(self):
        rendered = " ".join(
            Path("paper/manuscript.md").read_text(encoding="utf-8").split()
        )
        section = rendered[rendered.index("Data and code availability") :]
        assert "version DOI" in section and "not the concept DOI" in section


class TestTheCitationFileAgreesWithTheRepository:
    """Zenodo reads CITATION.cff to build the archive record. A release freezes it, so
    an author name, an ORCID or a version that disagrees with the repository is minted
    into a DOI that cannot be edited afterwards."""

    def _cff(self):
        path = Path("CITATION.cff")
        if not path.is_file():
            pytest.skip("no CITATION.cff in this checkout")
        return path.read_text(encoding="utf-8")

    def test_the_version_matches_the_package(self):
        import re as _re

        declared = _re.search(r'^version = "([^"]+)"', Path("pyproject.toml").read_text(
            encoding="utf-8"
        ), _re.M)
        assert declared, "pyproject.toml declares no version"
        assert f"version: {declared.group(1)}" in self._cff(), (
            f"pyproject says {declared.group(1)}; CITATION.cff says otherwise"
        )

    def test_the_author_matches_the_title_page(self):
        """The title page, not the manuscript.

        Medical Physics has been double-anonymised since 1 July 2026, so identity
        lives on the separate title page and must be absent from the manuscript.
        This test used to require the author's name *in* the manuscript, which is
        now the defect rather than the requirement, so it asserts both directions.
        """
        cff = self._cff()
        title_page = Path("paper/make_title_page.py").read_text(encoding="utf-8")
        manuscript = Path("paper/manuscript.md").read_text(encoding="utf-8")
        for field in ("Yamamoto", "Shuji", "0000-0001-9211-1071"):
            assert field in cff, f"CITATION.cff is missing {field}"
            assert field in title_page, f"the title page is missing {field}"
            assert field not in manuscript, (
                f"the manuscript carries {field}; the review copy is anonymised"
            )

    def test_the_repository_url_is_the_one_the_paper_names(self):
        """Both fields, separately. A substring search over the whole file passes while
        one of the two points somewhere else, because the other still carries the right
        URL -- which is exactly the state a careless edit leaves behind."""
        import re as _re

        release = json.loads(Path("results/release.json").read_text(encoding="utf-8"))
        cff = self._cff()
        for field in ("repository-code", "url"):
            found = _re.search(rf"^{field}: (\S+)", cff, _re.M)
            assert found, f"CITATION.cff has no {field} field"
            assert found.group(1).rstrip("/") == release["repository"].rstrip("/"), (
                f"CITATION.cff {field} is {found.group(1)}; results/release.json says "
                f"{release['repository']}"
            )

    def test_no_doi_is_guessed_before_it_exists(self):
        """The concept DOI does not exist until the first deposit. An invented one
        resolves to somebody else's record, which is the failure that looks correct."""
        import re as _re

        cff = self._cff()
        declared = _re.findall(r"^doi: (\S+)", cff, _re.M)
        release = json.loads(Path("results/release.json").read_text(encoding="utf-8"))
        if release.get("zenodo_concept_doi") is None:
            assert not declared, (
                f"CITATION.cff carries a top-level DOI {declared} while "
                "results/release.json has no concept DOI recorded"
            )
        else:
            assert declared == [release["zenodo_concept_doi"]]

    def test_every_reference_doi_is_one_the_bibliography_verified(self):
        """These DOIs were resolved against doi.org when the manuscript bibliography was
        built. Reusing the verified strings keeps a second, unchecked copy from drifting."""
        import re as _re

        bib = Path("paper/references.bib")
        if not bib.is_file():
            pytest.skip("no bibliography in this checkout")
        verified = {
            d.lower() for d in _re.findall(r"doi\s*=\s*\{([^}]+)\}", bib.read_text(
                encoding="utf-8"
            ))
        }
        for doi in _re.findall(r"^\s+doi: (\S+)", self._cff(), _re.M):
            assert doi.lower() in verified, (
                f"CITATION.cff cites {doi}, which is not in the verified bibliography"
            )


class TestTheArchiveMetadataIsConsistent:
    """Zenodo builds the deposit from .zenodo.json when one is present. Everything it
    says is minted into a record that a DOI makes permanent, so the parts that can
    disagree with the repository are checked before a release can freeze them.

    ctsegdose-core shipped a release whose .zenodo.json still declared the previous
    version. The same file in taskiq-core declares 0.3.0 against a published v0.4.0.
    Neither can be corrected now.
    """

    def _archive(self):
        path = Path(".zenodo.json")
        if not path.is_file():
            pytest.skip("no Zenodo metadata in this checkout")
        return json.loads(path.read_text(encoding="utf-8"))

    def _declared_version(self):
        import re as _re

        found = _re.search(
            r'^version = "([^"]+)"', Path("pyproject.toml").read_text(encoding="utf-8"), _re.M
        )
        assert found, "pyproject.toml declares no version"
        return found.group(1)

    def test_the_version_agrees_across_all_three_files(self):
        version = self._declared_version()
        assert self._archive()["version"] == version, (
            f".zenodo.json says {self._archive()['version']}, pyproject says {version}"
        )
        assert f"version: {version}" in Path("CITATION.cff").read_text(encoding="utf-8")

    def test_no_top_level_doi_stops_zenodo_versioning_the_release(self):
        """A top-level doi tells Zenodo the identifier came from elsewhere, and it stops
        minting a version DOI per release. The file's own notes say so."""
        assert "doi" not in self._archive(), (
            "a top-level doi in .zenodo.json stops Zenodo versioning this release"
        )

    def test_the_concept_doi_relation_matches_what_has_been_minted(self):
        """Before the first deposit there is no concept DOI, and inventing one would
        point the archive at somebody else's record. After it, the relation must be the
        one release.json records."""
        release = json.loads(RELEASE.read_text(encoding="utf-8"))
        relations = {
            r["relation"]: r["identifier"]
            for r in self._archive().get("related_identifiers", [])
        }
        concept = release.get("zenodo_concept_doi")
        if concept is None:
            assert "isVersionOf" not in relations, (
                f"the archive claims a concept DOI {relations.get('isVersionOf')} that "
                "results/release.json does not record"
            )
        else:
            assert relations.get("isVersionOf") == concept

    def test_the_author_and_repository_match_the_rest_of_the_project(self):
        archive = self._archive()
        release = json.loads(RELEASE.read_text(encoding="utf-8"))
        creator = archive["creators"][0]
        assert creator["orcid"] == "0000-0001-9211-1071"
        assert creator["name"] == "Yamamoto, Shuji"
        supplement = [
            r["identifier"]
            for r in archive["related_identifiers"]
            if r["relation"] == "isSupplementTo"
        ]
        assert release["repository"] in supplement, (
            f"the archive points at {supplement}, results/release.json says "
            f"{release['repository']}"
        )

    def test_the_description_does_not_overstate_the_validation(self):
        """The deposit description is read by people who never open the paper, and the
        CT narrowing is the claim most easily lost when prose is shortened for a
        landing page."""
        text = self._archive()["description"]
        assert "narrows to CT" in text
        assert "discordant study is retained" in text
        assert "No imaging data of any kind is redistributed" in text
