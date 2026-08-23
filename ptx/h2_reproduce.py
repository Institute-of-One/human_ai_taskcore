"""Per-study reproduction configs for the H2 external validation.

The registry (``data/h2_studies.json``) holds what each paper reports. This
module holds the other half: how those reports map onto the chain's inputs. The
schema is frozen (pre-registration v1.3 section D), so this mapping lives in
code rather than as extra registry fields.

Two kinds of missing value are kept apart, because conflating them is how a
guess turns into a datum:

- a parameter the paper *does not report* is filled from the declared defaults
  of pre-registration section 4 and published per condition in
  ``assumed_parameters``. That path is legitimate and already implemented in
  :class:`ptx.external.ModelPredictor`.
- a parameter the paper *does report* but we have not read yet is not defaulted
  at all. Substituting a default for a value that exists in the paper would
  put an invented number into the validation, so :meth:`StudyReproduction.build`
  refuses to produce a config while any such parameter is outstanding, and
  names them.

Nothing here computes a prediction. Rank agreement runs once, over the whole
pool, through :func:`gate_pool` — never study by study.
"""

from __future__ import annotations

import dataclasses

from .condition import Acquisition, Reading
from .external import ASSUMED_READING, validate_registry

__all__ = [
    "StudyReproduction",
    "STUDY_REPRODUCTIONS",
    "PoolNotReady",
    "gate_pool",
    "outstanding_parameters",
]


@dataclasses.dataclass(frozen=True)
class StudyReproduction:
    """How one study's reported conditions map onto the chain's inputs.

    ``dose_reference_label`` names the condition the paper's dose axis is
    normalised to, so ``dose_relative`` is a ratio of reported exposures and
    carries no assumption of its own. The absolute noise level that ratio acts
    on (``reference_sd_hu``) is a property of the images, so it has to be read
    from the paper like any other reported quantity.
    """

    study_id: str
    source: str
    task_diameters_mm: tuple
    task_contrast_hu: float
    dose_axis: dict  # reported label -> dose relative to the reference below
    dose_reference_label: str
    reading_overrides: dict = dataclasses.field(default_factory=dict)
    acquisition_overrides: dict = dataclasses.field(default_factory=dict)
    pending_from_pdf: tuple = ()
    notes: str = ""

    def build(self):
        """Base ``(Acquisition, Reading)`` for this study.

        Raises while any reported-but-unread parameter is outstanding: see the
        module docstring for why these are not defaulted.
        """
        if self.pending_from_pdf:
            raise PoolNotReady(
                f"{self.study_id}: these parameters are reported in the paper "
                f"but have not been read from it yet: "
                f"{', '.join(self.pending_from_pdf)}. They are not filled from "
                "the declared defaults, because a default standing in for a "
                "value the paper states would be an invented datum."
            )
        acquisition = dataclasses.replace(
            Acquisition(), **self.acquisition_overrides
        )
        reading = dataclasses.replace(ASSUMED_READING, **self.reading_overrides)
        return acquisition, reading


class PoolNotReady(RuntimeError):
    """Raised when an analysis is attempted before the pool is complete."""


# Reported design, read at title and abstract level only (candidate scan v1.1).
# Every performance value is still unread, and so is everything listed in
# pending_from_pdf.
STUDY_REPRODUCTIONS = {
    "yu2013": StudyReproduction(
        study_id="yu2013",
        source=(
            "Yu L, et al. Med Phys 2013;40(4):041908 (PMC3618092). "
            "CAND-01; design from the abstract, performance data unread."
        ),
        task_diameters_mm=(3.0, 5.0, 9.0),
        task_contrast_hu=-15.0,
        # quality reference mAs, normalised to the middle level
        dose_axis={
            "60 mAs": 0.25,
            "120 mAs": 0.5,
            "240 mAs": 1.0,
            "360 mAs": 1.5,
            "480 mAs": 2.0,
        },
        dose_reference_label="240 mAs",
        pending_from_pdf=(
            "pixel_mm_object (display FOV and matrix)",
            "kernel and its f50_lpmm",
            "slice_thickness_mm",
            "reference_sd_hu (noise level at 240 mAs)",
            "display and reading conditions, if reported",
        ),
        notes=(
            "Uniform water phantom with rods: signal known exactly on a flat "
            "background, which is the assumption the chain is built on, so no "
            "anatomical-noise term is needed. Reconstruction is an axis "
            "(FBP and IR); IR is not a linear filter, so how it enters the "
            "chain has to be stated in the manuscript rather than assumed."
        ),
    ),
    "leng2013": StudyReproduction(
        study_id="leng2013",
        source=(
            "Leng S, et al. Med Phys 2013;40(8):081908 (PMC3724792). "
            "CAND-13; design from the abstract, performance data unread."
        ),
        task_diameters_mm=(3.0, 5.0),
        task_contrast_hu=-15.0,
        # CTDIvol in mGy, normalised to the second level
        dose_axis={
            "5.7 mGy": 0.5,
            "11.4 mGy": 1.0,
            "17.1 mGy": 1.5,
            "22.8 mGy": 2.0,
        },
        dose_reference_label="11.4 mGy",
        pending_from_pdf=(
            "pixel_mm_object (the 128 x 128 ROI covers an unstated field)",
            "kernel and its f50_lpmm",
            "slice_thickness_mm",
            "reference_sd_hu (noise level at 11.4 mGy)",
            "display and reading conditions, if reported",
        ),
        notes=(
            "Same phantom family as yu2013. Use ROC AUC only: the AUC-to-d' "
            "identity holds for the equal-variance binormal ROC and not for "
            "LROC. Task congruence is search_or_location_uncertain, which is "
            "recorded and stratified on, never used to include or exclude."
        ),
    ),
}


def outstanding_parameters():
    """What still has to be read from the PDFs, per study."""
    return {
        study_id: config.pending_from_pdf
        for study_id, config in STUDY_REPRODUCTIONS.items()
        if config.pending_from_pdf
    }


def gate_pool(registry):
    """Refuse to analyse until the frozen pool requirements are met.

    H2 is a statement about a pool: at least three studies, at least fifteen
    condition points and at least one non-CT study. Running rank agreement on
    whatever is transcribed so far would mean looking at one study's agreement
    before deciding whether to keep hunting for the next, which is the
    selective-validation route the pre-registration exists to close. So the
    analysis is gated on the pool being complete, and the gate is this
    function rather than a habit.
    """
    problems = validate_registry(registry)
    if problems:
        raise PoolNotReady(
            "the H2 analysis runs once, over the complete pool; outstanding: "
            + "; ".join(
                f"{key}: {', '.join(value)}" for key, value in problems.items()
            )
        )
    return tuple(registry.studies)
