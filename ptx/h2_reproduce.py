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
    carries no assumption of its own.

    ``pending_from_pdf`` lists parameters the paper reports that we have not
    read; ``unreported`` lists parameters the paper does not report, which take
    the declared defaults and are published per condition as
    ``assumed_parameters``. The first blocks :meth:`build`, the second does not.
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
    unreported: tuple = ()
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


STUDY_REPRODUCTIONS = {
    "yu2013": StudyReproduction(
        study_id="yu2013",
        source=(
            "Yu L, Leng S, Chen L, Kofler JM, Carter RE, McCollough CH. "
            "Med Phys 2013;40(4):041908, sections II.A-II.C, pp. 041908-2 to "
            "041908-4. Scan and reading parameters read from the paper; "
            "performance values digitised from Figures 7 and 9; see "
            "data/h2_studies.json yu2013."
        ),
        task_diameters_mm=(3.0, 5.0, 9.0),
        task_contrast_hu=-15.0,
        # quality reference mAs, normalised to the middle level; CTDIvol runs
        # 2.8, 5.7, 11.4, 17.1, 22.8 mGy over the same five settings, and the
        # two axes agree on the ratios to within rounding
        dose_axis={
            "60 mAs": 0.25,
            "120 mAs": 0.5,
            "240 mAs": 1.0,
            "360 mAs": 1.5,
            "480 mAs": 2.0,
        },
        dose_reference_label="240 mAs",
        acquisition_overrides={
            # B40 kernel, MTF 3.97 cm^-1 at 50% (p. 041908-3)
            "f50_lpmm": 0.397,
            "slice_thickness_mm": 5.0,
            # the 128 x 128 ROI spans 6.2 x 6.2 cm (section II.B)
            "pixel_mm_object": 6.2 * 10.0 / 128.0,
        },
        reading_overrides={
            # binocular viewing from about 40 cm, ACR electronic practice
            # standard, darkened room (section II.C)
            "distance_mm": 400.0,
            "window_width_hu": 400.0,
        },
        unreported=(
            "reference_sd_hu (no image noise level is stated at any dose)",
            "display_pitch_mm and n_grey_levels (monitor not identified)",
            "luminance_cdm2 (calibration cited, level not stated)",
        ),
        notes=(
            "Uniform water phantom with rods: signal known exactly on a flat "
            "background, which is the assumption the chain is built on, so no "
            "anatomical-noise term is needed. Reconstruction is an axis (FBP "
            "B40 and SAFIRE I40 strength 3, the latter at 60 and 120 mAs "
            "only); IR is not a linear filter, so how it enters the chain has "
            "to be stated in the manuscript rather than assumed. Window width "
            "is taken as 400 HU from section II.C, which is the reading "
            "condition; the Figure 2 caption says 300 HU, but that describes "
            "the printed collage rather than the review sessions. Six of the "
            "21 percent-correct values appear in the text of section III.D; "
            "the other fifteen are only in Figures 7 and 9."
        ),
    ),
    "paul2007": StudyReproduction(
        study_id="paul2007",
        source=(
            "Paul NS, Siewerdsen JH, Patsios D, Chung T-B. Med Phys "
            "2007;34(9):3587-3595, sections II.B-II.C, pp. 3589-3590. Scan "
            "and reading parameters read from the paper; performance values "
            "digitised from Figure 6 on the reduced separable set "
            "(data/h2_studies.json paul2007)."
        ),
        # task 1 only: the solid 3.2 mm nodule at +23 HU, the one task in which
        # size and contrast are known to the observer. Tasks 2 and 3 vary the
        # signal within the trial set, which is outside the declared scope of
        # signal-specified detection (protocol section 2.1) — a scope
        # judgement on the task, made without reference to any performance
        # value
        task_diameters_mm=(3.2,),
        task_contrast_hu=23.0 - (-680.0),  # nodule against lung background
        # dose in mGy over the 54 techniques, normalised to a mid-range
        # diagnostic setting (120 kVp, 100 mA, 1.25 mm = 13.2 mGy)
        dose_axis={
            "0.34 mGy": 0.34 / 13.2,
            "1.0 mGy": 1.0 / 13.2,
            "5.5 mGy": 5.5 / 13.2,
            "13.2 mGy": 1.0,
            "26.4 mGy": 26.4 / 13.2,
        },
        dose_reference_label="13.2 mGy",
        acquisition_overrides={
            # 1.25, 2.5 and 5 mm are the reconstructed thicknesses; the axis is
            # entered per condition, and this is the mid setting
            "slice_thickness_mm": 2.5,
        },
        reading_overrides={
            "window_width_hu": 800.0,
        },
        unreported=(
            "pixel_mm_object (reconstruction FOV and matrix not stated; the "
            "2 x 2 cm ROI was interpolated to 200 x 200 pixels, which is "
            "display sampling and not the reconstruction's)",
            "f50_lpmm (an edge-enhancing lung filter, not characterised)",
            "reference_sd_hu (no image noise level is stated)",
            "distance_mm (observers were free to vary viewing distance)",
            "display_pitch_mm, n_grey_levels, luminance_cdm2",
        ),
        notes=(
            "Heterogeneous polyurethane/microballoon lung modules at about "
            "-680 HU, so unlike yu2013 the background carries anatomical-like "
            "structure the chain does not model; this belongs in the "
            "heterogeneity discussion. Condition axes are dose and "
            "slice_thickness. Task congruence is ske for task 1. Signal "
            "location was randomised by up to 5 mm within the ROI, which is "
            "small compared with the 2 cm crop but is not zero and is "
            "recorded."
        ),
    ),
    "leng2013": StudyReproduction(
        study_id="leng2013",
        source=(
            "Leng S, Yu L, Zhang Y, Carter R, Toledano AY, McCollough CH. "
            "Med Phys 2013;40(8):081908, sections 2.A-2.C, pp. 081908-2 to "
            "081908-3. Scan and reading parameters read from the PDF."
        ),
        task_diameters_mm=(3.0, 5.0),
        task_contrast_hu=-15.0,
        dose_axis={
            "5.7 mGy": 0.5,
            "11.4 mGy": 1.0,
            "17.1 mGy": 1.5,
            "22.8 mGy": 2.0,
        },
        dose_reference_label="11.4 mGy",
        acquisition_overrides={
            "slice_thickness_mm": 5.0,
            # paper: "pixel size ~0.5 mm" (p. 081908-5)
            "pixel_mm_object": 0.5,
            # B40, MTF50 not stated here; same kernel and scanner family as
            # Yu 2013, whose 3.97 cm^-1 is recorded as assumed, not as a
            # Leng-reported number
            "f50_lpmm": 0.397,
        },
        reading_overrides={
            # "approximately 50-60 cm"; the midpoint is the reported range,
            # not a default
            "distance_mm": 550.0,
            "window_width_hu": 400.0,
        },
        unreported=(
            "f50_lpmm (B40 named, MTF50 not stated; 0.397 taken from Yu "
            "2013 and listed as assumed)",
            "luminance_cdm2, display_pitch_mm, n_grey_levels (ACR-calibrated "
            "monitor, level not stated)",
            "reference_sd_hu",
        ),
        notes=(
            "Same phantom family as yu2013, location randomised inside the "
            "ROI. Use ROC AUC only: the AUC-to-d' identity holds for the "
            "equal-variance binormal ROC and not for LROC. Task congruence "
            "is search_or_location_uncertain, which is recorded and "
            "stratified on, never used to include or exclude."
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
