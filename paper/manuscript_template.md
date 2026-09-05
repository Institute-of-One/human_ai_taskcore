---
title: "Detection information saturates over a quarter of the reconstruction band, and the missing band is lost in the observer rather than the display"
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

**Background.** Resolution and dose are specified at the scanner, but they reach
the reader only through a display and an eye, and the imaging chain is usually
optimised against metrics that stop at the reconstruction.

**Purpose.** To locate, in closed form, the frequency above which further
acquisition performance stops reaching a human observer's detection task, and to
identify which stage of the chain withholds the rest.

**Methods.** A serial transfer model carries the task from reconstruction
through display, ocular optics and the neural internal noise of a published
contrast-sensitivity model. Sensitivity enters the noise term rather than
weighting the signal, the placement that lets kernel and display affect the
result. From the contribution density to $d'^2$ come a saturation frequency
$f_{\mathrm{sat}}$, a utilisation ratio $R_{\mathrm{perceptual}}$, a gain per
unit dose $G_{\mathrm{useful}}$ and a sufficient magnification $M^{*}$.
{{n_conditions}} conditions were evaluated as a full factorial, with
observer-parameter ranges propagated into 95% bands.

**Results.** The delivered band reaches {{f_sat_median_lpmm}} lp/mm in the
median, {{f_sat_median_percent_of_nyquist}}% of the reconstruction Nyquist
frequency, and $R_{\mathrm{perceptual}}$ is {{r_perceptual_median}}. Neural noise
supplies {{neural_share_median}}% of the effective noise, and all
{{n_dose_series}} dose series show declining $G_{\mathrm{useful}}$. In a U-HRCT
case study the band above the conventional Nyquist frequency adds
{{added_band_median_percent}}% of $d'^2$ in the median; its largest share,
{{small_task_added_band_percent}}% for the {{smallest_task_mm}} mm task, falls
where absolute detectability is lowest ($d'={{small_task_dprime_uhrct}}$).
Against human observer data admitted by criteria frozen before the literature
search, the model reproduces the within-study ordering in {{h2_n_meeting}} of
{{h2_n_studies}} studies (pooled $\rho={{h2_pooled_v1_2}}$, threshold
{{h2_threshold}}); the discordant study is retained.

**Conclusions.** Under the stated viewing conditions the observer, not the
imaging chain, is the limiting term. This constrains the reading condition rather
than the scanner: a sharper reconstruction never lowers $d'$ here, and the same
analysis names the magnification at which a task becomes sufficiently delivered.
The model addresses detection, not diagnosis, and its external validation covers
CT — a narrowing fixed in advance.

**Keywords:** task-based image quality; model observer; contrast sensitivity;
detectability; ultra-high-resolution CT; display conditions

# 1. Introduction

When Rossmann established the point spread function and the modulation
transfer function as the working language of radiographic image quality, he was
explicit that the object of analysis was not the imaging device but "the entire
radiological process involving exposing, imaging, and visual detection
operations" [@rossmann1969]. Visual detection was named as the terminal stage
of the chain from the beginning. What the era delivered, however, was a
descriptive cascade of transfer functions: the terminal stage was declared
rather than carried through, because closing it requires a task, a noise
spectrum and a statement about the observer's own limitations in the same
expression as the physics.

The two developments that followed did not close it either, and were never
meant to. Receiver operating characteristic analysis gave the field a rigorous
way to *measure* observer performance and to relate it to the costs and
benefits of diagnostic decisions [@metz1978], but it measures the observer
rather than predicting the observer from physical conditions: each new
acquisition or display condition requires a new reading study. Computer-aided
diagnosis, developed systematically in the same laboratory from the early
1980s, positioned the computer as a reader of the same image and a provider of
a second opinion [@doi2007], which again leaves the question of what the human
reader can extract from a given physical condition unaddressed. The physics of
the chain, the measurement of the observer, and computational assistance all
exist [@doi2006]; a closed-form path from the first to the second does not.

The gap matters more now than it did, because acquisition resolution and dose
efficiency are still improving and the question of where the returns stop is
being asked one device at a time. Dose is the half of that question that cannot
be settled by measuring more: the exposure that would resolve an observer study
is the exposure the study exists to justify [@icrp87]. Ultra-high-resolution CT reconstructs detail
well beyond the sampling of a routine display window [@kakinuma2015], and each
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

A detection task is carried from the reconstructed image to a decision through
four stages, each of which is a transfer function and a noise source: the
reconstruction, described by its task transfer function and noise power spectrum;
the display, described by its pixel aperture, its luminance mapping under the
greyscale standard display function, and the quantisation its bit depth imposes;
the eye, described by an optical modulation transfer function that depends on
pupil diameter and therefore on luminance; and the visual system, described by the
internal noise of Barten's contrast sensitivity model [@barten1999].

Composing them gives one effective transfer function $H_{\mathrm{eff}}$ and one
effective noise $N_{\mathrm{eff}}$, and the detectability of a task with
frequency-domain template $W$ follows as

$$d'^2 = \eta_{\mathrm{cog}} \int |W(f)|^2 \,
\frac{|H_{\mathrm{eff}}(f)|^2}{N_{\mathrm{eff}}(f)} \, df ,$$

with $\eta_{\mathrm{cog}}$ a scalar efficiency that carries everything the model
does not represent — attention, experience, the difference between a laboratory
task and a clinical one.

Two properties of this form matter for what follows. It is *serial*: each stage
acts on the output of the last, so no stage can restore what an earlier one
removed. And it is *frequency-resolved*: the integrand is a density, so the
question of where in the band a task's detectability comes from has an answer
rather than requiring an assumption. Every derived quantity in Section 2.4 is a
statement about that density.

The frequency variable is converted between object space and visual angle at the
point the chain reaches the eye, which is where viewing distance and magnification
enter. They are the only path by which a reading condition changes the integral,
and they change it without changing the image.

## 2.2 Where visual sensitivity enters

There are two places to put visual sensitivity in an integral of this shape, and
the choice is not cosmetic.

The first is as a weight on the numerator: multiply the signal by the contrast
sensitivity function, leaving the noise as the imaging chain delivered it. This is
the intuitive placement — the eye is less sensitive at high frequencies, so
attenuate the signal there — and it is the form an earlier version of this model
used.

It cannot work, and the reason is structural rather than empirical. Write the
integral with a numerator weight and no noise floors, and pass the image through
any invertible linear filter $F$. The filter multiplies the signal by $|F|^2$ and
the image noise by $|F|^2$, and the two cancel at every frequency. The integral is
unchanged. That is a correct result about an ideal observer on a noiseless-floor
chain, and it is fatal here: it says that reconstruction kernel and display
transfer function cannot affect detectability at all, so a model built this way is
in principle unable to describe the two things this work is about.

The second placement is the one used. Visual sensitivity enters through
$N_{\mathrm{eff}}$, as Barten's own internal noise [@barten1999] — a noise the observer adds
after the display, which no filter upstream of it can attenuate. The cancellation
then fails, and it fails for the right reason: the filter still scales signal and
image noise together, but the neural noise sits outside its reach, so what the
filter changes is which of the two dominates at a given frequency. The visual
weight $V$ in the implementation is unity in this form; the earlier weight form is
retained in the code as the ideal limit against which the appendix compares.

The cancellation itself is kept as a check rather than discarded. Switching the
noise floors off must recover it exactly, and Section 4.1.1 reports that it does.
A model that failed this would be describing kernel sensitivity that its own
structure cannot support.

## 2.3 The internal noise splits three ways

$N_{\mathrm{eff}}$ is not one quantity. Three noises enter the chain at three
different points, and where each enters decides what acts on it.

**Image noise** arrives with the reconstruction, upstream of everything. The
display transfer function and the eye act on it exactly as they act on the signal.

**Display quantisation noise** is added by the display's finite bit depth, after
its transfer function has been applied. It is shaped by the eye but not by the
display aperture.

**Neural noise** is added by the visual system, after the eye's optics. Nothing in
the imaging chain acts on it at all.

Writing $N_{\mathrm{eff}}$ as a sum in which only the first term carries
$|H_{\mathrm{display}}|^2$ is what makes pixel pitch and magnification affect
detectability. If all three were placed inside that factor, the display transfer
would divide out of the ratio exactly as Section 2.2 describes, and the model
would again be unable to say that a smaller pixel or a larger magnification
changes anything. The ordering of the noise terms is therefore not a modelling
refinement; it is the mechanism by which the display appears in the answer.

It also fixes what can be improved. A component upstream of the neural noise can
be made better and the improvement will reach the observer, subject to the
attenuation of every stage between. The neural noise cannot be improved by any
change to the imaging chain. When it dominates the sum — as Section 4.2 reports it
does over most of the band — the chain has stopped being the limiting factor, and
the remaining lever is the reading condition, because magnification and viewing
distance move the task relative to a noise that is fixed in visual angle.

## 2.4 Derived quantities

Four quantities are read off the contribution density.

**The saturation frequency** $f_{\mathrm{sat}}(\alpha)$ is the frequency below
which a fraction $\alpha$ of $d'^2$ has accumulated; $\alpha = 0.95$ throughout,
with 0.90 and 0.99 computed alongside so that the choice can be seen not to drive
the result. It locates the band that is delivered.

**The perceptual utilisation ratio** $R_{\mathrm{perceptual}}$ is the ratio of
$d'$ under the full chain to $d'$ under the ideal limit, and measures how much of
the available detectability survives the display and the eye.

**The gain per unit dose** $G_{\mathrm{useful}}$ is the increment in $d'^2$ per
increment in relative dose, evaluated as a finite difference along the dose axis.

**The sufficient magnification** $M^{*}$ is the magnification at which the
delivered band first covers the task. Since $d'$ is monotone in magnification
within this model, $M^{*}$ is a floor and not an optimum, and Section 5.3 says why
that is the honest form for a design statement.

$f_{\mathrm{sat}}$ needs a warning that the others do not, because it is the
quantity most likely to be quoted alone. It locates the band; it does not measure
how much arrives. The two come apart in a specific and predictable way: raising the
internal noise attenuates the high frequencies preferentially, which *lowers*
$f_{\mathrm{sat}}$ while also lowering $d'$. A reader comparing two conditions on
$f_{\mathrm{sat}}$ alone would find the noisier observer's band narrower and could
read that as a chain delivering less to a better observer, when it is a worse
observer receiving less from the same chain.

$f_{\mathrm{sat}}$ is therefore reported next to $d'$ and $G_{\mathrm{useful}}$
everywhere it appears, and never as a figure of merit on its own. The same
discipline governs the case study in Section 4.4, where a relative share and an
absolute detectability move in opposite directions for the same reason.

# 3. Methods

## 3.1 Implementation and reproducibility

The chain is implemented independently in numpy and scipy rather than assembled
from an existing toolkit, so that each transfer stage could be checked against its
primary source: the greyscale standard display function against DICOM PS3.14
[@dicomps314], the contrast sensitivity against Barten's tabulated values
[@barten1999], and the observer models [@burgess1994; @myers1987; @abbey2001]
against the closed-form results they reduce to when the noise is white.

Every random draw is seeded and every result file records the configuration that
produced it, together with the library versions and the protocol section it
implements. Rerunning a configuration reproduces its result file byte for byte;
the test suite performs that comparison rather than trusting it, so a change in a
dependency that moved a number would fail rather than pass quietly.

The reported detectability uses visual sensitivity inside the effective noise. An
earlier form of the model placed it as a weight on the numerator, and that form is
retained in the code and identified as superseded rather than deleted, because it
is the ideal-observer limit the appendix compares against and because a reader
checking an intermediate quantity against the earlier draft should find out that
the definition changed rather than conclude the implementation is wrong.

A generative artificial intelligence assistant (Claude Opus 5, Anthropic) was used
as a tool in developing and translating the software, in preparing figures from
result files already computed, and in language editing of this manuscript. It was
not used to generate, impute, or select any reported value: every number in the
text is resolved at build time from a machine-readable result file produced by the
code, and the build fails if a number cannot be traced to one. It was not used to
identify, screen, or judge candidate studies for the external validation, which
was carried out by the author against criteria frozen beforehand. The study design;
the eligibility rules; the quality-control criteria; and all scientific judgements,
interpretations, and conclusions are the author's, who takes full responsibility
for the content of this paper.

## 3.2 Conditions

The condition set is a full factorial over six axes: task diameter and task
contrast, relative dose, slice thickness, reconstruction kernel and magnification,
giving {{n_conditions}} conditions at a reconstruction Nyquist frequency of
{{nyquist_lpmm}} lp/mm. It is a grid rather than a sample, so no condition is
present because it was expected to be interesting, and the axes cross rather than
vary one at a time, so an interaction between the display and the acquisition
cannot be hidden by holding one of them fixed.

The axes were chosen for what they separate. Diameter and contrast move the task
through the frequency band independently, which is what distinguishes a task the
observer fails from one the chain fails to deliver. Dose and slice thickness move
the image noise without moving the signal. Kernel moves signal and image noise
together and leaves the neural floor alone, which is the property Section 4.1.1
uses as an internal check. Magnification moves the task relative to the observer
without touching the image at all, and it is the only axis in the set that a
reading protocol can change after the acquisition exists.

The remaining parameters are held at values stated in the configuration each
result file carries: viewing distance, luminance, display pitch, grey levels,
window width and the reference noise level. They are not swept here because they
are swept in the interval propagation of Section 3.3, where they enter as
properties of a reader rather than of a protocol.

## 3.3 Uncertainty propagation

The observer is not point-estimated, because the parameters that describe one are
literature ranges rather than measurements of any particular reader. Reporting a
single $f_{\mathrm{sat}}$ would state a precision the inputs do not have.

The ranges of the cognitive efficiency $\eta_{\mathrm{cog}}$ and the neural noise
scale $\kappa$, together with viewing distance, luminance and magnification, are
propagated by a seeded Latin hypercube of {{n_propagation_samples}} samples,
{{n_propagation_evaluations}} evaluations in all, and results are reported as 95%
bands.

The pairing matters more than the sample count. Each sample is held fixed across
the dose axis, so a series is evaluated by one coherent observer rather than by a
different draw at every dose. Resampling per dose point would let a favourable
observer appear at one dose and an unfavourable one at the next, which would widen
the band while also destroying the within-series comparison the hypothesis is
about: whether the gain per unit dose declines *for a reader*, not whether it
declines on average over readers who change between measurements.

## 3.4 Hypothesis tests declared in advance

Each hypothesis was given a rule that decides it before the quantities it decides
on were computed. The rules are stated here in the form they were frozen in, and
the protocol sections they come from are named so that the freezing can be checked
rather than taken on trust.

**H1 — saturation.** A condition saturates when the lower bound of the 95% band on
the decline of $G_{\mathrm{useful}}$ is positive. The rule is stated on the decline
and not on $G_{\mathrm{useful}}$ itself for a reason that would otherwise make the
test vacuous: more dose always means less image noise, so $G_{\mathrm{useful}}$
cannot change sign, and a test on its sign would be passed by any implementation
that runs at all. What is at issue is whether the *rate* falls, and whether it
falls by more than the observer parameters can account for, which is why the rule
is on the band rather than the point estimate.

**H2 — external agreement.** Within-study Spearman $\rho \ge 0.7$ against
published human observer performance, with the inclusion criteria, the pool
requirements and the rejection rule frozen before the literature search began.
The rule and the criteria are reproduced in Appendix A, and the registry records
every candidate screened and the criterion it failed.

**H3 — magnification.** $d'$ rises monotonically towards an asymptote in
magnification, so the quantity a design can be given is the sufficient
magnification $M^{*}$ at which the delivered band first covers the task, not an
optimum. This is a prediction about shape and not about level: an interior maximum,
had one appeared, would have falsified the serial-transfer form of the model rather
than merely shifting a number, since a chain in which each stage attenuates cannot
produce one.

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
the neural noise. NPWE [@burgess1994] and channelised Hotelling [@myers1987]
observers rank the conditions
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

Three studies were admitted [@yu2013; @paul2007; @leng2013], spanning
{{h2_n_yu2013}}, {{h2_n_paul2007}} and {{h2_n_leng2013}} condition points.
Within-study Spearman correlations between
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
chest-radiography candidates [@samei1999; @kroft2006; @macmahon1986; @herron2000;
@goo2004; @kimmesmith1996; @kimmesmith1995] were screened across two search
rounds and every one failed a frozen criterion — three on the condition-axis requirement, two on the
number of condition points, two on the reported figure of merit. The
pre-registration fixed the consequence of an unfilled slot before the search
began: **the generality claim narrows to CT**. The model is formulated generally
and is validated here on CT alone.

A second validation campaign was pre-registered after the above was complete, on
the ground that a pool of three studies is thin whatever its correlations. C1–C6
were carried over unchanged in substance; what was rewritten was the scope test,
from a list of modalities to the condition the model actually requires — a linear
system whose resolution and noise can be characterised by an MTF and an NPS — and
the pool requirement, raised to at least six studies of which at least three must
be newly admitted. The search terms were frozen before the search ran, and the
pre-registration recorded in advance that the floor might not be reachable and
that the round would then be reported as not having succeeded.

Nine candidates were judged on full text and none was admitted. Four failed on
the reported figure of merit: each reports a threshold contrast-detail index from
a phantom, or an ordinal visual-grading score, and neither is an AUC, a
two-alternative percent correct or a $d'$. Three failed on the condition-axis
requirement: two report the performance of a model observer and of no human, and
the third varied axes for which the model has no term. Two failed the scope test
for want of a published MTF and NPS for the imaging system, and one of those two
met every other criterion. The pool is therefore unchanged at three studies and
**the second round did not succeed** — the outcome its pre-registration named in
advance, rather than one it was amended to accommodate.

How the nine failed is more informative than the fact that they did. The two
requirements a study must meet — a background in which quantum and neural noise
are the limiting terms, and a figure of merit that is an AUC, a two-alternative
percent correct or a $d'$ — are each common on their own, but they rarely hold
together outside CT. Detection studies on radiographic systems overwhelmingly
report threshold contrast-detail indices or visual-grading scores, because those
are what phantom-based quality assurance produces. The studies that report an AUC
or a percent correct belong almost entirely to the lineage that compares model
observers with human observers, and that lineage is predominantly CT. The non-CT
slot is not empty because such work does not exist; it is empty because the two
requirements select for different literatures.

The clearest instance is a study that met every other requirement. It reports an
AUC for three readers under a multiple-reader multiple-case analysis, and it
measures the noise power spectrum of both its uniform and its anatomical
backgrounds, so the scope test would have been satisfied. But the axes it varied
were background type and single- against multislice reading, and the model has a
term for neither, so it contributes one admissible axis where two are required.
It fails not for any weakness of design but because what it set out to measure
lies outside what the model can predict. Three of the six frozen search terms
returned no hits at all, a consequence of combining seven to eleven terms
conjunctively; that weakness is recorded rather than repaired, because changing a
search term after seeing its yield is the search's own failure mode.

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

## 5.1 What the saturation frequency claims, and what it does not

$f_{\mathrm{sat}}$ is a statement about a chain, not about a scanner. Under the
stated display and viewing conditions, information above it does not reach the
observer; under a different magnification or viewing distance the same
reconstruction delivers a different band, and the model says so quantitatively
rather than as a caveat. The quantity that moves is the reading condition.

Two readings are not available from these results. The first is that a diagnosis
can or cannot be made: the model addresses near-threshold detection of a specified
signal, and detection is not diagnosis. Nothing here speaks to whether a finding is
recognised, characterised or acted upon, and the observer models used are not
clinical readers.

The second is that resolution beyond $f_{\mathrm{sat}}$ is wasted. In this model
sharper reconstruction never hurts and generally helps: the detectability integral
is monotone in the modulation transfer function, so a sharper chain delivers at
least as much at every frequency. What the results argue is narrower and more
useful — that whether the extra resolution *arrives* is decided downstream of the
reconstruction, by the display and the eye, and that this is measurable in advance
rather than discoverable only in a reading study.

A third bound is not a misreading but a condition of application. The noise in
this model is quantum and neural. Anatomic background — the structured,
patient-derived variability that dominates projection radiography and is present
in CT wherever a lesion sits against textured parenchyma — has no term in it.
Where that background is the operative limit, the $f_{\mathrm{sat}}$ computed
here is not the frequency at which information stops reaching the observer,
because the noise that bounds the task is not the noise the chain carries. The
results are stated for tasks in which quantum and neural noise are the limiting
terms, and Section 6 records what the literature search showed about how large
the difference can be.

## 5.2 The added band and the detectable task move in opposite directions

The case study makes a point that is easy to state backwards. The share of $d'^2$
arriving from above the conventional Nyquist frequency is largest for the smallest
task, and the smallest task is the one that is not detected at either resolution.
Where detection is actually happening, the added band contributes a fraction of a
percent.

The two quantities are anti-correlated by construction rather than by accident. A
task whose detectability is dominated by low frequencies is one the observer
already performs; a task pushed to the limit of the delivered band is one whose
signal has been carried into the frequencies the observer is worst at. So the share
of the total that arrives late rises exactly as the total falls.

The consequence for how a result like this should be reported is direct. A
maximum added-band share, quoted alone, reads as evidence that the finer chain
matters most for the hardest tasks. It is the same number that also says the
hardest tasks are not being performed. Any statement about an ultra-high-resolution
chain therefore has to carry an absolute detectability beside the relative gain, or
it will be read as a verdict on the scanner when it is a condition on the reading
protocol.

## 5.3 Design guidance: sufficiency rather than optimality

The magnification result should be read as a floor and not as a recommendation.
$M^{*}$ is the magnification at which the delivered band first covers the task; $d'$
is monotone in magnification, so there is no interior optimum to find and no point
at which further magnification becomes harmful within the model. The useful
statement is therefore of the form *this much is enough for this task under these
conditions*, not *this is the right amount*.

That the finer chain reaches its sufficient magnification at a lower value than the
conventional one is the expected behaviour of a chain limited by the observer. It
is also the practical form of the paper's argument: the way to make a finer
acquisition arrive is to change the reading condition until it does, and the amount
of change needed is computable from the reconstruction and the display without
running a reading study first.

## 5.4 What the external validation supports

The validation establishes that the model orders conditions as published human
observers did, on CT, in a majority of the studies that met criteria frozen before
the search. It does not establish that the absolute detectability is calibrated,
and the analysis was deliberately confined to within-study rank for that reason:
observer panels, decision criteria and task definitions differ between studies in
ways no rescaling repairs.

Ordering is the right target for the claims above, because each of them is an
ordering claim — that one reading condition delivers more than another, that a
band contributes more for one task than another, that one magnification suffices
where a smaller one does not. None of them requires the absolute level to be
right. The results that would require it, such as predicting a reader's detection
rate for a given lesion, are outside what this work supports.

# 6. Limitations

Two kinds of limitation are listed here and they do not carry the same weight.
One kind bounds the model: an assumption in the formulation, which a different
formulation could relax. The other bounds the evidence: something the validation
could not settle with the studies that existed and met criteria frozen before the
search. Reading them as one class would overstate the first and understate the
second.

The two entries in bold bound this work more than the rest, and there is one of
each kind. The validation covers CT because a pre-registered pool requirement
could not be met; that is a limit on the evidence, and a suitable study would
lift it. The model carries no anatomic-noise term; that is a limit on the
formulation, and no amount of further evidence would repair it. The second is
therefore the more serious of the two, and it is stated here at its full strength
rather than deferred to future work.

Neither was discovered after the results were seen. The narrowing to CT is the
consequence the pre-registration fixed in advance for exactly this outcome, and
the anatomic-noise bound was surfaced by a study the screening excluded on a
frozen criterion — an exclusion that nonetheless carried the most informative
fact in the search. Both changed what this paper claims: the first narrowed the
generality statement, the second bounded the scope statement in Section 5.

- Linear serial approximation, near-threshold detection tasks only.
- Absolute $d'$ is not calibrated; the results are ordering and relative
  quantities. The ranges of $\eta_{\mathrm{cog}}$ and $\kappa$ carry the
  absolute level.
- The external validation rests on published studies whose display conditions
  are often unreported; substituted values are listed per condition and swept.
- **The validation covers CT only.** The frozen pool required at least one
  non-CT study so that the generality of the formulation would rest on evidence.
  Seven candidates were screened in the first campaign and a further nine, on full
  text, in a second campaign pre-registered afterwards; none was admitted. The
  pre-registration fixed the consequence in advance, and it is taken here: the
  model is formulated generally and validated on CT. The second campaign also
  showed why the slot stays empty. A study must have a background in which quantum
  and neural noise are the limiting terms and must report an AUC, a
  two-alternative percent correct or a $d'$, and outside CT those two conditions
  select for different literatures: radiographic detection work reports
  contrast-detail indices and visual-grading scores, while the studies reporting an
  AUC or a percent correct are largely the model-observer lineage, which is CT.
  This is a statement about what exists to validate against, not about the
  quality of the excluded work.
- **Anatomic noise has no term in the model.** The nearest miss in the
  chest-radiography search [@samei1999] was excluded on the number of condition
  points, but the
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
`data/h2_studies.json` for the first campaign and `data/h2_studies_v2.json` for
the second.

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

**The second campaign, pre-registered after the first was complete.** C2 to C6
were carried over word for word. C1 was rewritten: where it had listed CT and
chest radiography, it now requires a linear system whose resolution and noise can
be characterised by an MTF and an NPS, obtainable either from the study or from
published characterisation of the device, with the set of admissible modalities
frozen in the same document. That is a statement of where the model applies, not
a widening — the background type still carries no power to exclude, and is
recorded as a descriptive variable with a prediction fixed in advance. The pool
requirement became at least six studies including those carried over, of which at
least three newly admitted, at least sixty condition points, and at least two
non-CT studies; and the document recorded, before the search ran, that the floor
might not be reachable and that the round would then be reported as not having
succeeded. It was not reachable. Nine candidates were judged and none admitted,
so the pool reported above is the first campaign's, unchanged.

# Data and code availability

All code, every results file the manuscript quotes, and the pre-registration
documents are available at {{repository_url}}, released as {{release_tag}}
(commit `{{release_commit}}`) and archived at {{zenodo_version_doi}}. That is
the version DOI of the release the
numbers in this paper were computed from, not the concept DOI: it resolves to
this snapshot and will continue to, whatever is released later.

The manuscript is built from a template in which every quoted number is a
placeholder resolved from `results/*.json`, so no result reaches the text by
being typed. `paper/numbers.json` records each quantity with the file and path
it was read from.

The claim that the H2 inclusion criteria were frozen before the literature
search is checkable rather than asserted. Commit `{{h2_freeze_commit}}` froze
the criteria; commit `{{h2_search_commit}}` recorded the first candidate scan.
A reader can confirm the order in the released repository with

```
git merge-base --is-ancestor {{h2_freeze_commit}} {{h2_search_commit}}
```

which succeeds only if the freeze precedes the search. The three subsequent
amendments to the pre-registration are separate commits, each carrying what was
changed and why, and every frozen reading is analysed and reported (Section 4.3).

`data/h2_studies.json` lists every candidate screened, admitted or excluded, with
the criterion each excluded study failed and the page or table each admitted
value was read from. The two independent digitisation passes are included. The
published papers themselves are not redistributed, and no imaging data of any
kind is included in the repository.

# References

<!-- Generated by pandoc --citeproc from paper/references.bib. Every DOI in that
     file resolves to the record it names; run tools/check_references.py. -->

::: {#refs}
:::

# Figure captions

<!-- Medical Physics asks for the captions to appear beneath each figure for
     review AND to be listed here after the references. The list below is
     generated from the captions in the body by paper/make_figures.py, so the two
     cannot disagree; do not type it by hand. -->

<!-- FIGURE-CAPTION-LIST -->

