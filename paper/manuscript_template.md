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
{{n_conditions}} conditions were evaluated, and the literature ranges of the
observer parameters were propagated into 95% bands.

**Results.** [TODO prose] Under standard reading conditions the delivered band
reaches only {{f_sat_median_lpmm}} lp/mm in the median, or
{{f_sat_median_percent_of_nyquist}}% of the reconstruction Nyquist frequency of
{{nyquist_lpmm}} lp/mm, and all {{n_dose_series}} dose series show a declining
$G_{\mathrm{useful}}$. In a U-HRCT-class case study the band above the
conventional Nyquist frequency contributes {{added_band_median_percent}}% of
$d'^2$ in the median. Against published human observer data, admitted by criteria
frozen before the literature search, the model reproduces the within-study
ordering of conditions in {{h2_n_meeting}} of {{h2_n_studies}} studies, with a
pooled rank correlation of {{h2_pooled_v1_2}} against a threshold of
{{h2_threshold}} set in advance.

**Conclusions.** Under the stated display and viewing conditions, information
above a few tenths of a line pair per millimetre does not reach the observer; the
model states the display conditions under which it would. The external validation
covers CT: the pool requirement for a chest-radiography study could not be met
under the frozen criteria, so the generality claim narrows accordingly.

**Keywords:** task-based image quality; model observer; contrast sensitivity;
detectability; ultra-high-resolution CT; display conditions

# 1. Introduction

When Rossmann established the point spread function and the modulation
transfer function as the working language of radiographic image quality, he was
explicit that the object of analysis was not the imaging device but "the entire
radiological process involving exposing, imaging, and visual detection
operations" (Rossmann 1969). Visual detection was named as the terminal stage
of the chain from the beginning. What the era delivered, however, was a
descriptive cascade of transfer functions: the terminal stage was declared
rather than carried through, because closing it requires a task, a noise
spectrum and a statement about the observer's own limitations in the same
expression as the physics.

The two developments that followed did not close it either, and were never
meant to. Receiver operating characteristic analysis gave the field a rigorous
way to *measure* observer performance and to relate it to the costs and
benefits of diagnostic decisions (Metz 1978), but it measures the observer
rather than predicting the observer from physical conditions: each new
acquisition or display condition requires a new reading study. Computer-aided
diagnosis, developed systematically in the same laboratory from the early
1980s, positioned the computer as a reader of the same image and a provider of
a second opinion (Doi 2007), which again leaves the question of what the human
reader can extract from a given physical condition unaddressed. The physics of
the chain, the measurement of the observer, and computational assistance all
exist; a closed-form path from the first to the second does not.

The gap matters more now than it did, because acquisition resolution and dose
efficiency are still improving and the question of where the returns stop is
being asked one device at a time. Ultra-high-resolution CT reconstructs detail
well beyond the sampling of a routine display window (Kakinuma 2015), and each
such advance is evaluated with its own multireader study, on its own display
protocol, without a common formulation in which the answers could be compared
or predicted. Asked device by device, the question also invites the wrong
answer: that finer acquisition is or is not "worth it", as though the ceiling
were a property of the scanner.

This work closes the chain in a single closed-form, falsifiable expression. A
detection task is carried from the reconstruction through display transfer and
luminance mapping, ocular optics, and the neural internal noise of a published
contrast-sensitivity model, and integrated into a task-weighted detectability
$d'^2_{\mathrm{human}}$. The display and visual stages are anchored to current
standards rather than to period hardware, so that the only free parameters are
the declared ranges of the observer terms, and results are reported as
intervals rather than point estimates. From the frequency-resolved integrand we
define where the delivered information sits (the saturation frequency
$f_{\mathrm{sat}}$), how much of the available information arrives
($R_{\mathrm{perceptual}}$), what an increment of dose buys
($G_{\mathrm{useful}}$), and how much magnification a given acquisition
requires before its finest band arrives at all (the sufficient magnification
$M^{*}$).

The structural consequence is worth stating plainly, because it is easily
misread as an argument against resolution. In this model sharper
reconstruction never hurts and resolution is never wasted. But the ceiling it
approaches is not set by the scanner. A reconstruction kernel filters signal
and image noise by the same factor, so in the absence of any noise the observer
contributes themselves, it cancels out of the detectability integral exactly —
an invertible filter cannot change what is detectable. What breaks that
cancellation is the observer's own noise, which enters after the display and is
therefore not filtered by anything upstream. The height of the attainable
ceiling is thus a property of the observer and of the display that feeds them,
and the same acquisition can sit far below or close to that ceiling depending
on how it is displayed. Resolution always acts; the limit on what it buys is
set elsewhere.

