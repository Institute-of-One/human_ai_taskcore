# H2 digitisation targets, v1 (2026-08-24)

Work order for criterion C6 of the frozen pre-registration: every performance
value that a study reports only in a figure has to be recovered by **two
independent digitisations agreeing to within 5%**.

## How independence is constituted

The pre-registration requires two independent passes. We constitute them as
**different extractor and different method**, which is stricter than two passes
by one person with one tool, and is recorded here so that the strengthening is
visible and cannot be mistaken for a relaxation of C6:

| Pass | Extractor | Method | Output |
|---|---|---|---|
| 1 | S. Yamamoto | WebPlotDigitizer, manual point picking | CSV, schema below |
| 2 | Cowork session | pixel-based script: render the figure at high DPI, detect axes, detect markers; code and coordinates committed so the pass is deterministically reproducible | CSV, same schema |

C6 verdict = maximum absolute deviation between passes, per point, expressed as
a percentage of the value. Report the maximum, not the mean. If any point
exceeds 5%, that point is resolved by a third pass or the study's condition set
is reduced, and either outcome is recorded.

## The stronger check: text anchors

Both papers state some of their figure values numerically in the running text.
These are **not** to be entered from the text and then also digitised as if
independent. They are held out as anchors: each pass must reproduce them from
the figure alone to within 5%, which tests the digitisation against ground
truth rather than only against the other pass. Two passes can agree and both be
wrong; an anchor catches that.

Enter the anchored conditions in the registry using the **text values**, since a
printed number beats a recovered one, and record the digitised value alongside
as the accuracy evidence.

## Study 1 — Yu 2013

Yu L, Leng S, Chen L, Kofler JM, Carter RE, McCollough CH. *Med Phys*
2013;40(4):041908. Local copy `data/papers/CAND-1_yu2013.pdf`.

Metric: percent correct in a 2AFC task, four human observers. Error bars are
standard errors, i.e. 68% intervals, for both human and model series
(section II.C and III.B) — do not read them as 95%.

### Figure 7 (p. 041908-6): FBP, 15 tasks

- 5 dose levels: 60, 120, 240, 360, 480 quality reference mAs
  (CTDIvol 2.8, 5.7, 11.4, 17.1, 22.8 mGy)
- 3 lesion sizes: 3, 5, 9 mm
- Two series per size: **human (filled squares)** and CHO model (empty squares)
- Required: 15 human points, with error bars. Digitise the 15 model points too
  and keep them in the CSV: they are not H2 data, but they enable the
  Bland-Altman cross-check below.

### Figure 9 (p. 041908-7): IR, 6 tasks

- 2 dose levels: 60, 120 mAs; 3 lesion sizes: 3, 5, 9 mm
- Same two series. The FBP series is redrawn here for reference; check it
  against Figure 7 rather than entering it twice.
- Required: 6 human points, with error bars.

### Anchors, from section III.D (p. 041908-7)

| Size | Dose | Recon | Human | Model |
|---|---|---|---|---|
| 5 mm | 60 mAs | FBP | 88.3 ± 2.7 | 86.5 ± 3.2 |
| 5 mm | 60 mAs | IR | 91.5 ± 2.1 | 91.3 ± 2.9 |
| 5 mm | 120 mAs | FBP | 92.5 ± 1.8 | 92.4 ± 2.6 |
| 5 mm | 120 mAs | IR | 98.3 ± 0.9 | 97.6 ± 1.4 |
| 3 mm | 120 mAs | FBP | 79.8 ± 2.8 | 78.3 ± 4.1 |
| 3 mm | 120 mAs | IR | 68.8 ± 3.0 | 77.4 ± 3.8 |

Six of the 21 human points are therefore anchored. Note the 3 mm 120 mAs IR
point: the humans did worse than at 60 mAs, which the paper flags as an
anomaly. It stays in — the pre-registration has no provision for dropping a
point for being surprising, and it is exactly the kind of point that a
model-versus-human comparison should have to face.

### Independent constraints (checks on the whole set, not on single points)

