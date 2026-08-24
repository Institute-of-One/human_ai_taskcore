"""Deviation check for criterion C6.

Two passes agree when every matched point differs by no more than 5%. The
maximum is what gets reported, not the mean: an average hides the one point
that was read wrong, and it is the wrong point that would move a rank.

Saturated points (fraction correct >= 99.5%) are reported separately. Markers
pinned at the ceiling coincide, so both passes can recover the same number
for reasons that have nothing to do with either pass being accurate. Folding
those into one statistic would dilute the check with points that cannot fail
it.

Paul 2007 is handled as a reduced condition set, not a full-set fail. The
pre-registration (digitisation targets v1, criterion C6) allows a point to be
resolved by a third pass *or the study's condition set to be reduced*, with
either outcome recorded. The reduced set is the separable points: every
non-saturated marker that is not a ``narrow_occluded_uncertain`` leftover,
plus every saturated marker that sits alone at its dose. The occluded
0.66-0.70 mGy pile and the Az = 1.000 stacks whose cardinality cannot be
recovered independently of method are dropped, and the drop is the record.

    python data/h2_digitisation/compare_passes.py
"""

from __future__ import annotations

import csv
import pathlib

HERE = pathlib.Path(__file__).parent

# Markers closer than this in dose overlap on Paul 2007 Fig. 6 (6.5 px radius
# on an axis of 264 px/decade).
DOSE_TOLERANCE = 0.06
SATURATED_FRACTION = 0.995
C6_LIMIT_PERCENT = 5.0


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)]


def get(row, field):
    return (row.get(field) or "").strip()


def number(row, field):
    text = get(row, field)
    return float(text) if text else None


def as_fraction(y):
    """Yu plots percent; Paul plots A_z in 0-1. Compare on the unit interval."""
    return y / 100.0 if y > 2.0 else y


def is_saturated(y):
    return as_fraction(y) >= SATURATED_FRACTION


def condition_key(row):
    """Physical condition, independent of either pass's naming."""
    diameter = number(row, "diameter_mm")
    return (
        round(diameter, 1) if diameter is not None else None,
        get(row, "observer_type"),
        get(row, "recon").upper(),
        get(row, "dose_label").lower().replace(" ", ""),
    )


def deviation_percent(a, b):
    a, b = as_fraction(a), as_fraction(b)
    scale = max(abs(a), abs(b))
    return 0.0 if scale == 0 else 100.0 * abs(a - b) / scale


def compare_yu():
    rows1 = load(HERE / "pass1x_CAND-01.csv")
    rows2 = load(HERE / "pass2_CAND-01.csv")
    index2 = {condition_key(row): row for row in rows2}

    matched = []
    only1 = []
    for row in rows1:
        key = condition_key(row)
        other = index2.get(key)
        if other is None:
            only1.append(key)
            continue
        y1, y2 = number(row, "y_value"), number(other, "y_value")
        matched.append(
            {
                "key": key,
                "y1": y1,
                "y2": y2,
                "deviation_percent": deviation_percent(y1, y2),
                "saturated": is_saturated(y1) or is_saturated(y2),
            }
        )
    only2 = sorted(set(index2) - {condition_key(r) for r in rows1})

    unsaturated = [m for m in matched if not m["saturated"]]
    saturated = [m for m in matched if m["saturated"]]
    worst_unsat = max((m["deviation_percent"] for m in unsaturated), default=0.0)
    worst_sat = max((m["deviation_percent"] for m in saturated), default=0.0)
    over = [m for m in unsaturated if m["deviation_percent"] > C6_LIMIT_PERCENT]
    return {
        "study": "CAND-01",
        "n_matched": len(matched),
        "n_unsaturated": len(unsaturated),
        "n_saturated": len(saturated),
        "max_deviation_unsaturated_percent": worst_unsat,
        "max_deviation_saturated_percent": worst_sat,
        "digitisation_repeat_max_deviation": worst_unsat / 100.0,
        "only_pass1x": only1,
        "only_pass2": only2,
        "over_limit": over,
        "verdict": "PASS" if matched and not over else "FAIL",
    }


