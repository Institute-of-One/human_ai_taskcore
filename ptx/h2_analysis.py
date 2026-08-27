"""Run the H2 external validation once, exactly as the pre-registration specifies.

Usage::

    python -m ptx.h2_analysis

This runs after the pool is complete and not before: ``gate_pool`` refuses an
incomplete pool, because computing a correlation for one study and then deciding
whether to keep hunting for the next is the selective-validation route the
pre-registration exists to close.

What is computed, and nothing else:

* within-study Spearman rho against the model's prediction, with the verdict at
  the threshold of 0.7 frozen in v1.0 section 1;
* pooled calibration after within-study rank standardisation, with the same
  threshold;
* the same pair for all three frozen readings of C2, because v1.1 section D
  requires every widening of the vocabulary to be shown not to have manufactured
  the conclusion;
* heterogeneity, and the stratification by ``task_congruence`` that v1.3 adds as
  description. The stratification is not a success condition: v1.3 section A.2
  fixed that so a stratum could not be used to rescue H2.

No threshold is chosen here, no study is dropped here, and no p-value is computed
-- v1.0 section 5-5 forbids the last of these outright.

Writes ``results/h2.json``.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .external import (
    ModelPredictor,
    load_registry,
    pool_partition,
    pooled_calibration,
    rank_agreement,
)
from .h2_reproduce import STUDY_REPRODUCTIONS, gate_pool

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "results" / "h2.json"

#: v1.0 section 1. Written here as a name so that the number appears once.
SUCCESS_RHO = 0.7


def _predict(study) -> tuple[list[float], list[float], list[str]]:
    """Predicted d' and observed figure of merit, in the study's own order.

    The observed values are taken as reported and are not converted. v1.0 section
    5-4 converts AUC and PC to d' for the calibration plot only, and notes that a
    rank judgement is invariant under a monotone transform, so the primary analysis
    does not depend on it.
    """
    config = STUDY_REPRODUCTIONS[study.study_id]
    acquisition, reading = config.build()
    predictor = ModelPredictor(acquisition, reading)
    predicted = list(predictor.predict_study(study))
    observed = [condition.metric_value for condition in study.conditions]
    assumed = sorted(
        {key for condition in study.conditions for key in condition.assumed_parameters}
    )
    return predicted, observed, assumed


def analyse() -> dict[str, Any]:
    registry = load_registry()
    studies = gate_pool(registry)

    per_study: dict[str, Any] = {}
    ordered: dict[str, tuple[list[float], list[float]]] = {}
    for study in studies:
        predicted, observed, assumed = _predict(study)
        agreement = rank_agreement(predicted, observed)
        rho = agreement["spearman"]
        passed = agreement["meets_success_criterion"]
        ordered[study.study_id] = (predicted, observed)
        per_study[study.study_id] = {
            "n_conditions": len(observed),
            "metric": study.metric,
            "task_congruence": study.task_congruence,
            "spearman_rho": rho,
            "meets_threshold": passed,
            "assumed_parameters": sorted(set(assumed)),
        }

    partitions = pool_partition(registry)
    pools: dict[str, Any] = {}
    for name in ("v1_0_strict", "v1_1", "v1_2"):
        members = [s.study_id for s in partitions[name]]
        pairs = [ordered[key] for key in members if key in ordered]
        if not pairs:
            pools[name] = {"studies": members, "pooled_rho": None}
            continue
        calibration = pooled_calibration(pairs)
        rho = calibration["pooled_spearman"]
        passed = rho >= SUCCESS_RHO
        successes = sum(1 for key in members if per_study[key]["meets_threshold"])
        pools[name] = {
            "studies": members,
            "n_studies": len(members),
            "n_meeting_threshold": successes,
            "majority_meet_threshold": successes * 2 > len(members),
            "pooled_rho": rho,
            "pooled_meets_threshold": passed,
            # v1.0 section 1: rejection is a majority below threshold, or a pooled
            # calibration that is not monotone.
            "h2_rejected": (successes * 2 <= len(members)) or (rho is not None and rho < 0),
        }

    rhos = [v["spearman_rho"] for v in per_study.values() if v["spearman_rho"] is not None]
    strata: dict[str, Any] = {}
    for stratum in sorted({s.task_congruence for s in studies}):
        members = [s.study_id for s in studies if s.task_congruence == stratum]
        values = [
            per_study[key]["spearman_rho"]
            for key in members
            if per_study[key]["spearman_rho"] is not None
        ]
        pairs = [ordered[key] for key in members]
        pooled = pooled_calibration(pairs)["pooled_spearman"] if pairs else None
        strata[stratum] = {
            "studies": members,
            "n_studies": len(members),
            "median_within_study_rho": statistics.median(values) if values else None,
            "pooled_rho": pooled,
        }

    return {
        "what": (
            "H2 external validation, run once over the complete pool under the "
            "pre-registration frozen in docs/IORN-009A_H2_preregistration_v1.0.md "
            "and amended through v1.3."
        ),
        "success_threshold_rho": SUCCESS_RHO,
        "generality_narrowed_to_ct": registry.generality_narrowed_to_ct,
        "scope_note": (
            "The non-CT slot could not be filled, so the generality claim is CT only. "
            "See generality_narrowing_note in data/h2_studies.json."
        )
        if registry.generality_narrowed_to_ct
        else None,
        "per_study": per_study,
        "pools": pools,
        "heterogeneity": {
            "min_within_study_rho": min(rhos) if rhos else None,
            "median_within_study_rho": statistics.median(rhos) if rhos else None,
            "max_within_study_rho": max(rhos) if rhos else None,
        },
        "stratification_by_task_congruence": {
            "note": (
                "Description only. v1.3 section A.2 keeps this out of the success "
                "condition so that a stratum cannot rescue H2. The prediction written "
                "in advance was that the SKE stratum's median within-study rho would "
                "be at least the search stratum's; a clearly higher search stratum "
                "would mean the premise of the stratification was wrong, and that is "
                "reported either way."
            ),
            "strata": strata,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    payload = analyse()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("within-study:")
    for key, value in payload["per_study"].items():
        rho = value["spearman_rho"]
        mark = "pass" if value["meets_threshold"] else "FAIL"
        print(
            f"  {key:10} n={value['n_conditions']:3d}  rho={rho:+.3f}  {mark}"
            f"   ({value['task_congruence']})"
        )
    print("\npools:")
    for name, value in payload["pools"].items():
        if value.get("pooled_rho") is None:
            print(f"  {name:12} (empty)")
            continue
        print(
            f"  {name:12} {value['n_meeting_threshold']}/{value['n_studies']} studies"
            f"   pooled rho={value['pooled_rho']:+.3f}"
            f"   H2 {'REJECTED' if value['h2_rejected'] else 'not rejected'}"
        )
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
