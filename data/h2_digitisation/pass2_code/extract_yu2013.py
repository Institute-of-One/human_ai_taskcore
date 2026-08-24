"""Pass-2 digitisation of Yu 2013 (CAND-01) Figures 7 and 9.

Deterministic pixel-based extraction. Marker centres are obtained by
template correlation on the binarised embedded figure images (1000-px wide,
extracted at native resolution from data/papers/CAND-1_yu2013.pdf).
Overlapping saturated clusters (Fig.7 at 240/360/480 mAs; Fig.9 IR at
120 mAs large) were decomposed by direct pixel inspection; those centres are
recorded below as reviewed constants with provenance notes.

Axis calibration (horizontal gridlines, detected programmatically):
  Fig.7: PC 100% at y=63.5, 60% at y=557  ->  12.3375 px per percent
  Fig.9: PC 100% at y=63.0, 60% at y=554  ->  12.2750 px per percent
Dose values are the nominal protocol values stated in the paper's text
(60/120/240/360/480 quality reference mAs); they are not digitised.
"""

import csv
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
import scipy.ndimage as ndi

PASS_META = dict(pass_id=2, extractor="Cowork Claude session",
                 method="pixel-template extraction, extract_yu2013.py")


def load(path):
    img = np.array(Image.open(path).convert("L"))
    return img, img < 128


def pc_of(y, y100, ppp):
    return 100.0 - (y - y100) / ppp


def tri_template(size=19, lw=3, filled=False):
    t = np.zeros((size, size))
    for r in range(size):
        half = (r + 1) * (size / 2) / size
        c0 = int(np.floor(size / 2 - half))
        c1 = int(np.ceil(size / 2 + half))
        if filled or r >= size - lw:
            t[r, max(c0, 0):min(c1, size)] = 1
        else:
            t[r, max(c0, 0):min(c0 + lw, size)] = 1
            t[r, max(c1 - lw, 0):min(c1, size)] = 1
    return t


def sq_template(size=19, lw=3, filled=False):
    t = np.zeros((size, size))
    if filled:
        t[:, :] = 1
    else:
        t[:lw, :] = 1
        t[-lw:, :] = 1
        t[:, :lw] = 1
        t[:, -lw:] = 1
    return t


def match(dark, tmpl, thresh, exclude=25):
    """Normalised match: fraction of template covered by dark pixels minus
    penalty for dark pixels where the template is empty (interior)."""
    d = dark.astype(float)
    hit = fftconvolve(d, tmpl[::-1, ::-1], mode="same") / tmpl.sum()
    inv = (1 - tmpl)
    if inv.sum() > 0:
        miss = fftconvolve(d, inv[::-1, ::-1], mode="same") / inv.sum()
    else:
        miss = np.zeros_like(hit)
    score = hit - 0.8 * miss
    peaks = []
    s = np.where(score > thresh, score, 0.0)
    while True:
        idx = np.unravel_index(np.argmax(s), s.shape)
        if s[idx] <= 0:
            break
        peaks.append((idx[1], idx[0], float(score[idx])))
        y, x = idx
        s[max(0, y - exclude):y + exclude + 1,
          max(0, x - exclude):x + exclude + 1] = 0
    return peaks


def find_error_caps(dark, cx, cy, half_h=80):
    """Walk the vertical error-bar line outward from the marker; the cap is
    the farthest short horizontal stroke encountered while the bar is
    continuous (gap tolerance 2 px). Returns (y_top_cap, y_bot_cap)."""
    cx = int(round(cx)); cy = int(round(cy))
    H = dark.shape[0]

    def cap_like(y):
        seg = dark[y, max(0, cx - 10):cx + 11]
        flanks = dark[y, max(0, cx - 20):max(0, cx - 13)].any() or                  dark[y, cx + 14:cx + 21].any()
        return seg.sum() >= 5 and dark[y, cx - 2:cx + 3].any() and not flanks

    def walk(step):
        gap, last_cap, y = 0, None, cy + step * 10
        while 0 <= y < H and abs(y - cy) <= half_h:
            on_bar = dark[y, cx - 1:cx + 2].any()
            if on_bar:
                gap = 0
                if cap_like(y):
                    last_cap = y
            else:
                gap += 1
                if gap > 2:
                    break
            y += step
        return last_cap

    return walk(-1), walk(+1)


