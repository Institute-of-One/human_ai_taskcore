---
title: "Where does imaging resolution stop reaching the reader? A closed-form physics-to-perception transfer model with saturation frequencies"
author: "Shuji Yamamoto"
affiliation: "Institute of One, LISIT Co., Ltd., Tokyo, Japan"
orcid: "0000-0001-9211-1071"
email: "yamamoto@lisit.jp"
date: "2026"
geometry: margin=1in
fontsize: 10.5pt
papersize: a4
bibliography: references.bib
---

<!-- Rendered from manuscript_template.md by paper/make_figures.py.
     Do not edit manuscript.md directly: every number comes from
     results/*.json through paper/numbers.json. -->

# Abstract

**Purpose.** [TODO prose] To determine, in closed form, at which spatial
frequency and under which display conditions further gains in acquisition
resolution and dose stop contributing to a human observer's detection
performance.

**Methods.** [TODO prose] A serial transfer model carries a detection task
from the reconstruction through display, ocular optics and the neural internal
noise of a published contrast-sensitivity model, yielding a
frequency-resolved contribution density to $d'^2$, a perceptual saturation
frequency $f_{\mathrm{sat}}$, a perceptual utilisation ratio
$R_{\mathrm{perceptual}}$ and a gain per unit dose $G_{\mathrm{useful}}$.
540 conditions were evaluated, and the literature ranges of the
observer parameters were propagated into 95% bands.

**Results.** [TODO prose] Under standard reading conditions the delivered band
reaches only 0.335 lp/mm in the median, or
26% of the reconstruction Nyquist frequency of
1.28 lp/mm, and all 108 dose series show a declining
$G_{\mathrm{useful}}$. In a U-HRCT-class case study the band above the
conventional Nyquist frequency contributes 0.33% of
$d'^2$ in the median.

**Conclusions.** [TODO prose] Under the stated display and viewing conditions,
information above a few tenths of a line pair per millimetre does not reach the
observer; the model states the display conditions under which it would.

**Keywords:** task-based image quality; model observer; contrast sensitivity;
detectability; ultra-high-resolution CT; display conditions

# 1. Introduction

[TODO prose. Structure to keep:]

- The Rossmann programme measured the physics of the imaging chain (MTF, NPS)
  and Metz-era ROC analysis measured the observer; what has never been closed
  in one expression is the path from the physics to what the observer can use.
- Acquisition resolution and dose keep improving, and the question of where
  the returns stop is asked device by device rather than from a common
  formulation.
- This work closes the chain in a single closed-form expression, and states
  the answer as a frequency ($f_{\mathrm{sat}}$) and a display condition
  rather than as a verdict on any scanner.
- Falsifiable hypotheses: H1 (saturation exists), H2 (the model reproduces the
  condition ordering of published observer studies), H3 (a U-HRCT-class extra
  band reaches the reader only under sufficient magnification).
- Scope: linear X-ray-based systems, near-threshold detection tasks. No claim
  about diagnosis is made anywhere in this paper.

# 2. Theory

## 2.1 The chain

[TODO prose] Reconstruction TTF and NPS, display transfer and GSDF luminance
mapping, ocular MTF, and the neural internal noise of Barten's
contrast-sensitivity model, composed as one effective transfer function
$H_{\mathrm{eff}}$ and one effective noise $N_{\mathrm{eff}}$.

## 2.2 Where visual sensitivity enters

[TODO prose] Visual sensitivity enters through $N_{\mathrm{eff}}$ as Barten's
own internal noise, not as a numerator weight on the signal. The reason is
structural: with a numerator weight and no noise floors, any invertible linear
filter cancels out of the detectability integral exactly, so reconstruction
kernel and display transfer become undescribable in principle. That
cancellation is retained as a validation result (Section 4.1) rather than
discarded.

## 2.3 The internal noise splits three ways

[TODO prose] Image noise, display quantisation noise and neural noise enter at
different points of the chain, so the display transfer function acts on them
differently. Placing the floors outside $|H_{\mathrm{display}}|^2$ is the only
route by which pixel pitch and magnification affect detectability at all.

## 2.4 Derived quantities

[TODO prose] $f_{\mathrm{sat}}$, $R_{\mathrm{perceptual}}$,
$G_{\mathrm{useful}}$, and the sufficient magnification $M^{*}$.
$f_{\mathrm{sat}}$ locates the delivered band; it does not measure how much
information arrives, and it moves in the opposite direction to $d'$ when the
internal noise is raised. It is therefore always reported next to $d'$ and
$G_{\mathrm{useful}}$.

# 3. Methods

## 3.1 Implementation and reproducibility

[TODO prose] Independent implementation in numpy/scipy, checked against the
primary sources and standards (DICOM PS3.14 GSDF, Barten's tabulated values).
Every random draw is seeded; the same configuration reproduces the same
results file byte for byte.

## 3.2 Conditions

[TODO prose] 540 conditions: task diameter and contrast, dose,
slice thickness, reconstruction kernel and magnification, at a reconstruction
Nyquist frequency of 1.28 lp/mm.

## 3.3 Uncertainty propagation

[TODO prose] The observer is not point-estimated. The literature ranges of
$\eta_{\mathrm{cog}}$ and $\kappa$, together with viewing distance, luminance
and magnification, are propagated by a seeded Latin hypercube of
256 samples (23,040 evaluations),
paired across the dose axis so that each sample is one coherent observer.
Results are reported as 95% bands.

## 3.4 Hypothesis tests declared in advance

[TODO prose] H1: a condition saturates when the lower bound of the 95% band on
the decline of $G_{\mathrm{useful}}$ is positive. The sign of
$G_{\mathrm{useful}}$ itself carries no information, since more dose always
means less image noise. H2: within-study Spearman $\rho \geq 0.7$, with
inclusion criteria frozen before the literature search. H3: $d'$ rises
monotonically towards an asymptote in magnification, so the design quantity is
the sufficient magnification $M^{*}$ and not an optimum.

# 4. Results

## 4.1 Validation

[TODO prose] With the noise floors switched off, the reconstruction kernel
cancels out of the detectability integral to
0.0e+00 relative spread, confirming invertible-filter
invariance and identifying the kernel sensitivity observed with the floors on
(8.5% median spread) as the footprint of the neural
noise. NPWE and channelised Hotelling observers rank the conditions alike
(Spearman $\rho$ = 1.00).

## 4.2 The delivered band sits far below Nyquist (H1)

![Contribution density to $d'^2$ against spatial frequency at three dose
levels, with $f_{\mathrm{sat}}(95\%)$ marked. The reconstruction Nyquist
frequency is 1.28 lp/mm.](figures/fig1_contribution_density.png)

![Distribution of $f_{\mathrm{sat}}(95\%)$ relative to the reconstruction
Nyquist frequency over all 540 conditions.](figures/fig2_f_sat_distribution.png)

[TODO prose] $f_{\mathrm{sat}}(95\%)$ spans 0.213 to
0.653 lp/mm with a median of 0.335 lp/mm, that is
26% of Nyquist. The perceptual utilisation
ratio has a median of 0.226. The neural noise holds
63% of the band-integrated effective noise in the median,
while display quantisation never exceeds 0.031%: what
withholds the high frequencies is the observer, not the display's bit depth.

## 4.3 The gain per unit dose declines in every condition (H1)

![$G_{\mathrm{useful}}$ against relative dose with 95% bands, for the standard
kernel at the lower of the two task contrasts.](figures/fig3_g_useful_bands.png)

[TODO prose] 100% of the 108 dose
series show a monotonically declining $G_{\mathrm{useful}}$ at the point
estimate, and
100% of the propagated series satisfy the declared
rule that the 95% band on the decline excludes zero. The $f_{\mathrm{sat}}$
band is 0.125 lp/mm wide in the median against a median
of 0.444 lp/mm, that is
28% of its own centre, so the conclusion survives
the interval treatment. $R_{\mathrm{perceptual}}$ stays within
0.045 to 0.319 across all series.

## 4.4 The U-HRCT case study (H3)

![Share of $d'^2$ arriving from above the conventional Nyquist frequency of
1.28 lp/mm, over anatomical magnification and viewing
distance.](figures/fig4_added_band_map.png)

![Maximum added-band share against task diameter, with the absolute $d'$ of the
U-HRCT chain at the reference reading condition on the right
axis.](figures/fig5_added_band_vs_task.png)

[TODO prose] The band above 1.28 lp/mm contributes
0.33% of $d'^2$ in the median and at most
12.3%. The maximum belongs to the
0.5 mm task, which gains 20.8%
in $d'$ from the finer chain and reaches
12.3% added-band share — at an absolute $d'$ of
0.36. The 8 mm task, detectable at
$d'$ = 12.31, gains
1.4% with an added-band share of
0.2%. $d'$ is monotone in magnification in every
row, with $M^{*}$ at 0.75 for the conventional chain
and 0.50 for the U-HRCT chain in the median.

# 5. Discussion

[TODO prose. The claims that are allowed:]

- Under the stated display and viewing conditions, information above
  $f_{\mathrm{sat}}$ does not reach the observer. Nothing here says whether a
  diagnosis can be made.
- Sharper reconstruction always helps in this model; the paper does not argue
  that resolution is wasted. What it argues is that the *display* decides
  whether the resolution arrives.
- The relative value of an extra band and the absolute detectability of the
  task move in opposite directions. The extra band matters most where nothing
  is detectable, which is why the U-HRCT result must be phrased as a condition
  on the reading protocol rather than as a verdict on the scanner.
- Design guidance: the sufficient magnification, not an optimal one.

# 6. Limitations

[TODO prose]

- Linear serial approximation, near-threshold detection tasks only.
- Absolute $d'$ is not calibrated; the results are ordering and relative
  quantities. The ranges of $\eta_{\mathrm{cog}}$ and $\kappa$ carry the
  absolute level.
- The external validation rests on published studies whose display conditions
  are often unreported; substituted values are listed per condition and swept.
- Model observers are not clinical performance. A reading study is future work.

# 7. Conclusion

[TODO prose]

# Data and code availability

[TODO] Repository, version tag, and the commit that froze the H2 inclusion
criteria before the literature search.

# References

[TODO] Rossmann 1969; Metz 1978; Barten 1999; DICOM PS3.14; Abbey & Barrett;
Doi 2006/2007; Kakinuma 2015; ICRP 87.
