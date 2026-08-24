"""Pass-1x rendering: regenerate exactly the images that were read.

Pass 1x is an independent reading of the same figures that pass 2 extracted by
script. The method is deliberately different: the page is rendered to a raster
at high DPI, cropped to one band of one figure at a time, and the marker
positions are read against the printed gridlines. No axis fitting and no
detection -- the gridlines are the ruler.

That makes it weak in x (a dose read off a log axis by eye is good to roughly
15%) and strong in y (a percent-correct value read between gridlines 10% apart
is good to a few tenths of a percent). Pass 2 is the reverse: exact in x because
it calibrates the axis in pixels, but vulnerable to mistaking a feature for a
marker. The two failure modes do not overlap, which is the point of running
both.

The crops below are the ones the reading was taken from, so the reading can be
audited against the same pixels.

    python data/h2_digitisation/pass1x_code/render_pages.py

Writes to data/papers/qc_pass1/, which is gitignored: the crops reproduce
copyrighted figures and must not be committed.
"""

import pathlib

import fitz

PAPERS = pathlib.Path("data/papers")
OUT = PAPERS / "qc_pass1"

# (pdf, page 1-based, clip in PDF points as x0 y0 x1 y1, dpi, tag, what it shows)
CROPS = [
    ("CAND-1_yu2013.pdf", 6, (55, 500, 300, 665), 900, "yu_fig7_full",
     "Fig 7 whole plot, FBP, three lesion sizes against mAs"),
    ("CAND-1_yu2013.pdf", 6, (85, 510, 300, 545), 1500, "yu_f7_top",
     "Fig 7 band from about 94% to 101%, where large and medium converge"),
    ("CAND-1_yu2013.pdf", 6, (85, 540, 300, 590), 1200, "yu_f7_mid",
     "Fig 7 band around the 90% and 80% gridlines"),
    ("CAND-1_yu2013.pdf", 6, (85, 585, 300, 625), 1200, "yu_f7_low",
     "Fig 7 band around the 70% gridline"),
    ("CAND-1_yu2013.pdf", 6, (225, 505, 300, 550), 2000, "yu_f7_sat",
     "Fig 7 at 360 and 480 mAs, where the saturated markers coincide"),
    ("CAND-1_yu2013.pdf", 7, (55, 40, 295, 250), 1300, "yu_f9",
     "Fig 9 whole plot, IR against FBP at 60 and 120 mAs"),
    ("CAND-1_yu2013.pdf", 7, (60, 480, 300, 660), 900, "yu_fig10",
     "Fig 10 Bland-Altman, used to cross-check the Fig 7 and Fig 9 pairs"),
    ("CAND-4_paul2007.pdf", 7, (315, 38, 530, 200), 1400, "paul_f6b",
     "Fig 6 panel b, task 1 solid nodule"),
    ("CAND-4_paul2007.pdf", 7, (405, 50, 437, 78), 4000, "paul_lowdose",
     "Fig 6 panel b at 0.55 to 1.05 mGy, the disputed marker cluster"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, page, clip, dpi, tag, description in CROPS:
        document = fitz.open(PAPERS / name)
        pixmap = document[page - 1].get_pixmap(dpi=dpi, clip=fitz.Rect(*clip))
        path = OUT / f"{tag}.png"
        pixmap.save(path)
        print(f"{path}  {pixmap.width}x{pixmap.height}  {description}")


if __name__ == "__main__":
    main()
