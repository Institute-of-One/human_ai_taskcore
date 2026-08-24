"""Pass-2 digitisation of Paul 2007 (CAND-04), Figure 6 panels (b)(c)(d).

Pixel-based extraction from the embedded raster figure (1495x1334 px,
data/papers/CAND-4_paul2007.pdf p.3593). Pipeline: axis frames and inward
major ticks detected programmatically; filled markers (panels b, d) by
morphological opening + distance-transform peak decomposition of merged
clusters; open circles (panel c) by annulus/interior correlation (R=6.5 px,
two-threshold pass) with visual QC; error bars by walking the thin vertical
line at each marker abscissa (caps = farthest stroke; asymmetric bars kept
separate as plotted).

Axis calibration (all three panels share scale):
  dose: log10, 264.0 px/decade; panel b x(1.0 mGy)=1149.0,
        c x(1.0)=393.5, d x(1.0)=1147.5
  Az:   123.0 px per 0.1; panel b y(1.0)=63.5, c y(1.0)=740.5, d y(1.0)=738.5

The marker lists below are the QC-accepted outputs of that pipeline
(reviewed against the figure overlay). Rerunning this file regenerates
pass2_CAND-04.csv deterministically from these coordinates.

v2 (after pass-1x cross-check by the local session): the distance-transform
peak decomposition had sliced bundled error-bar bands into fake marker
chains (fixed x, ~7 px y-steps). v2 removes peaks whose marker row is
narrower than 11 px AND which sit in a vertical run of >=3 peaks at the
same abscissa (spacing <= 10 px). Removed artifact coordinates:
  panel b: x=1289 y=86..114 (5), x=1369 y=75..110 (6)
  panel d: x=1287 y=811..832 (4), x=1367 y=804..825 (4)
Narrow peaks NOT in such runs are kept, flagged narrow_occluded_uncertain
(3 in panel b, 5 in panel d) for adjudication against pass 1.

Known open items (recorded, not hidden):
- panel b: 10 points read below 1.0 mGy vs "nine measurements" stated in
  section III.C - one point near the 0.68 mGy cluster may be a duplicate
  detection; to be adjudicated against pass 1.
- panel c holds 56 detections (paper max 54): 1-2 possible duplicates in
  the dense >5 mGy region; panels c/d are context-only (not H2 data).
- the paper's 99%-of-maximum statements refer to the fitted curve
  Az = 1 - a*exp(-b*D^c), not to individual technique points, so they
  constrain the digitised set only loosely.
"""

import csv

PXDEC, PX_AZ = 264.0, 1230.0
CAL = {'b': (1149.0, 63.5), 'c': (393.5, 740.5), 'd': (1147.5, 738.5)}

