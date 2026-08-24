"""Build the Yu 2013 and Paul 2007 study records from the digitisation CSVs.

Value convention (frozen with this commit):
- printed text beats a recovered number (Yu section III.D anchors)
- otherwise the first-pass value is used, never the average of the two passes
- for Paul, dose (x) is the pass-2 axis calibration until Yamamoto's
  WebPlotDigitizer pass 1 arrives, because pass 1x is only good to ~15% on a
  log axis; y is the pass-1x reading where one exists

    python data/h2_digitisation/emit_registry_studies.py
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import compare_passes as cmp  # noqa: E402

# Yu section III.D, percent correct as printed. Registry stores the fraction.
YU_ANCHORS = {
    (3.0, 120, "FBP"): 0.798,
    (3.0, 120, "IR"): 0.688,
    (5.0, 60, "FBP"): 0.883,
    (5.0, 60, "IR"): 0.915,
    (5.0, 120, "FBP"): 0.925,
    (5.0, 120, "IR"): 0.983,
}

YU_DOSE_RELATIVE = {60: 0.25, 120: 0.5, 240: 1.0, 360: 1.5, 480: 2.0}
PAUL_DOSE_REFERENCE_MGY = 13.2

YU_ASSUMED = {
    "luminance_cdm2": 100.0,
    "display_pitch_mm": 0.2,
    "n_grey_levels": 256,
    "magnification": 1.0,
    "reference_sd_hu": 50.0,
}
PAUL_ASSUMED = {
    "distance_mm": 500.0,
    "luminance_cdm2": 100.0,
    "display_pitch_mm": 0.2,
    "n_grey_levels": 256,
    "magnification": 1.0,
    "f50_lpmm": None,  # listed so the gap is visible; omitted from the dict below
    "pixel_mm_object": None,
    "reference_sd_hu": 50.0,
    "slice_thickness_mm": 2.5,
}


def _round(value, places=6):
    return round(float(value), places)


def yu_conditions():
    rows = [
        row
        for row in cmp.load(HERE / "pass1x_CAND-01.csv")
        if cmp.get(row, "observer_type") == "human"
    ]
    conditions = []
    for row in rows:
        diameter = cmp.number(row, "diameter_mm")
        dose = int(cmp.number(row, "dose_value"))
        recon = cmp.get(row, "recon")
        anchor = YU_ANCHORS.get((diameter, dose, recon))
        if anchor is not None:
            value, source = anchor, "text_III.D"
        else:
            value, source = cmp.as_fraction(cmp.number(row, "y_value")), "pass1x"
        label = f"{diameter:g} mm {dose} mAs {recon}"
        conditions.append(
            {
                "label": label,
                "metric_value": _round(value, 4),
                "parameters": {
                    "diameter_mm": diameter,
                    "contrast_hu": -15.0,
                    "dose_relative": YU_DOSE_RELATIVE[dose],
                    "reconstruction": recon,
                    "f50_lpmm": 0.397,
                    "slice_thickness_mm": 5.0,
                    "pixel_mm_object": 6.2 * 10.0 / 128.0,
                    "distance_mm": 400.0,
                    "window_width_hu": 400.0,
                    "value_source": source,
                },
                "assumed_parameters": dict(YU_ASSUMED),
            }
        )
    return conditions


def paul_conditions(kept, matched):
    """One condition per kept marker. y from pass 1x when matched, else pass 2."""
    by_dose_y = {}
    for item in matched:
        by_dose_y[item["dose_pass2"]] = item["y1"]

    conditions = []
    for row in kept:
        dose = cmp.number(row, "dose_value")
        if dose in by_dose_y:
            value, source = cmp.as_fraction(by_dose_y[dose]), "pass1x"
        else:
            value, source = cmp.as_fraction(cmp.number(row, "y_value")), "pass2"
        # pixel calibration can land 0.0004 above the plotted ceiling
        value = min(value, 1.0)
        # A_z = 1 is plotted; the d' identity is undefined at 1, so the
        # calibration plot will have to drop those points. Rank agreement
        # does not use the identity and keeps them as ties at the ceiling.
        label = f"task1 {dose:.3f} mGy"
        assumed = {
            key: val
            for key, val in PAUL_ASSUMED.items()
            if val is not None
        }
        conditions.append(
            {
                "label": label,
                "metric_value": _round(value, 4),
                "parameters": {
                    "diameter_mm": 3.2,
                    "contrast_hu": 23.0 - (-680.0),
                    "dose_mgy": _round(dose, 3),
                    "dose_relative": _round(dose / PAUL_DOSE_REFERENCE_MGY, 6),
                    "value_source": source,
                },
                "assumed_parameters": assumed,
            }
        )
    return conditions


def yu_record(yu_stats):
    return {
        "study_id": "yu2013",
        "citation": (
            "Yu L, Leng S, Chen L, Kofler JM, Carter RE, McCollough CH. "
            "Prediction of human observer performance in a 2-alternative "
            "forced choice low-contrast detection task using channelized "
            "Hotelling observer: impact of radiation dose and reconstruction "
            "algorithms. Med Phys 2013;40(4):041908. doi:10.1118/1.4794498 "
            "(PMID 23556902, PMC3618092). Candidate CAND-01."
        ),
        "modality": "ct",
        "task": "2AFC low-contrast rod detection in a uniform water phantom",
        "condition_axes": ["dose", "reconstruction", "lesion_size"],
        "metric": "pc_2afc",
        "acquisition": "digitised_figure",
        "reports_display_conditions": False,
        "reports_reading_conditions": True,
        "generality_check": False,
        "n_readers": 4,
        "task_congruence": "ske",
        "digitisation_repeat_max_deviation": _round(
            yu_stats["digitisation_repeat_max_deviation"], 5
        ),
        "conditions": yu_conditions(),
        "notes": (
            "C6 pass on the full 21 human points (15 FBP Fig. 7 + 6 IR Fig. 9). "
            f"Max deviation unsaturated "
            f"{yu_stats['max_deviation_unsaturated_percent']:.2f}%, "
            f"saturated {yu_stats['max_deviation_saturated_percent']:.2f}% "
            "(saturated = fraction >= 0.995, reported separately so the "
            "ceiling cluster cannot dilute the check). Six values are the "
            "printed numbers from section III.D; the rest are the pass-1x "
            "reading, never the average of the two passes. Model-observer "
            "series were digitised for the Bland-Altman cross-check and are "
            "not condition points."
        ),
    }


def paul_record(paul_stats):
    return {
        "study_id": "paul2007",
        "citation": (
            "Paul NS, Siewerdsen JH, Patsios D, Chung T-B. Investigating the "
            "low-dose limits of multidetector CT in lung nodule surveillance. "
            "Med Phys 2007;34(9):3587-3595. doi:10.1118/1.2768866. "
            "Candidate CAND-04; task 1 only (solid 3.2 mm nodule, signal "
            "specified)."
        ),
        "modality": "ct",
        "task": "2AFC detection of a specified solid 3.2 mm nodule",
        "condition_axes": ["dose", "slice_thickness"],
        "metric": "auc",
        "acquisition": "digitised_figure",
        "reports_display_conditions": False,
        "reports_reading_conditions": False,
        "generality_check": False,
        "n_readers": 9,
        "task_congruence": "ske",
        "digitisation_repeat_max_deviation": _round(
            paul_stats["digitisation_repeat_max_deviation"], 5
        ),
        "conditions": paul_conditions(paul_stats["kept"], paul_stats["matched"]),
        "notes": (
            "C6 pass on a reduced condition set, the path the pre-registration "
            "explicitly allows (a point is resolved by a third pass or the "
            "study's condition set is reduced, and either outcome is recorded). "
            f"Kept {paul_stats['n_kept']} separable points (non-saturated "
            "markers plus isolated saturated markers); dropped the eight "
            "narrow_occluded_uncertain leftovers (three on panel b, five on "
            "panel d) after adjudication against pass 1x. Section III.C's "
            "nine measurements below 1 mGy are the paper's count: seven are "
            "in the kept set, two remain in the occluded 0.66-0.70 mGy pile "
            "whose cardinality cannot be recovered independently of method. "
            "Saturated Az=1.000 stacks have no rank information and are not "
            "kept as clusters. x (dose) is the pass-2 axis calibration "
            "pending Yamamoto WebPlotDigitizer pass 1; y is the pass-1x "
            "value where one exists, otherwise pass 2, never the average. "
            f"Max deviation on the reduced unsaturated matches "
            f"{paul_stats['max_deviation_unsaturated_percent']:.2f}%. "
            "Full record: docs/h2_cand04_condition_set_reduction.md."
        ),
    }


def main():
    yu = cmp.compare_yu()
    paul = cmp.compare_paul()
    path = ROOT / "data" / "h2_studies.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["studies"] = [yu_record(yu), paul_record(paul)]
    payload["note"] = (
        "Registry for the H2 external validation (protocol section 8). The "
        "inclusion criteria in docs/IORN-009A_H2_preregistration_v1.0.md were "
        "frozen before the literature search began; v1.1 amended C2's "
        "condition-axis vocabulary, v1.2 replaced the enumeration with the "
        "principle that an axis counts only if it names a declared model "
        "input, and v1.3 added the task_congruence descriptive field and "
        "froze the schema, each with the disclosure its own document carries. "
        "Yu 2013 is in studies with its full 21 human points (C6 pass). "
        "Paul 2007 is in studies on the reduced separable set recorded in "
        "docs/h2_cand04_condition_set_reduction.md (C6 pass by reduction, "
        "not a full-set fail). CAND-13 is still waiting on its PDF. No "
        "rank agreement has been run: gate_pool still holds."
    )
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {path}: yu2013 {len(payload['studies'][0]['conditions'])} pts, "
        f"paul2007 {len(payload['studies'][1]['conditions'])} pts"
    )


if __name__ == "__main__":
    main()