Three hypotheses are stated in advance and tested. H1: perceptually weighted
detectability saturates in acquisition resolution and dose, so that a
saturation frequency exists; the test is whether the decline of
$G_{\mathrm{useful}}$ is resolved by its interval, since the sign of
$G_{\mathrm{useful}}$ itself is uninformative. H2: the model reproduces the
ordering of conditions in published human observer experiments; inclusion
criteria, schema and analysis were frozen and committed before the literature
search began, and the commit is cited in the data availability statement so
that the ordering of criteria and data is auditable rather than asserted. H3:
the extra band of a U-HRCT-class acquisition reaches the reader only under
sufficient magnification, and because detectability rises monotonically towards
an asymptote, the design quantity is a sufficient magnification and not an
optimum.

The scope is deliberately narrow. The formulation applies to linear,
X-ray-based imaging chains and near-threshold detection tasks with the signal
specified; the validation covers CT and chest radiography. Every statement in
this paper is conditional on stated display and viewing conditions and concerns
whether task-relevant information reaches the observer. Nothing here is a claim
about whether a diagnosis can be made.

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

[TODO prose] {{n_conditions}} conditions: task diameter and contrast, dose,
slice thickness, reconstruction kernel and magnification, at a reconstruction
Nyquist frequency of {{nyquist_lpmm}} lp/mm.

## 3.3 Uncertainty propagation

[TODO prose] The observer is not point-estimated. The literature ranges of
$\eta_{\mathrm{cog}}$ and $\kappa$, together with viewing distance, luminance
and magnification, are propagated by a seeded Latin hypercube of
{{n_propagation_samples}} samples ({{n_propagation_evaluations}} evaluations),
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

![Left: $d'^2$ across the three reconstruction kernels, relative to the
standard kernel, with both noise floors switched off and switched on. With the
floors off the kernel leaves the integral exactly, as an invertible filter
must. Right: the mechanism — the kernel filters signal and image noise
together and leaves the neural floor untouched, so all it can move is which of
the two dominates at a given frequency.](figures/fig1_kernel_invariance.png)

Two things are checked here, and they are different in kind. The first is that
the model behaves as its own construction requires. The second is that its
predictions order published human performance correctly, which is the only test
the model can fail against evidence it did not produce.

### 4.1.1 Internal consistency

With the noise floors switched off, the reconstruction kernel cancels out of the
detectability integral to {{invariance_primary}} relative spread, confirming
invertible-filter invariance and identifying the kernel sensitivity observed with
the floors on ({{kernel_sensitivity_median}}% median spread) as the footprint of
the neural noise. NPWE and channelised Hotelling observers rank the conditions
alike (Spearman $\rho$ = {{spearman_npwe_cho}}).

Neither result is evidence that the model is right. An invertible filter must
cancel, and two observer models built on the same integral must agree; a failure
would have meant an implementation error, and its absence means only that there is
none of that kind.

### 4.1.2 External validation against published human performance

H2 asks whether the model reproduces the *ordering* of conditions in published
observer experiments. Absolute levels are not compared: observer panels, decision
criteria and task definitions differ between studies in ways no rescaling repairs,
so the quantity carried across studies is the within-study rank.

The criteria for admitting a study, the analysis, and the thresholds at which H2
succeeds or is rejected were frozen before the literature search began, and are
reproduced in Appendix A. Studies were admitted by mechanical application of those
criteria, without regard to how well the model was expected to do on them; the
registry records every candidate screened and the criterion each failed.

Three studies were admitted, spanning {{h2_n_yu2013}}, {{h2_n_paul2007}} and
{{h2_n_leng2013}} condition points. Within-study Spearman correlations between
predicted $d'$ and the reported figure of merit are {{h2_rho_yu2013}},
{{h2_rho_paul2007}} and {{h2_rho_leng2013}}, against the success threshold of
{{h2_threshold}} fixed in advance. {{h2_n_meeting}} of {{h2_n_studies}} studies
meet it, and the pooled calibration, formed by standardising ranks within each
study before combining, is {{h2_pooled_v1_2}}. **H2 is therefore not rejected**:
the majority condition and the pooled threshold are both met and the calibration
is monotone.

