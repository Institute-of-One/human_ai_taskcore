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

Milestone **M2** — Phase 1 runs end to end:

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

The external validation against digitized observer studies (H2) is the
remaining M3 item.

## Install & test

```bash
pip install -e ".[dev]"
pytest
python -m ptx.phase1 --out results/phase1.json
python -m ptx.uncertainty --out results/uncertainty.json
python -m ptx.case_uhrct --out results/case_uhrct.json
```

## Manuscript

Numbers reach the text one way only. `paper/manuscript_template.md` carries
`{{key}}` placeholders, and `paper/make_figures.py` reads `results/*.json`,
writes the figures and `paper/numbers.json` (each quantity with the file and
path it came from), then renders `paper/manuscript.md`. Editing
`manuscript.md` by hand is pointless: it is generated.

```bash
pip install -e ".[dev,paper]"
python paper/make_figures.py
pandoc -f markdown-implicit_figures paper/manuscript.md \
  --reference-doc=paper/reference.docx -o paper/manuscript.docx
```

`-f markdown-implicit_figures` matters: without it pandoc turns each figure's
alt text into a second caption.

## Design principles

Inherited from IORN-002
([radiomics-phantom](https://github.com/Institute-of-One/radiomics-phantom),
*J. Imaging* 2026, 12, 392): full determinism (explicit seeds everywhere),
results.json-driven manuscripts (no hand-typed numbers), independent
implementation cross-checked against published anchor values in CI, and
interval-first statistics.

## License

MIT — see `LICENSE`.
