# Medical Physics (AAPM / Wiley) — Submission Kit — IORN-009 (human_ai_taskcore)

Built on the kit written for IORN-005, which was submitted to this journal as MS 26-1820
and **returned before peer review for want of line numbers and page numbers**. Everything
that return taught is machinery here rather than a note to remember.

**Run `python tools/presubmission_check.py` before building anything to send.** It must
print `ready`. It reads the built `.docx`, not the Markdown, because page furniture exists
only in the artefact the editor receives — which is exactly what the IORN-005 return
turned on.

```bash
python paper/make_figures.py        # figures + resolve every number into manuscript.md
python paper/build_docx.py          # -> paper/build/manuscript.docx  (line + page numbers)
python paper/make_title_page.py     # -> paper/build/title_page.docx
python tools/presubmission_check.py # must print: ready
```

## Upload files

| File | Designation |
|---|---|
| `paper/build/manuscript.docx` | Main Document |
| `paper/build/title_page.docx` | Title Page |
| cover letter | pasted or attached per the form |

There is no supplementary file. Every figure is embedded in the main document.

## Why this venue

The paper is a physics-to-perception transfer model validated against published human
observer data under a protocol frozen before the literature search. Medical Physics is
where the model-observer and task-based image-quality literature this work engages with
is published: of the three studies in the validation pool, two are *Med Phys* papers
(Yu et al 2013, Leng et al 2013).

The Note risk is small and measured rather than assumed: of 200 items Crossref records
for *Medical Physics* since 2026-05-01, **one** is labelled a Note or Letter, 0.5 per
cent. The paper is 8,502 words with 21 references, a density of 2.5 per 1000 words, and
it carries prespecified hypotheses with declared consequences — none of which reads as a
Note.

**Cost.** Medical Physics is hybrid. The subscription route carries no APC and no funder
mandates open access here, so no charge applies unless OnlineOpen is chosen.

## Requirements verified

- **Structured abstract**, Background / Purpose / Methods / Results / Conclusions,
  maximum 500 words — **ours: 354**. Checked mechanically.
- **Line numbering and page numbers** in the `.docx` — present, and the check fails
  without either. Verified by removing each and confirming the gate catches it.
- **Separate title page** — built from the manuscript's own front matter, so the two
  titles cannot drift. The check compares them.
- **References numbered in order of first citation**, AMA style — 21 entries, numbered by
  citeproc against `paper/references.bib` and `paper/style/american-medical-association.csl`,
  so the ordering is a property of the build and not of anyone's attention. Every DOI is
  resolved against Crossref by `tools/check_references.py`.
- **Title in sentence case** — it is.
- Figures: **6**, each embedded, each captioned beneath itself for review, and each
  listed again after the references — the Files step asks for both. The list after
  the references is generated from the body's own captions by `paper/make_figures.py`,
  so the two copies of a caption cannot drift apart.
- **Generative AI** is declared in Section 3.1 of the Methods, which is where Wiley
  asks for it, and in the cover letter.

  This kit asserted both of the above before either was true. It was written from the
  IORN-005 kit and the two claims were carried over rather than checked; the
  manuscript had neither until 2026-09-05, and the submission form's own wording is
  what exposed it. Both are now gates in `tools/presubmission_check.py`, verified by
  removing each and confirming the check fails — the general rule being that a claim
  in a kit is worth nothing until something fails when it stops being true.

## Form fields (copy–paste)

**Title:**

```
Detection information saturates over a quarter of the reconstruction band, and the missing band is lost in the observer rather than the display
```

**Article type:** Research Article

**Author:** Shuji Yamamoto — sole and corresponding author
- Affiliation: **Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan**
- Email: yamamoto@lisit.jp · ORCID: 0000-0001-9211-1071

Enter the affiliation exactly as written. It is the string Crossref carries for both
published papers under this affiliation; a second ordering of the same address reads to
an affiliation-matching system as a second affiliation.

**Keywords:**

```
task-based image quality; model observer; contrast sensitivity; detectability; ultra-high-resolution CT; display conditions
```

**Abstract:** paste from `paper/build/manuscript.docx` or from `paper/manuscript.md`.
**Not** from `paper/manuscript_template.md`, which still carries `{{placeholders}}`.

## Suggested reviewers

**Addresses are looked up from published records and never generated.** If the form
requires suggestions, take them from the authors of the work this paper engages with and
find each address from the corresponding-author details of the cited paper:

| Candidate | Why | Where to find the address |
|---|---|---|
| Lifeng Yu, Mayo Clinic | First author of two of the three studies in the validation pool | doi:10.1118/1.4794498 |
| Craig K. Abbey, UC Santa Barbara | Model-observer and human-observer correlation; author of a candidate the pool judged | doi:10.1117/1.JMI.6.2.025501 |
| Ehsan Samei, Duke | Task-based image quality and the anatomic-noise result the Limitations turn on | doi:10.1148/radiology.213.3.r99dc19727 |

Suggesting the authors of work you engage with is normal and is not a conflict.
**Excluded reviewers: none.** Naming exclusions without cause reads badly.

## Statements

| Field | Answer |
|---|---|
| Conflict of interest | The author is Representative Director of LISIT Co., Ltd., which funds Institute of One and is his affiliation on this paper, and Chief Executive Officer of TexelCraft OÜ (Estonia). No product of either company is evaluated, recommended or used in this work. No other competing interest, financial or personal. |
| Funding | No external funding. |
| Ethics | No human participants and no animals. The external validation uses performance values published in the cited studies; no imaging or patient data was obtained or analysed. |
| Data availability | Repository `https://github.com/Institute-of-One/human_ai_taskcore`, release **v0.1.1** (commit `47f9631`), archived at **https://doi.org/10.5281/zenodo.22313885**. Concept DOI 10.5281/zenodo.22144839. |
| Generative AI | Declared in Section 3.1 of the Methods and in the cover letter. On the Files step, answer: **"Yes, I confirm my article used AIGC and declares so in the manuscript text, adhering to the policy."** |

## What a reviewer will ask first, and where it is answered

- *Is the second validation round a failure being reported as a finding?* Section 4.1.2
  gives the pre-registration's own words, recorded before the search: the floor might not
  be reachable, and the round would then be reported as not having succeeded. The
  registry `data/h2_studies_v2.json` names all nine candidates and the criterion each
  failed.
- *Was the pool narrowed after seeing the correlations?* The order is checkable, not
  asserted: `git merge-base --is-ancestor 6b77ee3 21d9421` in the released repository.
  Continuous integration runs that check on every push — it had been silently unable to,
  because `actions/checkout` is shallow by default, until 2026-09-05.
- *Why only CT?* Because the two admission requirements select for different literatures,
  which the second round measured rather than assumed. Section 4.1.2 and the Limitations.

---

Prepared 2026-09-05 from `paper/manuscript.md` at v0.1.1 and the IORN-005 kit.