def is_uncertain(row):
    return "narrow_occluded_uncertain" in get(row, "notes")


def paul_task1_pass2():
    return [
        row
        for row in load(HERE / "pass2_CAND-04.csv")
        if get(row, "panel") == "b" and "task1" in get(row, "series")
    ]


def paul_reduction(rows=None):
    """Split Paul 2007 task 1 into the reduced (kept) set and the dropped set.

    Kept: every marker that is not ``narrow_occluded_uncertain``, including
    isolated saturated points (one marker at that dose). Dropped: the eight
    ``narrow_occluded_uncertain`` leftovers (three on panel b, five on
    panel d) and, were any to remain, same-dose saturated stacks. Section
    III.C's nine measurements below 1 mGy remain the paper's count; seven of
    them are in the kept set and two sit in the occluded 0.66-0.70 mGy pile
    that neither method can separate.
    """
    rows = rows if rows is not None else paul_task1_pass2()
    by_dose = {}
    for row in rows:
        by_dose.setdefault(number(row, "dose_value"), []).append(row)

    kept, dropped = [], []
    for dose, group in sorted(by_dose.items()):
        uncertain = [row for row in group if is_uncertain(row)]
        clean = [row for row in group if not is_uncertain(row)]
        dropped.extend(
            {**row, "_reason": "narrow_occluded_uncertain, not confirmed by pass 1x"}
            for row in uncertain
        )
        if len(clean) > 1 and all(
            is_saturated(number(row, "y_value")) for row in clean
        ):
            dropped.extend(
                {**row, "_reason": "saturated stack, cardinality method-dependent"}
                for row in clean
            )
            continue
        kept.extend(clean)
    return kept, dropped


def match_pass1x_to_kept(kept):
    """One-to-one match from pass 1x onto the reduced pass-2 set.

    Each pass-1x point is paired to the unused kept point nearest in dose
    (within 25%, the pass-1x log-axis tolerance) and then in y. Pairing on
    y is used only to break a dose tie, never to search the whole panel:
    that would manufacture the agreement C6 is supposed to test.
    """
    rows1 = load(HERE / "pass1x_CAND-04.csv")
    unused = list(kept)
    matched, unmatched = [], []
    for row in rows1:
        dose1, y1 = number(row, "dose_value"), number(row, "y_value")
        near = [
            other
            for other in unused
            if abs(number(other, "dose_value") - dose1) / dose1 <= 0.25
        ]
        if not near:
            unmatched.append(row)
            continue
        other = min(
            near,
            key=lambda r: abs(number(r, "dose_value") - dose1) / dose1
            + abs(as_fraction(number(r, "y_value")) - as_fraction(y1))
            / max(as_fraction(y1), 1e-9),
        )
        unused.remove(other)
        matched.append(
            {
                "dose_pass1x": dose1,
                "dose_pass2": number(other, "dose_value"),
                "y1": y1,
                "y2": number(other, "y_value"),
                "deviation_percent": deviation_percent(y1, number(other, "y_value")),
                "saturated": is_saturated(y1) or is_saturated(number(other, "y_value")),
            }
        )
    return matched, unmatched


def compare_paul():
    kept, dropped = paul_reduction()
    matched, unmatched = match_pass1x_to_kept(kept)
    unsaturated = [m for m in matched if not m["saturated"]]
    saturated = [m for m in matched if m["saturated"]]
    worst_unsat = max((m["deviation_percent"] for m in unsaturated), default=0.0)
    worst_sat = max((m["deviation_percent"] for m in saturated), default=0.0)
    over = [m for m in unsaturated if m["deviation_percent"] > C6_LIMIT_PERCENT]
    below1_kept = sum(1 for row in kept if number(row, "dose_value") < 1.0)
    return {
        "study": "CAND-04",
        "n_pass2_task1": len(paul_task1_pass2()),
        "n_kept": len(kept),
        "n_dropped": len(dropped),
        "n_below_1_mgy_kept": below1_kept,
        "n_below_1_mgy_paper": 9,
        "n_matched": len(matched),
        "n_unsaturated": len(unsaturated),
        "n_saturated": len(saturated),
        "max_deviation_unsaturated_percent": worst_unsat,
        "max_deviation_saturated_percent": worst_sat,
        "digitisation_repeat_max_deviation": worst_unsat / 100.0,
        "unmatched_pass1x": unmatched,
        "over_limit": over,
        "kept": kept,
        "dropped": dropped,
        "matched": matched,
        "verdict": "PASS_REDUCED" if matched and not over else "FAIL",
    }


