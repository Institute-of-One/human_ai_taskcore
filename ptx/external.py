"""H2 external validation against published observer studies (section 8).

This module is the executable half of the pre-registration
(``docs/IORN-009A_H2_preregistration_v1.0.md``, amended by ``..._v1.1.md`` and
``..._v1.2.md``): the inclusion criteria, the schema and the analysis are all
fixed here so that study selection cannot drift once the literature is in front
of us. The
registry it validates (``data/h2_studies.json``) is deliberately empty until
the systematic search runs — the criteria were frozen first, and the commit
that added them is the evidence.

What the criteria buy us:

- rank agreement within a study is the primary measure, because observer
  panels, task definitions and decision criteria are not comparable across
  studies, but the ordering of conditions inside one study is
- reading conditions that a paper does not report are filled from declared
  defaults and recorded per condition, then varied over the section 5.4
  intervals, so a conclusion resting on an assumption is visible as such
- every screened study is recorded with the criterion it failed, so the pool
  cannot be quietly curated
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import special, stats

from .condition import Acquisition, Reading, Task, evaluate, frequency_grid

__all__ = [
    "SCHEMA_VERSION",
    "ObservedCondition",
    "StudyRecord",
    "ScreenedStudy",
    "Registry",
    "auc_to_dprime",
    "pc_2afc_to_dprime",
    "metric_to_dprime",
    "validate_study",
    "validate_registry",
    "qualifies_under_v1_0",
    "qualifies_under_v1_1",
    "pool_partition",
    "unpredictable_axis_reason",
    "load_registry",
    "ModelPredictor",
    "rank_agreement",
    "pooled_calibration",
]

SCHEMA_VERSION = "1.2"

# --- C2 condition-axis vocabulary -------------------------------------------
#
# Frozen 2026-08-23; the pre-registration documents carry the rationale and the
# disclosures. Axes are a closed vocabulary so that "two condition axes" cannot
# be argued into existence with free text.
#
# v1.0 enumerated the axes by hand and v1.1 bolted two more on, which is how a
# vocabulary ends up needing an amendment every time an unfamiliar study shows
# up. v1.2 stops enumerating: an axis is admissible exactly when it names a
# declared input of the model, because that is the same thing as saying the
# model can predict what happens when a study varies it. An axis the chain has
# no term for cannot be predicted, so counting it as validation would be empty.
#
# The mapping below is the vocabulary. Every entry points at fields of
# Acquisition/Reading/Task, and the test suite checks both directions: no axis
# without a field, and no eligible field without an axis. So the vocabulary is
# derived from the implementation rather than curated, and it cannot be widened
# without widening the model itself.
#
# Two categories of declared input are deliberately not axes:
OBSERVER_EFFICIENCY_FIELDS = ("kappa", "eta_cog")  # inferred, never read off a
# paper: these are propagated over the section 5.4 intervals, so admitting them
# as conditions would let a study "vary" a quantity we are fitting.
CALIBRATION_FIELDS = (
    "reference_kernel",
    "reference_sd_hu",
    "reference_slice_mm",
    "noise_scale_at_reference",
)  # anchor the noise scale to a stated reference; not conditions of a reading.

AXIS_TO_MODEL_INPUT = {
    "dose": (("Acquisition", "dose_relative"),),
    "lesion_size": (("Task", "diameter_mm"),),
    "contrast": (("Task", "contrast_hu"),),
    "reconstruction": (
        ("Acquisition", "kernel"),
        ("Acquisition", "kernel_sharpness"),
    ),
    "processing": (
        ("Acquisition", "f50_lpmm"),
        ("Acquisition", "ramp_exponent"),
    ),
    "slice_thickness": (("Acquisition", "slice_thickness_mm"),),
    "pixel_size": (("Acquisition", "pixel_mm_object"),),
    "displayed_matrix": (("Reading", "display_pitch_mm"),),
    "magnification": (("Reading", "zoom"),),
    "luminance": (("Reading", "luminance_cdm2"),),
    "viewing_distance": (("Reading", "distance_mm"),),
    "field_of_view": (("Reading", "field_deg"),),
    "window_width": (("Reading", "window_width_hu"),),
    "grey_levels": (("Reading", "n_grey_levels"),),
}

V1_0_AXES = ("dose", "lesion_size", "contrast", "reconstruction", "processing")
V1_1_AXES = V1_0_AXES + ("pixel_size", "displayed_matrix")
V1_2_AXES = tuple(sorted(AXIS_TO_MODEL_INPUT))
ALLOWED_AXES = V1_2_AXES

UNPREDICTABLE_AXIS_REASON = (
    "C2: {axes} correspond to no term in the model, so the effect of varying "
    "them cannot be predicted; an axis that cannot be predicted is not counted "
    "as a validation axis (pre-registration v1.2 §A)"
)


def unpredictable_axis_reason(axes):
    """The frozen wording for excluding a study on unpredictable axes.

    Generated rather than typed per study so that exclusion records state the
    same reason in the same words, which is what makes them auditable.
    """
    listed = ", ".join(f"{axis!r}" for axis in axes)
    return UNPREDICTABLE_AXIS_REASON.format(axes=listed)

ALLOWED_MODALITIES = ("ct", "chest_radiography")
ALLOWED_METRICS = ("auc", "pc_2afc", "dprime")
ALLOWED_ACQUISITION = ("table", "digitised_figure")
MIN_CONDITION_AXES = 2
MIN_CONDITIONS_PER_STUDY = 4
MIN_STUDIES = 3
MIN_CONDITION_POINTS = 15
MIN_NON_CT_STUDIES = 1
DIGITISATION_TOLERANCE = 0.05
SPEARMAN_SUCCESS = 0.7

# declared defaults for reading conditions a paper does not report
ASSUMED_READING = Reading(
    zoom=1.0,
    distance_mm=500.0,
    luminance_cdm2=100.0,
    display_pitch_mm=0.2,
    window_width_hu=1500.0,
    n_grey_levels=256,
)


def auc_to_dprime(auc):
    """d' from AUC under the equal-variance binormal model.

    ``AUC = Phi(d'/sqrt(2))``, so ``d' = sqrt(2) Phi^-1(AUC)``. Used only for
    the calibration plot: rank agreement is invariant to this transform.
    """
    auc = np.asarray(auc, dtype=float)
    if np.any((auc <= 0.0) | (auc >= 1.0)):
        raise ValueError("AUC must lie strictly between 0 and 1")
    return np.sqrt(2.0) * special.ndtri(auc)


def pc_2afc_to_dprime(pc):
    """d' from two-alternative forced-choice proportion correct.

    ``PC = Phi(d'/sqrt(2))`` for 2AFC, the same relation as AUC. m-AFC with
    m > 2 needs a numerical integral and extra assumptions, so the
    pre-registration excludes it rather than approximating it here.
    """
    pc = np.asarray(pc, dtype=float)
    if np.any((pc <= 0.5) | (pc >= 1.0)):
        raise ValueError("2AFC proportion correct must lie in (0.5, 1)")
    return np.sqrt(2.0) * special.ndtri(pc)


def metric_to_dprime(metric, value):
    if metric == "auc":
        return auc_to_dprime(value)
    if metric == "pc_2afc":
        return pc_2afc_to_dprime(value)
    if metric == "dprime":
        return np.asarray(value, dtype=float)
    raise ValueError(f"unsupported metric: {metric!r}")


@dataclasses.dataclass(frozen=True)
class ObservedCondition:
    """One reported condition point of one study."""

    label: str
    metric_value: float
    parameters: dict = dataclasses.field(default_factory=dict)
    assumed_parameters: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class StudyRecord:
    """An included study, with everything the criteria need to be checked."""

    study_id: str
    citation: str
    modality: str
    task: str
    condition_axes: tuple
    metric: str
    acquisition: str
    reports_display_conditions: bool
    reports_reading_conditions: bool
    generality_check: bool
    n_readers: int | None
    conditions: tuple
    digitisation_repeat_max_deviation: float = 0.0
    notes: str = ""

    @property
    def observed_dprime(self):
        return metric_to_dprime(
            self.metric, [c.metric_value for c in self.conditions]
        )


@dataclasses.dataclass(frozen=True)
class ScreenedStudy:
    """A study that was looked at and not used."""

    study_id: str
    citation: str
    failed_criterion: str
    exclusion_reason: str


@dataclasses.dataclass(frozen=True)
class Registry:
    schema_version: str
    frozen: str
    studies: tuple = ()
    screened: tuple = ()


def validate_study(study):
    """Return the list of frozen criteria a study record violates."""
    problems = []
    if study.modality not in ALLOWED_MODALITIES:
        problems.append(f"C1: modality {study.modality!r} out of scope")
    unknown = [
        axis for axis in study.condition_axes if axis not in ALLOWED_AXES
    ]
    if unknown:
        problems.append(f"C2: condition axes outside the vocabulary: {unknown}")
    elif len(study.condition_axes) < MIN_CONDITION_AXES:
        problems.append(
            f"C2: needs >= {MIN_CONDITION_AXES} condition axes, "
            f"has {len(study.condition_axes)}"
        )
    if len(study.conditions) < MIN_CONDITIONS_PER_STUDY:
        problems.append(
            f"C3: needs >= {MIN_CONDITIONS_PER_STUDY} condition points, "
            f"has {len(study.conditions)}"
        )
    if study.metric not in ALLOWED_METRICS:
        problems.append(f"C5: metric {study.metric!r} not accepted")
    if study.acquisition not in ALLOWED_ACQUISITION:
        problems.append(f"acquisition {study.acquisition!r} not recognised")
    if study.acquisition == "digitised_figure":
        if study.digitisation_repeat_max_deviation > DIGITISATION_TOLERANCE:
            problems.append(
                "C6: repeat digitisation deviates by "
                f"{study.digitisation_repeat_max_deviation:.3f} > "
                f"{DIGITISATION_TOLERANCE}"
            )
    elif study.digitisation_repeat_max_deviation != 0.0:
        problems.append("C6: table-sourced data cannot have a digitisation error")
    if study.generality_check and study.modality == "ct":
        problems.append(
            "the generality check must be carried by a non-CT study"
        )
    # C4 never excludes, but assumptions have to be visible
    if not (
        study.reports_display_conditions and study.reports_reading_conditions
    ):
        if not any(c.assumed_parameters for c in study.conditions):
            problems.append(
                "C4: display or reading conditions are unreported, so the "
                "substituted values must be listed in assumed_parameters"
            )
    return problems


def validate_registry(registry):
    """Per-study problems plus the frozen pool requirements."""
    problems = {}
    if registry.schema_version != SCHEMA_VERSION:
        problems["schema"] = [
            f"registry schema {registry.schema_version} != {SCHEMA_VERSION}"
        ]
    for study in registry.studies:
        found = validate_study(study)
        if found:
            problems[study.study_id] = found
    for screened in registry.screened:
        if not screened.exclusion_reason.strip():
            problems[screened.study_id] = ["exclusion needs a stated reason"]

    pool = []
    n_points = sum(len(s.conditions) for s in registry.studies)
    if len(registry.studies) < MIN_STUDIES:
        pool.append(
            f"pool needs >= {MIN_STUDIES} studies, has {len(registry.studies)}"
        )
    if n_points < MIN_CONDITION_POINTS:
        pool.append(
            f"pool needs >= {MIN_CONDITION_POINTS} condition points, "
            f"has {n_points}"
        )
    non_ct = sum(1 for s in registry.studies if s.modality != "ct")
    if non_ct < MIN_NON_CT_STUDIES:
        pool.append(
            f"pool needs >= {MIN_NON_CT_STUDIES} non-CT study for the "
            "generality claim; without it the claim drops to CT only"
        )
    if pool:
        problems["pool"] = pool
    return problems


def _qualifies_under(study, vocabulary):
    return (
        sum(1 for axis in study.condition_axes if axis in vocabulary)
        >= MIN_CONDITION_AXES
    )


def qualifies_under_v1_0(study):
    """Whether the study meets C2 under the original hand-enumerated reading."""
    return _qualifies_under(study, V1_0_AXES)


def qualifies_under_v1_1(study):
    """Whether the study meets C2 under the first amendment's vocabulary."""
    return _qualifies_under(study, V1_1_AXES)


def pool_partition(registry):
    """Split the pool by the C2 vocabulary of each frozen version.

    Every widening of C2 has to be shown not to have manufactured the
    conclusion, so the sensitivity analysis reports all three frozen readings
    and the paper's success condition asks them to agree in direction. Doing
    the split mechanically leaves no room for choosing a subset after seeing
    the correlations.
    """
    v1_2 = tuple(registry.studies)
    v1_1 = tuple(s for s in v1_2 if qualifies_under_v1_1(s))
    v1_0 = tuple(s for s in v1_2 if qualifies_under_v1_0(s))
    return {
        "v1_0_strict": v1_0,
        "v1_1": v1_1,
        "v1_2": v1_2,
        "admitted_by_v1_1": tuple(
            s.study_id for s in v1_1 if s not in v1_0
        ),
        "admitted_by_v1_2": tuple(
            s.study_id for s in v1_2 if s not in v1_1
        ),
    }


def _study_from_dict(payload):
    conditions = tuple(
        ObservedCondition(**condition) for condition in payload["conditions"]
    )
    return StudyRecord(
        **{
            **payload,
            "condition_axes": tuple(payload["condition_axes"]),
            "conditions": conditions,
        }
    )


def load_registry(path="data/h2_studies.json"):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Registry(
        schema_version=payload["schema_version"],
        frozen=payload["frozen"],
        studies=tuple(_study_from_dict(s) for s in payload.get("studies", [])),
        screened=tuple(
            ScreenedStudy(**s) for s in payload.get("screened", [])
        ),
    )


class ModelPredictor:
    """Turn a study's reported parameters into a predicted d'.

    Keys are read from the condition's ``parameters``; anything missing comes
    from the declared defaults and is reported in :attr:`assumed`, which is
    what the pre-registration requires to be published per condition.
    """

    ACQUISITION_KEYS = (
        "kernel",
        "f50_lpmm",
        "dose_relative",
        "slice_thickness_mm",
        "pixel_mm_object",
    )
    READING_KEYS = (
        "distance_mm",
        "luminance_cdm2",
        "display_pitch_mm",
        "window_width_hu",
        "kappa",
        "eta_cog",
    )
    TASK_KEYS = ("diameter_mm", "contrast_hu")

    def __init__(self, acquisition=None, reading=None, n_freq=1024):
        self.acquisition = acquisition or Acquisition()
        self.reading = reading or ASSUMED_READING
        self.n_freq = n_freq
        self.assumptions = []

    def __call__(self, parameters):
        missing = [key for key in self.TASK_KEYS if key not in parameters]
        if missing:
            raise ValueError(
                f"a study condition must report {missing}: the task function "
                "cannot be assumed"
            )
        taken, assumed = {}, []
        for group in (self.ACQUISITION_KEYS, self.READING_KEYS):
            for key in group:
                if key in parameters:
                    taken[key] = parameters[key]
                else:
                    assumed.append(key)

        acquisition = dataclasses.replace(
            self.acquisition,
            **{k: v for k, v in taken.items() if k in self.ACQUISITION_KEYS},
        )
        reading = dataclasses.replace(
            self.reading,
            **{k: v for k, v in taken.items() if k in self.READING_KEYS},
        )
        if "magnification" in parameters:
            # the chain takes a pixel zoom; studies report apparent size
            reading = dataclasses.replace(
                reading,
                zoom=parameters["magnification"]
                * acquisition.pixel_mm_object
                / reading.display_pitch_mm,
            )
        else:
            assumed.append("magnification")

        self.assumptions.append(
            {
                "label": parameters.get("label"),
                "assumed": tuple(assumed),
            }
        )
        task = Task(
            diameter_mm=parameters["diameter_mm"],
            contrast_hu=parameters["contrast_hu"],
        )
        f = frequency_grid(acquisition, self.n_freq)
        return evaluate(f, task, acquisition, reading).dprime_human

    def predict_study(self, study):
        """Predicted d' for every condition point of a study, in order."""
        return np.array(
            [
                self(dict(condition.parameters, label=condition.label))
                for condition in study.conditions
            ]
        )


def rank_agreement(predicted, observed):
    """Within-study Spearman rank correlation and its success verdict."""
    predicted = np.asarray(predicted, dtype=float)
    observed = np.asarray(observed, dtype=float)
    if predicted.shape != observed.shape:
        raise ValueError("predicted and observed must have the same shape")
    if predicted.size < MIN_CONDITIONS_PER_STUDY:
        raise ValueError(
            f"rank agreement needs >= {MIN_CONDITIONS_PER_STUDY} points"
        )
    rho = float(stats.spearmanr(predicted, observed).statistic)
    return {
        "spearman": rho,
        "n": int(predicted.size),
        "meets_success_criterion": bool(rho >= SPEARMAN_SUCCESS),
    }


def pooled_calibration(per_study):
    """Pool studies after within-study rank standardisation.

    Standardising inside each study is what makes pooling defensible: the
    observer panels and decision criteria differ, the orderings do not.
    ``per_study`` is an iterable of (predicted, observed) sequences.
    """
    pooled_predicted, pooled_observed, rhos = [], [], []
    for predicted, observed in per_study:
        agreement = rank_agreement(predicted, observed)
        rhos.append(agreement["spearman"])
        n = agreement["n"]
        pooled_predicted.append(stats.rankdata(predicted) / (n + 1.0))
        pooled_observed.append(stats.rankdata(observed) / (n + 1.0))
    if not rhos:
        raise ValueError("no studies to pool")

    predicted = np.concatenate(pooled_predicted)
    observed = np.concatenate(pooled_observed)
    pooled_rho = float(stats.spearmanr(predicted, observed).statistic)
    rhos = np.array(rhos)
    return {
        "n_studies": int(rhos.size),
        "n_points": int(predicted.size),
        "pooled_spearman": pooled_rho,
        "per_study_spearman": {
            "min": float(rhos.min()),
            "median": float(np.median(rhos)),
            "max": float(rhos.max()),
        },
        "studies_meeting_criterion": int(np.sum(rhos >= SPEARMAN_SUCCESS)),
        "h2_supported": bool(
            np.mean(rhos >= SPEARMAN_SUCCESS) > 0.5
            and pooled_rho >= SPEARMAN_SUCCESS
        ),
    }