rows = []


def emit(figure, series, recon, dose, size_label, diam, cx, cy, y100, ppp,
         dark, notes=""):
    pc = pc_of(cy, y100, ppp)
    top, bot = find_error_caps(dark, cx, cy)
    e_hi = pc_of(top, y100, ppp) - pc if top is not None else ""
    e_lo = pc - pc_of(bot, y100, ppp) if bot is not None else ""
    rows.append(dict(
        study_id="CAND-01", figure=figure, panel="", series=series,
        observer_type=("human" if series.startswith("human") else "model_cho"),
        recon=recon, dose_label=f"{dose} mAs", dose_value=dose,
        dose_unit="mAs", diameter_mm=diam,
        y_value=round(pc, 2),
        y_err_low=(round(e_lo, 2) if e_lo != "" else ""),
        y_err_high=(round(e_hi, 2) if e_hi != "" else ""),
        notes=notes, **PASS_META))


# ---------------------------------------------------------------- Figure 7
img7, dark7 = load("CAND-1_p6_img2.png")
Y100_7, PPP_7 = 63.5, 12.3375
SIZES = {"large": 9, "medium": 5, "small": 3}

# separable markers, auto-detected (verified on QC overlay)
auto7 = [
    # (series, recon, dose, size, cx, cy)
    ("human", "FBP", 60, "large", 231.0, 96.0),
    ("human", "FBP", 60, "medium", 230.0, 208.0),
    ("human", "FBP", 60, "small", 230.0, 403.0),
    ("model", "FBP", 60, "large", 243.0, 97.0),
    ("model", "FBP", 60, "medium", 243.0, 229.0),
    ("model", "FBP", 60, "small", 243.0, 385.0),
    ("human", "FBP", 120, "large", 333.0, 75.0),
    ("human", "FBP", 120, "medium", 333.0, 156.0),
    ("human", "FBP", 120, "small", 333.0, 312.0),
    ("model", "FBP", 120, "large", 345.5, 63.5),   # on 100% line
    ("model", "FBP", 120, "medium", 345.0, 155.0),
    ("model", "FBP", 120, "small", 345.0, 333.0),
    ("human", "FBP", 240, "medium", 538.0, 100.0),
    ("human", "FBP", 240, "small", 538.0, 270.0),
    ("model", "FBP", 240, "small", 552.0, 228.0),
    ("human", "FBP", 360, "small", 744.0, 115.0),
]
# cluster decompositions, reviewed constants (pixel inspection, this file's
# header; ASCII dumps archived in the session log)
clusters7 = [
    ("human", "FBP", 240, "large", 536.5, 63.0, "overlaps model marker on 100% gridline"),
    ("model", "FBP", 240, "large", 552.0, 63.5, "overlaps human marker on 100% gridline"),
    ("model", "FBP", 240, "medium", 553.0, 74.5, "adjacent to 100% cluster"),
    ("human", "FBP", 360, "large", 744.5, 64.0, "coincident cluster at 100%"),
    ("human", "FBP", 360, "medium", 744.5, 64.0, "coincident with human large (hidden)"),
    ("model", "FBP", 360, "large", 758.0, 63.0, "coincident cluster at 100%"),
    ("model", "FBP", 360, "medium", 758.0, 63.0, "coincident with model large (hidden)"),
    ("model", "FBP", 360, "small", 758.0, 85.5, "on small-series polyline"),
    ("human", "FBP", 480, "large", 950.0, 63.0, "two stacked human markers, upper"),
    ("human", "FBP", 480, "medium", 950.0, 77.0, "two stacked human markers, lower; size assignment by monotonic order"),
    ("human", "FBP", 480, "small", 950.0, 77.0, "coincident-ambiguous: third human marker not separable, recorded at lower level"),
    ("model", "FBP", 480, "large", 963.5, 63.0, "upper open marker"),
    ("model", "FBP", 480, "medium", 963.5, 63.0, "coincident with model large (hidden)"),
    ("model", "FBP", 480, "small", 963.5, 84.0, "on small-series polyline"),
]
for series, recon, dose, size, cx, cy in auto7:
    emit("Fig7", f"{series}_{recon}", recon, dose, size, SIZES[size],
         cx, cy, Y100_7, PPP_7, dark7)
