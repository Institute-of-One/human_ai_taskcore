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
- `ptx.phase1` — the section 7 condition grid (540 conditions), written to a
  deterministic `results.json`.

Running the grid forced one formulation change, adopted in protocol v0.4: the
visual system enters through N<sub>effective</sub> as Barten's own internal
noise, not as a numerator weight. A weight applied to both signal and noise
cancels exactly in a quantum-limited chain — that invariance is kept as a
validation result, and it is the neural noise floor, which bypasses every
transfer factor, that makes reconstruction kernel and viewing geometry matter.

Uncertainty propagation, the U-HRCT case study (H3) and the external
validation against digitized observer studies (H2) land in M3.

## Install & test

```bash
pip install -e ".[dev]"
pytest
python -m ptx.phase1 --out results/phase1.json
```

## Design principles

Inherited from IORN-002
([radiomics-phantom](https://github.com/Institute-of-One/radiomics-phantom),
*J. Imaging* 2026, 12, 392): full determinism (explicit seeds everywhere),
results.json-driven manuscripts (no hand-typed numbers), independent
implementation cross-checked against published anchor values in CI, and
interval-first statistics.

## License

MIT — see `LICENSE`.
