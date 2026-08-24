# CAND-04 (Paul 2007) — C6 by reduction of the condition set

**Date:** 2026-08-24
**Criterion:** pre-registration C6, as restated in `docs/h2_digitisation_targets_v1.md`: if two independent digitisations do not agree to 5% on a point, *that point is resolved by a third pass or the study's condition set is reduced, and either outcome is recorded*.
**This document is the record of the second path.** It is not a full-set fail and it is not a silent drop.

## What was reduced, and why

Paul 2007 Figure 6(b) (task 1, the only task in scope) cannot be recovered marker-for-marker. Two facts, neither of them about the performance values themselves:

1. **Saturated Az = 1.000 clusters.** Above about 1 mGy the points sit on the ceiling. Where several techniques land on the same dose their markers coincide, and the number of markers in the pile cannot be recovered independently of the extraction method. Those clusters also carry no rank information: every kept value would be a tie at the ceiling.
2. **The 0.66–0.70 mGy pile.** The embedded raster is 1495×1334 px for four panels. In this pile the markers (radius 6.5 px) overlap on a 6 px abscissa that the fitted curve also crosses. Pass 1x sees three markers, pass 2 v2 sees six of which three are flagged `narrow_occluded_uncertain`. Section III.C states **nine measurements below 1 mGy**; that count is the paper's, and it is kept as the truth. Seven of the nine are separable and stay in the set. Two remain inside this pile and are not recovered.

Pass 2 v2 already removed 19 chain-rule artifacts (error-bar strokes decomposed as markers). That cleaning is not this reduction; it is a defect fix, recorded in `data/h2_digitisation/pass2_code/extract_paul2007.py`.

## Adjudication of the eight `narrow_occluded_uncertain` flags

| Panel | Dose (pass 2) | Az | Decision | Against pass 1x |
|---|---|---|---|---|
| b | 0.681 mGy | 0.9817 | drop | Pass 1x already has three cluster readings (0.993, 0.998, 0.975) matching the three *clean* pass-2 detections. These three extras are what made pass 2 read ten points below 1 mGy against the paper's nine. |
| b | 0.681 mGy | 0.9760 | drop | same |
| b | 0.681 mGy | 0.9598 | drop | same |
| d | 0.672 mGy | 0.9215 | drop | Panel d is task 3 (context only, not H2 data). Pass 1x did not read it. |
| d | 3.406 mGy | 0.9573 | drop | same |
| d | 3.466 mGy | 0.9793 | drop | same |
| d | 6.783 mGy | 0.9606 | drop | same |
| d | 16.086 mGy | 0.9565 | drop | same |

Panel d doses in the table are indicative; the five flags live in `pass2_CAND-04.csv` with `notes=narrow_occluded_uncertain`. None of them enter the registry.

## The kept set

Every task-1 marker that is not one of those eight flags, including isolated saturated points (one marker at that dose). Same-dose saturated stacks, if any remain after the chain-rule cleaning, are dropped. The kept list is the output of `compare_passes.paul_reduction()` and is written into `data/h2_studies.json` as `paul2007.conditions`.

C6 on the reduced set is the maximum deviation between pass 1x and pass 2 on the unsaturated matched points, reported separately from the saturated matched points (`compare_passes.py`, threshold 99.5%).

## Value convention

- **x (dose):** Yamamoto WebPlotDigitizer pass 1 is the adopted source. Until that pass is delivered, the registry stores the pass-2 axis calibration (pixel-calibrated; pass 1x is only good to about 15% on a log axis and cannot land in the right cluster).
- **y (Az):** the first-pass value, never the average of the two passes. Where pass 1x has a match, that reading is stored; otherwise pass 2.
- Section III.C's nine-below-1-mGy count is not a licence to invent the two unrecoverable points.

## What this is not

It is not an exclusion. Paul 2007 remains in `studies` because C1–C5 were already passed on the PDF and C6 is satisfied on the reduced set. Rank degeneracy at the ceiling is recorded here and will be visible in the heterogeneity discussion; it is not a C-criterion and is not used to drop the study.