The pooled value sits close to its threshold, and it is worth being explicit about
where the margin went. The condition-axis vocabulary was widened twice during
pre-registration, and each frozen reading was required to be reported so that a
widening could not be what produced the conclusion. Under the strictest reading
the pool holds two studies and calibrates at {{h2_pooled_v1_0_strict}}; the
intermediate reading gives {{h2_pooled_v1_1}}; the full reading admits the third
study and gives {{h2_pooled_v1_2}}. All three agree in direction, so the widening
did not manufacture the result — but it did not improve it either, and the
difference between {{h2_pooled_v1_0_strict}} and {{h2_pooled_v1_2}} is one study
entering.

That study is the discordant one. Paul *et al* fall below threshold at
{{h2_rho_paul2007}} and are retained, because the pre-registration requires a
disagreeing study to be reported rather than dropped. Its first task saturates:
the reported detectability reaches its ceiling across most of the dose range, so
the majority of its condition points carry almost no rank information, and the
region that does is the one where the digitised marker positions are least
separable. A study whose conditions are mostly tied is one a rank statistic has
little to work with, and that is the most likely reading of its value. It is a
reading, not a measurement, and it does not license setting the study aside.

Across the three studies the within-study correlations run from {{h2_rho_min}} to
{{h2_rho_max}} with a median of {{h2_rho_median}}. No meta-analytic pooled estimate
is offered: three studies with this much heterogeneity would give a number more
precise-looking than the evidence supports.

One prediction made in advance was wrong. Because the model has no search term, we
predicted that studies with a signal-known-exactly task would agree with it at
least as well as those with location uncertainty. The medians run the other way,
{{h2_stratum_ske}} for the former against {{h2_stratum_search}} for the latter.
The stratum on the far side of that comparison holds one study, so this is not
strong evidence that the premise was wrong; it is reported because the prediction
was recorded before the analysis and because the stratification was deliberately
excluded from the success conditions, so that no stratum could be used to rescue
H2 had the pool failed.

Finally, the scope of what this validates is narrower than intended. The frozen
pool requirements asked for at least one non-CT study, so that the generality of
the formulation would be supported by evidence rather than by assertion. Seven
chest-radiography candidates were screened across two search rounds and every one
failed a frozen criterion — three on the condition-axis requirement, two on the
number of condition points, two on the reported figure of merit. The
pre-registration fixed the consequence of an unfilled slot before the search
began: **the generality claim narrows to CT**. The model is formulated generally
and is validated here on CT alone.

## 4.2 The delivered band sits far below Nyquist (H1)

![Contribution density to $d'^2$ against spatial frequency at three dose
levels, with $f_{\mathrm{sat}}(95\%)$ marked. The reconstruction Nyquist
frequency is {{nyquist_lpmm}} lp/mm.](figures/fig2_contribution_density.png)

![$f_{\mathrm{sat}}(95\%)$ relative to the reconstruction Nyquist frequency.
Left and centre: against dose for each kernel at both magnifications, with
bands spanning task diameter, contrast and slice thickness. Right: the
distribution over all {{n_conditions}} conditions.](figures/fig3_f_sat_atlas.png)

The contribution density to $d'^2$ falls away long before the reconstruction runs
out of frequencies to deliver. Across the {{n_conditions}} conditions,
$f_{\mathrm{sat}}(95\%)$ — the frequency below which 95% of $d'^2$ has already
accumulated — spans {{f_sat_min_lpmm}} to {{f_sat_max_lpmm}} lp/mm with a median
of {{f_sat_median_lpmm}} lp/mm. Against a reconstruction Nyquist frequency of
{{nyquist_lpmm}} lp/mm, the median condition delivers detection information over
{{f_sat_median_percent_of_nyquist}}% of the band the reconstruction supports. The
perceptual utilisation ratio, which measures the same thing as a fraction of the
detectability available before the display and the eye, has a median of
{{r_perceptual_median}}.

The immediate question is what withholds the rest, and the model answers it by
decomposition rather than by inference. The neural internal noise carries
{{neural_share_median}}% of the band-integrated effective noise in the median.
Display quantisation never exceeds {{quantisation_share_max}}% in any condition.
The high frequencies are therefore not being lost in the display's bit depth,
which is the component most readily improved and the one most often blamed; they
are lost in the observer, which is not improvable at all by changing the imaging
chain.

