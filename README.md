# human_ai_taskcore (IORN-009)

Physics-to-perception framework for task-based medical imaging — the open
research core for **IORN-009A/B** (Institute of One, LISIT Co., Ltd.).

The framework formulates the acquisition → display → human-visual-system
chain as a single closed-form, falsifiable task-weighted information
integral and derives the perceptual saturation frequency *f*<sub>sat</sub>,
the perceptual utilisation ratio *R*<sub>perceptual</sub>, and the
per-dose perceptual gain *G*<sub>useful</sub>. Formulation is
modality-agnostic (linear X-ray-based imaging characterizable by MTF/NPS);
the primary demonstration is CT, with an ultra-high-resolution CT case
study. See `docs/IORN-009A_research_protocol_v0.4.md` (Japanese) for the
governing research protocol.

Package name: `ptx` (physics-to-perception transfer core).

## Status

Milestone **M4** — all three hypotheses have been run and the manuscript is
written. H1 and H3 come from the condition grid, the propagation and the case
study; H2 is the external validation against published human observer studies,
run once over a pool that was closed before any correlation was computed.

**H2 result.** Three CT studies were admitted under criteria frozen before the
literature search. The model reproduces the within-study ordering in two of the
three (Spearman ρ = +0.853, +0.626, +0.810; pooled +0.724 against a threshold of
0.7 fixed in advance). The discordant study is retained and reported, not
dropped. **The pool requirement for one non-CT study could not be met** — seven
chest-radiography candidates were screened across two rounds and every one failed
a frozen criterion — so the pre-registered consequence was taken and the
generality claim narrows to CT. The model is formulated generally and validated
here on CT alone. Every candidate screened, and the criterion each failed, is in
`data/h2_studies.json`.

That the criteria were frozen *before* the search is checkable rather than
asserted:

```bash
git merge-base --is-ancestor 6b77ee3 21d9421   # freeze, then first candidate scan
```

which succeeds only if the freeze precedes the search. `tests/test_release.py`
runs that same check, so the repository cannot drift into claiming an order it
does not have. The pre-registration and its three amendments — each recording
what changed and why — are in `docs/`, and every frozen reading of the amended
criteria is analysed and reported rather than only the final one.

Phase 1 components:

- `ptx.chain` — DICOM GSDF display model, display pixel MTF, ocular MTF,
  Barten CSF, CT TTF/NPS acquisition stage, and the assembled
  H<sub>effective</sub> / N<sub>effective</sub> of the protocol. Every
  component is implemented independently and anchored to published values or
  analytic limits in `tests/`.
- `ptx.detectability` — d'² integral (1-D and isotropic 2-D form), f_sat,
  R<sub>perceptual</sub>, G<sub>useful</sub>.
- `ptx.observer` — NPWE and channelized Hotelling (difference-of-Gaussian
  channels) side by side, plus the prewhitening ideal observer.
- `ptx.phantom_lung` — HU-calibrated anisotropic parenchyma texture,
  Murray's-law vessel tree, spherical nodules with partial volume, and the
  analytic nodule task function.
- `ptx.condition` — one reading condition end to end; the single evaluation
  path shared by the grid, the propagation and the case study.
- `ptx.phase1` — the section 7 condition grid (540 conditions), written to a
  deterministic `results.json`.
- `ptx.uncertainty` — Latin-hypercube propagation of the section 5.4 intervals
  (eta_cog, kappa, viewing distance, luminance, magnification) into 95% bands,
  and H1's saturation rule.
- `ptx.case_uhrct` — the H3 case study: a U-HRCT-class chain against a
  conventional one over a magnification/distance map, with the sufficient
  magnification M*.

Running the grid forced one formulation change, adopted in protocol v0.4: the
visual system enters through N<sub>effective</sub> as Barten's own internal
noise, not as a numerator weight. A weight applied to both signal and noise
cancels exactly in a quantum-limited chain — that invariance is kept as a
validation result, and it is the neural noise floor, which bypasses every
transfer factor, that makes reconstruction kernel and viewing geometry matter.

## Install & test

```bash
pip install -e ".[dev]"
pytest
python -m ptx.phase1 --out results/phase1.json
python -m ptx.uncertainty --out results/uncertainty.json
python -m ptx.case_uhrct --out results/case_uhrct.json
python -m ptx.h2_analysis --out results/h2.json
```

`ptx.h2_analysis` refuses to run on an incomplete pool. Computing a correlation
for one study and then deciding whether to keep searching is the selective
validation the pre-registration exists to close, so the gate is in the code and
not in the discipline of whoever runs it.

## Manuscript

Numbers reach the text one way only. `paper/manuscript_template.md` carries
`{{key}}` placeholders, and `paper/make_figures.py` reads `results/*.json`,
writes the figures and `paper/numbers.json` (each quantity with the file and
path it came from), then renders `paper/manuscript.md`. Editing
`manuscript.md` by hand is pointless: it is generated.

```bash
pip install -e ".[dev,paper]"
python paper/make_figures.py
pandoc -f markdown-implicit_figures --citeproc \
  --bibliography=paper/references.bib \
  paper/manuscript.md -o paper/manuscript.docx
```

`-f markdown-implicit_figures` matters: without it pandoc turns each figure's
alt text into a second caption. `--citeproc` matters as much: without it the
citations render as literal `[@key]` markers and the reference list is silently
empty, in a document that otherwise looks finished.

### Before sending it anywhere

```bash
python tools/check_references.py      # resolve every DOI against doi.org
python tools/presubmission_check.py   # refuse while anything is still unset
```

`check_references.py` asks doi.org what each DOI actually resolves to and
compares it with the entry that produced it. A DOI written from memory usually
resolves — to somebody else's paper — so a spot check does not find it. Building
this file, two of twenty-one entries were wrong that way.

`presubmission_check.py` refuses to call the manuscript ready while any release
field is unset, any placeholder is unresolved, the version tag names a tag that
was never cut, or the working tree is dirty. The release tag and the Zenodo
version DOI live in `results/release.json` and start as `null`; until they are
filled the built manuscript carries a loud `[UNSET: ...]` marker rather than
anything that could be mistaken for a value.

## Design principles

Inherited from IORN-002
([radiomics-phantom](https://github.com/Institute-of-One/radiomics-phantom),
*J. Imaging* 2026, 12, 392): full determinism (explicit seeds everywhere),
results.json-driven manuscripts (no hand-typed numbers), independent
implementation cross-checked against published anchor values in CI, and
interval-first statistics.

## License

MIT — see `LICENSE`.