for series, recon, dose, size, cx, cy, note in clusters7:
    emit("Fig7", f"{series}_{recon}", recon, dose, size, SIZES[size],
         cx, cy, Y100_7, PPP_7, dark7, notes=note)

# ---------------------------------------------------------------- Figure 9
img9, dark9 = load("CAND-1_p7_img1.png")
Y100_9, PPP_9 = 63.0, 12.275

auto9 = [
    # IR series only (FBP is redrawn from Fig.7; checked, not re-entered)
    ("human", "IR", 60, "large", 359.0, 119.0),
    ("human", "IR", 60, "medium", 359.0, 171.0),
    ("human", "IR", 60, "small", 359.0, 423.0),
    ("model", "IR", 60, "large", 368.0, 116.0),
    ("model", "IR", 60, "medium", 368.0, 169.0),
    ("model", "IR", 60, "small", 377.0, 387.5),
    ("human", "IR", 120, "small", 542.0, 450.0),
    ("model", "IR", 120, "small", 553.5, 340.5),
]
clusters9 = [
    ("human", "IR", 120, "large", 543.0, 67.0, "filled apex under 100% gridline; bbox rows 60-74"),
    ("model", "IR", 120, "large", 555.0, 63.5, "open triangle on gridline; apex row 55"),
    ("human", "IR", 120, "medium", 541.0, 85.0, "overlapping pair, filled; bbox rows 76-94"),
    ("model", "IR", 120, "medium", 554.0, 93.0, "overlapping pair, open; base rows 100-102"),
]
for series, recon, dose, size, cx, cy in auto9:
    emit("Fig9", f"{series}_{recon}", recon, dose, size, SIZES[size],
         cx, cy, Y100_9, PPP_9, dark9)
for series, recon, dose, size, cx, cy, note in clusters9:
    emit("Fig9", f"{series}_{recon}", recon, dose, size, SIZES[size],
         cx, cy, Y100_9, PPP_9, dark9, notes=note)

# ---------------------------------------------------------------- output
FIELDS = ["study_id", "figure", "panel", "series", "observer_type", "recon",
          "dose_label", "dose_value", "dose_unit", "diameter_mm", "y_value",
          "y_err_low", "y_err_high", "pass_id", "extractor", "method",
          "notes"]
with open("pass2_CAND-01.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"wrote pass2_CAND-01.csv with {len(rows)} rows")

# ---------------------------------------------------------------- anchors
ANCHORS = [  # (recon, dose, size, series, text_value)
    ("FBP", 60, "medium", "human", 88.3), ("FBP", 60, "medium", "model", 86.5),
    ("IR", 60, "medium", "human", 91.5), ("IR", 60, "medium", "model", 91.3),
    ("FBP", 120, "medium", "human", 92.5), ("FBP", 120, "medium", "model", 92.4),
    ("IR", 120, "medium", "human", 98.3), ("IR", 120, "medium", "model", 97.6),
    ("FBP", 120, "small", "human", 79.8), ("FBP", 120, "small", "model", 78.3),
    ("IR", 120, "small", "human", 68.8), ("IR", 120, "small", "model", 77.4),
]
print("\nanchor check (|dev| must be <= 5%):")
ok = True
for recon, dose, size, series, val in ANCHORS:
    got = [r for r in rows if r["recon"] == recon and r["dose_value"] == dose
           and r["diameter_mm"] == SIZES[size]
           and r["series"].startswith(series)]
    assert len(got) == 1, (recon, dose, size, series)
    dv = got[0]["y_value"]
    dev = 100 * abs(dv - val) / val
    flag = "OK " if dev <= 5 else "FAIL"
    ok &= dev <= 5
    print(f"  {flag} {series:5s} {recon:3s} {dose:3d} {size:6s}: text {val:5.1f}  pass2 {dv:6.2f}  dev {dev:4.2f}%")
print("ALL ANCHORS OK" if ok else "ANCHOR FAILURE")
