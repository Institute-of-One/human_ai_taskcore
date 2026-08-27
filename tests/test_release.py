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