# (x_px, y_px, err_low_Az, err_high_Az); None = no bar recovered
PANEL_B = [  # Task 1, filled circles; v2 chain-rule cleaned
    (1026, 234, 0.0951, 0.0561, ''),
    (1028, 152, 0.0585, 0.0398, ''),
    (1102, 77, None, None, ''),
    (1104, 64, None, None, ''),
    (1105, 86, None, None, 'narrow_occluded_uncertain'),
    (1105, 93, None, None, 'narrow_occluded_uncertain'),
    (1105, 113, None, None, 'narrow_occluded_uncertain'),
    (1108, 104, None, None, ''),
    (1124, 77, 0.0472, 0.0106, ''),
    (1128, 146, 0.0797, 0.039, ''),
    (1161, 66, None, None, ''),
    (1163, 77, 0.0577, None, ''),
    (1181, 64, 0.0236, None, ''),
    (1183, 104, 0.0683, 0.0236, ''),
    (1203, 64, 0.048, None, ''),
    (1210, 64, None, None, ''),
    (1213, 77, 0.0577, None, ''),
    (1234, 84, 0.0602, 0.0106, ''),
    (1241, 64, 0.0089, None, ''),
    (1262, 64, 0.048, None, ''),
    (1287, 77, None, None, ''),
    (1291, 64, None, None, ''),
    (1308, 64, None, None, ''),
    (1313, 77, 0.0577, None, ''),
    (1342, 66, None, None, ''),
    (1343, 75, None, None, ''),
    (1359, 64, 0.048, None, ''),
    (1368, 64, None, None, ''),
    (1390, 63, 0.0488, None, ''),
    (1412, 64, 0.048, None, ''),
    (1422, 64, 0.048, None, ''),
]
PANEL_D = [  # Task 3, filled triangles; v2 chain-rule cleaned (context only)
    (1024, 1012, 0.1049, 0.1431, ''),
    (1100, 871, None, 0.0195, ''),
    (1102, 810, 0.0106, 0.0293, ''),
    (1102, 835, 0.0211, 0.0122, 'narrow_occluded_uncertain'),
    (1104, 899, 0.0927, None, ''),
    (1106, 766, 0.0285, 0.0179, ''),
    (1123, 906, 0.0951, 0.0301, ''),
    (1126, 862, 0.0293, 0.0504, ''),
    (1159, 818, 0.0268, 0.0374, ''),
    (1161, 863, 0.087, 0.0285, ''),
    (1179, 871, 0.0228, 0.0463, ''),
    (1181, 803, 0.0488, 0.0333, ''),
    (1181, 907, 0.0943, 0.022, ''),
    (1209, 819, 0.0789, None, ''),
    (1285, 846, None, None, ''),
    (1287, 803, None, None, ''),
    (1287, 839, None, None, ''),
    (1288, 777, None, None, ''),
    (1288, 791, None, None, 'narrow_occluded_uncertain'),
    (1290, 764, None, None, 'narrow_occluded_uncertain'),
    (1335, 766, None, 0.0098, ''),
    (1337, 739, None, None, ''),
    (1340, 773, 0.0228, 0.0138, ''),
    (1346, 810, 0.0764, 0.0179, ''),
    (1358, 749, 0.0211, None, ''),
    (1367, 743, None, None, ''),
    (1367, 774, None, None, ''),
    (1367, 787, None, None, 'narrow_occluded_uncertain'),
    (1367, 797, None, None, ''),
    (1368, 760, None, None, ''),
    (1387, 770, 0.0642, 0.0114, ''),
    (1411, 739, 0.0488, None, ''),
    (1421, 862, 0.0878, 0.0585, ''),
    (1423, 781, 0.0593, 0.0244, ''),
    (1443, 770, 0.0423, None, ''),
    (1444, 832, 0.0813, 0.0431, ''),
    (1466, 792, 0.0236, 0.0106, 'narrow_occluded_uncertain'),
    (1469, 832, 0.0813, 0.022, ''),
]
PANEL_C = [  # Task 2, variable contrast, open circles (context only)
    (270, 857, 0.087, None),
    (272, 845, None, 0.0447),
    (346, 759, None, 0.013),
    (346, 839, 0.0447, 0.0528),
    (352, 769, 0.0358, None),
    (354, 822, 0.0089, 0.0358),
    (368, 884, 0.0919, 0.0553),
    (372, 795, 0.0659, 0.0293),
    (405, 761, 0.0374, 0.0146),
    (407, 816, 0.0772, 0.0374),
    (421, 800, 0.0114, None),
    (424, 782, 0.0081, 0.0244),
    (448, 788, None, None),
    (452, 774, None, None),
    (452, 799, 0.0293, None),
    (454, 761, None, None),
    (457, 749, None, None),
    (478, 747, None, None),
    (482, 761, None, None),
    (483, 775, 0.0154, None),
    (486, 803, 0.0748, 0.0154),
    (506, 795, 0.0724, 0.0285),
    (537, 761, 0.0602, 0.0163),
    (545, 750, None, None),
    (548, 763, None, None),
    (552, 774, 0.0667, None),
    (557, 747, 0.0154, None),
    (584, 747, None, None),
    (585, 786, None, None),
    (586, 763, None, None),
    (586, 804, None, None),
    (586, 816, 0.0325, None),
    (588, 774, None, None),
    (594, 753, None, 0.0098),
    (607, 759, 0.0098, 0.0122),
    (607, 780, None, 0.0098),
    (607, 791, None, None),
    (607, 807, None, None),
    (613, 739, 0.0081, None),
    (617, 756, 0.0577, None),
    (632, 759, 0.0585, None),
    (636, 748, None, None),
    (658, 741, None, None),
    (663, 751, None, None),
    (663, 793, None, None),
    (668, 740, None, None),
    (673, 751, None, None),
    (673, 771, None, None),
    (678, 761, None, None),
    (683, 827, None, None),
    (684, 750, None, None),
    (684, 771, None, None),
    (684, 793, None, None),
    (690, 740, None, None),
    (712, 761, 0.0602, 0.0106),
    (716, 741, 0.0106, None),
]

FIELDS = ["study_id","figure","panel","series","observer_type","recon",
          "dose_label","dose_value","dose_unit","diameter_mm","y_value",
          "y_err_low","y_err_high","pass_id","extractor","method","notes"]
META = dict(pass_id=2, extractor="Cowork Claude session",
            method="pixel extraction, extract_paul2007.py")

def rows():
    out = []
    def add(panel, task, x, y, e_lo, e_hi, note=""):
        X1, Y1 = CAL[panel]
        dose = 10 ** ((x - X1) / PXDEC)
        az = 1.0 - (y - Y1) / PX_AZ
        out.append(dict(study_id="CAND-04", figure="Fig6", panel=panel,
            series=f"human_task{task}", observer_type="human", recon="",
            dose_label=f"{dose:.2f} mGy", dose_value=round(dose, 3),
            dose_unit="mGy", diameter_mm=(3.2 if task == 1 else ""),
            y_value=round(az, 4),
            y_err_low=(round(e_lo, 4) if e_lo else ""),
            y_err_high=(round(e_hi, 4) if e_hi else ""), notes=note, **META))
    for x, y, lo, hi, nt in PANEL_B: add('b', 1, x, y, lo, hi, nt)
    for x, y, lo, hi, nt in PANEL_D: add('d', 3, x, y, lo, hi, nt)
    for x, y, lo, hi in PANEL_C: add('c', 2, x, y, lo, hi)
    return out

if __name__ == "__main__":
    rs = rows()
    with open("pass2_CAND-04.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for r in rs: w.writerow(r)
    print("wrote pass2_CAND-04.csv,", len(rs), "rows")