def report_yu(result):
    print(f"=== {result['study']} ===")
    print(
        f"matched {result['n_matched']} points "
        f"(unsaturated {result['n_unsaturated']}, "
        f"saturated {result['n_saturated']}, threshold {SATURATED_FRACTION:g})"
    )
    print(
        f"  unsaturated: max deviation "
        f"{result['max_deviation_unsaturated_percent']:.2f}%"
    )
    print(
        f"  saturated:   max deviation "
        f"{result['max_deviation_saturated_percent']:.2f}%"
    )
    for item in result["over_limit"]:
        print(
            f"    OVER 5%: {item['key']}  {item['y1']} vs {item['y2']} -> "
            f"{item['deviation_percent']:.2f}%"
        )
    print(f"  C6 verdict: {result['verdict']}")
    print()


def report_paul(result):
    print(f"=== {result['study']} (reduced condition set) ===")
    print(
        f"pass 2 task 1: {result['n_pass2_task1']} detections; "
        f"kept {result['n_kept']}, dropped {result['n_dropped']}"
    )
    print(
        f"below 1 mGy: {result['n_below_1_mgy_kept']} kept "
        f"(paper section III.C states {result['n_below_1_mgy_paper']}; "
        "the two missing sit in the occluded 0.66-0.70 mGy pile)"
    )
    print(
        f"matched against pass 1x: {result['n_matched']} "
        f"(unsaturated {result['n_unsaturated']}, "
        f"saturated {result['n_saturated']})"
    )
    print(
        f"  unsaturated: max deviation "
        f"{result['max_deviation_unsaturated_percent']:.2f}%"
    )
    print(
        f"  saturated:   max deviation "
        f"{result['max_deviation_saturated_percent']:.2f}%"
    )
    for item in result["over_limit"]:
        print(
            f"    OVER 5%: {item['dose_pass1x']} vs {item['dose_pass2']}  "
            f"{item['y1']} vs {item['y2']} -> {item['deviation_percent']:.2f}%"
        )
    print(f"  C6 verdict: {result['verdict']}")
    print()


def adjudicate_uncertain():
    """The eight narrow_occluded_uncertain leftovers against pass 1x."""
    rows = load(HERE / "pass2_CAND-04.csv")
    flagged = [row for row in rows if is_uncertain(row)]
    decisions = []
    for row in flagged:
        panel = get(row, "panel")
        dose = number(row, "dose_value")
        y = number(row, "y_value")
        if panel == "b":
            decision = (
                "drop",
                "pass 1x already accounts for three markers in the "
                "0.66-0.70 mGy cluster (0.993, 0.998, 0.975) against the "
                "three clean pass-2 detections; these three extras are the "
                "occlusion leftovers that made pass 2 read ten points below "
                "1 mGy against the paper's nine",
            )
        else:
            decision = (
                "drop",
                "panel d is task 3 (context only, not H2 data); pass 1x did "
                "not read this panel, so the flag cannot be confirmed",
            )
        decisions.append(
            {
                "panel": panel,
                "dose_mgy": dose,
                "y": y,
                "decision": decision[0],
                "reason": decision[1],
            }
        )
    return decisions


if __name__ == "__main__":
    yu = compare_yu()
    paul = compare_paul()
    report_yu(yu)
    report_paul(paul)
    print("=== CAND-04: narrow_occluded_uncertain adjudication ===")
    for item in adjudicate_uncertain():
        print(
            f"  panel {item['panel']}  {item['dose_mgy']:.3f} mGy  "
            f"Az={item['y']:.4f}  -> {item['decision']}"
        )
        print(f"    {item['reason']}")