- Figure 8: Bland-Altman for the 15 FBP tasks; mean absolute human-model
  difference 1.0% ± 1.1%, limits [−3.3%, 2.4%]
- Figure 10: all 21 tasks; mean absolute difference 1.0% ± 1.0%, limits
  [−3.2%, 2.2%]; for the 6 IR tasks alone, [−8.8%, 5.2%]; excluding the
  −8.6% outlier, [−3.0%, 2.1%]
- Correlations, for reference: overall Pearson 0.986 (FBP), 0.985 (IR); by
  size 0.982 (3 mm), 0.981 (5 mm), 0.948 (9 mm)

If the digitised human and model series do not reproduce these summary
statistics, the digitisation is wrong even if both passes agree.

## Study 2 — Paul 2007

Paul NS, Siewerdsen JH, Patsios D, Chung T-B. *Med Phys* 2007;34(9):3587–3595.
Local copy `data/papers/CAND-4_paul2007.pdf`.

Metric: proportion correct in a 2AFC test, taken equal to A_z, nine observers
(four radiologists, five physicists). Error bars are 95% binomial confidence
limits, and are asymmetric (section II.C) — record low and high separately.

### Figure 6 (p. 3593)

- Panel (a): all three tasks on a linear axis, with an inset near the low-dose
  shoulder. Panels (b), (c), (d): task 1, 2, 3 individually on a **semilog**
  dose axis.
- **Digitise panels (b), (c), (d), not (a).** The semilog axis resolves the
  low-dose region, which is where the whole result lives, and panel (a) is the
  same data compressed.
- **Only task 1 is required** (panel b): the solid 3.2 mm nodule at +23 HU, the
  one task in which the observer knows size and contrast. Tasks 2 and 3 vary
  the signal within the trial set and fall outside the declared scope of
  signal-specified detection (protocol section 2.1). Digitise (c) and (d)
  anyway and keep them in the CSV, labelled — they cost little, and the
  contrast between a signal-specified and a signal-unknown task is worth
  having in the heterogeneity discussion.
- Expect up to 54 dose points per task (3 kVp × 6 mA × 3 slice thicknesses,
  0.34 to 26.4 mGy), though points may overlap where techniques coincide in
  dose. Record the dose as read; do not snap it to a nominal value.

### Anchors, from section III.C (p. 3593)

These are stated as thresholds rather than as point values, so they constrain
the curve instead of fixing single points:

| Task | Statement |
|---|---|
| 1 | A_z within 99% of its maximum down to 1.0 mGy; saturates at 100% above 10 mGy |
| 2 | within 99% of maximum down to 5.0 mGy, within 95% down to 1.0 mGy |
| 3 | mean 98% above 10 mGy; 99% of that level down to 7.0 mGy; 90% at 1.0 mGy |

Nine measurements lie below 1 mGy (section III.C) — that count is a check on
the low-dose end of the digitised set.

## CSV schema (both passes, one file per pass)

```
study_id,figure,panel,series,observer_type,recon,dose_label,dose_value,dose_unit,diameter_mm,y_value,y_err_low,y_err_high,pass_id,extractor,method,notes
```

- `observer_type`: `human` or `model_cho`
- `y_value`: percent correct or A_z **as plotted**, in the figure's own units;
  no rescaling, no rounding beyond what can be read
- `y_err_low` / `y_err_high`: as plotted; leave blank if no bar is drawn
- one row per marker; do not average across markers
- `pass_id`: `1` or `2`

Deposit as `data/h2_digitisation/pass1_<study_id>.csv` and
`pass2_<study_id>.csv`. These are extracted coordinates rather than the papers,
so they are committed — the figures they came from are not.

## What happens next, and what must not

Once both passes exist for a study, the deviation check runs and the condition
points enter `data/h2_studies.json` with their provenance. Rank agreement still
does not run: `ptx.h2_reproduce.gate_pool` holds until the pool requirements
are met, so no study's ρ is visible while the pool is still being assembled.