That distinction is what makes $f_{\mathrm{sat}}$ a statement about a reading
condition rather than about a scanner. Nothing here says that the frequencies
above it are absent from the image, and the image is unchanged whether an observer
uses them or not. What the number says is that under the stated viewing distance,
luminance and magnification, information above roughly a third of a line pair per
millimetre arrives at a detector — the visual system — that has already stopped
contributing it to the decision.

## 4.3 The gain per unit dose declines in every condition (H1)

![$G_{\mathrm{useful}}$ against relative dose with 95% bands, for the standard
kernel at the lower of the two task contrasts.](figures/fig4_g_useful_bands.png)

$G_{\mathrm{useful}}$, the increment in $d'^2$ bought by an increment in dose,
declines monotonically in {{saturating_fraction_phase1}}% of the
{{n_dose_series}} dose series at the point estimate. The direction is not in
doubt within this model: added dose lowers the quantum noise and leaves the neural
floor where it was, so each further increment buys less than the one before it.
What the calculation supplies is where the decline becomes steep enough to matter,
and that depends on the reading condition rather than on the acquisition.

A monotone decline at the point estimate would be worth little if the observer
parameters could move it, since those parameters are literature ranges rather than
measurements of any particular reader. Propagating them,
{{saturating_fraction_bands}}% of the series satisfy the rule declared in advance,
that the 95% band on the decline excludes zero. The bands are not narrow: the
$f_{\mathrm{sat}}$ band is {{f_sat_band_width_median}} lp/mm wide in the median
against a median centre of {{f_sat_band_centre_median}} lp/mm, or
{{f_sat_band_width_percent}}% of its own centre, and $R_{\mathrm{perceptual}}$
ranges from {{r_perceptual_band_low}} to {{r_perceptual_band_high}} across all
series. The conclusion survives that width because it is an ordering claim and not
a level claim: every value inside the band still saturates, and the band is wide
enough to say that the *position* of $f_{\mathrm{sat}}$ for an individual reader
should not be quoted to the precision the median suggests.

## 4.4 The U-HRCT case study (H3)

![Share of $d'^2$ arriving from above the conventional Nyquist frequency of
{{added_band_cutoff_lpmm}} lp/mm, over anatomical magnification and viewing
distance.](figures/fig5_added_band_map.png)

![Maximum added-band share against task diameter, with the absolute $d'$ of the
U-HRCT chain at the reference reading condition on the right
axis.](figures/fig6_added_band_vs_task.png)

An ultra-high-resolution chain delivers frequencies a conventional one cannot. The
question H3 puts is not whether those frequencies exist but whether they reach the
observer, and the model answers it by integrating the contribution density above
the conventional Nyquist frequency of {{added_band_cutoff_lpmm}} lp/mm.

Across the case study that band contributes {{added_band_median_percent}}% of
$d'^2$ in the median. The maximum is {{added_band_max_percent}}%, and where it
occurs is the finding rather than the number itself. It belongs to the
{{smallest_task_mm}} mm task, whose added-band share is
{{small_task_added_band_percent}}% and which gains
{{small_task_dprime_gain_percent}}% in $d'$ from the finer chain — and which sits
at an absolute $d'$ of {{small_task_dprime_uhrct}}. A detectability of that size is
not a detection. The
task that benefits most from the added band is the one the observer does not
perform at either resolution, so the benefit is a larger share of a quantity that
is too small to act on.

The {{largest_task_mm}} mm task makes the same point from the other end. It is
detected comfortably, at $d'$ = {{large_task_dprime_uhrct}}, and it takes
{{large_task_dprime_gain_percent}}% from the finer chain with an added-band share
of {{large_task_added_band_percent}}%. Where detection is happening, the added band
is not what is doing it.

This is the shape of the result and it does not depend on the particular numbers:
the added band matters most exactly where detectability is lowest, and where
detectability is adequate the added band is negligible. Reporting the maximum share
alone would invert the reading, which is why the absolute $d'$ is carried alongside
it in the figure and in the text.

The magnification behaviour is consistent with the same mechanism. $d'$ is monotone
in magnification in every row, and the magnification at which the delivered band
first covers the task, $M^{*}$, is {{m_star_conventional_median}} for the
conventional chain against {{m_star_uhrct_median}} for the U-HRCT chain in the
median. The finer chain reaches its own limit at lower magnification, which is what
a chain limited by the observer rather than by the acquisition should do.

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
- **The validation covers CT only.** The frozen pool required at least one
  chest-radiography study so that the generality of the formulation would rest on
  evidence; seven candidates were screened and all failed a criterion frozen
  before the search. The pre-registration fixed the consequence in advance, and it
  is taken here: the model is formulated generally and validated on CT.
- **Anatomic noise has no term in the model.** The nearest miss in the
  chest-radiography search was excluded on the number of condition points, but the
  more informative fact is what it reports: at matched detectability a nodule
  needs roughly four times the diameter on an anatomic background that it needs on
  quantum noise alone. A model whose noise is quantum and neural cannot express
  that difference, and on chest radiography it is the dominant one. This bounds
  where the present formulation can be expected to hold at all, independently of
  whether a suitable validation study exists.
- One of three admitted studies falls below the agreement threshold and is
  retained rather than dropped; its conditions are largely saturated, so a rank
  statistic has little to separate.
- Model observers are not clinical performance. A reading study is future work.

# 7. Conclusion

A detection task carried from the reconstruction through display, ocular optics
and neural internal noise saturates well below the frequencies modern CT delivers.
Under standard reading conditions the delivered band reaches
{{f_sat_median_percent_of_nyquist}}% of the reconstruction Nyquist frequency, the
gain per unit dose declines in every series examined, and in a U-HRCT-class case
the band above the conventional Nyquist frequency contributes
{{added_band_median_percent}}% of $d'^2$. These are statements about what reaches
an observer under stated display conditions, not about what a scanner can resolve;
the same model says which display conditions would change them.

Tested against published human observer experiments admitted by criteria frozen
before the search, the model orders conditions correctly in {{h2_n_meeting}} of
{{h2_n_studies}} studies, pooling at {{h2_pooled_v1_2}}. That is agreement in
ordering and not in level, on CT, with one discordant study retained and reported.
The requirement that a chest-radiography study support the generality of the
formulation could not be met, so the claim is the narrower one the
pre-registration fixed in advance: the model is formulated generally and validated
here on CT.

# Appendix A. The frozen H2 protocol

Reproduced so that the criteria can be read without consulting the repository.
The full documents, their version history and the commit that froze each are in
`docs/`; every candidate screened and the criterion it failed are in
`data/h2_studies.json`.

**Inclusion criteria (frozen before the literature search).** A study is admitted
when: (C1) the modality is CT or chest radiography and the task is detection;
(C2) human observer performance is reported over at least two condition axes, each
of which corresponds to a declared input of the model — an axis the model cannot
predict is not a validation axis; (C3) at least four condition points are
reported, so that a rank correlation means something; (C4) display and reading
conditions are recorded where given, and substituted where not, with every
substitution published per condition — C4 never excludes; (C5) the figure of merit
is AUC, two-alternative forced-choice proportion correct, or $d'$; (C6) values
taken from a figure digitise to within 5%, measured as the maximum deviation
between two independent passes.

**Pool requirements.** At least three studies, at least fifteen condition points,
and at least one non-CT study. The last supports the generality of the claim; if
it cannot be met, the claim narrows to CT.

**Analysis and verdict.** Within-study Spearman $\rho$ between predicted $d'$ and
the reported figure of merit. A study succeeds at $\rho \ge$ {{h2_threshold}}. The
pool succeeds when a majority of studies succeed and the pooled calibration —
ranks standardised within each study, then combined — also reaches
{{h2_threshold}}. H2 is rejected when a majority fall below the threshold, or when
the pooled calibration is not monotone. No significance test is performed and no
$p$-value is reported: the comparison is against a threshold fixed in advance.

**Two provisions against selective validation.** The analysis is gated on the pool
being complete, so that no correlation is seen before deciding whether to keep
searching. And the condition-axis vocabulary was widened twice; every frozen
reading is reported, so that a widening cannot be what produced the conclusion.

# Data and code availability

[TODO] Repository, version tag, and the commit that froze the H2 inclusion
criteria before the literature search.

# References

[TODO] Rossmann 1969; Metz 1978; Barten 1999; DICOM PS3.14; Abbey & Barrett;
Doi 2006/2007; Kakinuma 2015; ICRP 87.
