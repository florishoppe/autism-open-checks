# Does starting a laxative reduce recorded challenging behaviour?

**A proposed within-person analysis for CPRD-type primary-care data, motivated by Millington et
al., BMJ Open 2026 (doi:10.1136/bmjopen-2025-111117).** Draft for discussion, October 2026.

*Prepared with substantial help from an AI system (Anthropic's Claude) by a non-specialist.
References were checked against PubMed and Europe PMC, but the design and every figure here should
be checked independently before being relied on.*

## 1. Question

Millington et al. found that incident constipation is followed by more challenging-behaviour records
(HR 1.89, 1.74–2.05). That is consistent with constipation pain driving behaviour, but also with
shared causes: illness, medication changes, or a period of more GP contact. **If pain is part of
the cause, effective treatment should be followed by a fall in recorded challenging behaviour
within the same person, and the fall should be larger when treatment continues.** No trial has
tested this with a behaviour outcome in autistic children or in people with intellectual
disabilities, and parent-rated outcomes cannot test it well, because parents know when treatment
has started.

## 2. Design: within-person comparison around the first laxative prescription

**Index event.** The first prescription of a laxative (BNF chapter 1.6, or the equivalent dm+d
codes) after cohort entry, with at least 12 months of prior registration and no laxative
prescription in that time.

**Non-acute index only.** This guards against reverse causation: a behaviour crisis prompting both
the consultation and the prescription. The index consultation is eligible only if none of the
following was recorded in the preceding 30 days:
- a challenging-behaviour code;
- an emergency-department attendance or out-of-hours contact;
- an injury code;
- a new or increased psychotropic prescription.

**Windows**, relative to the index date:

| Window | Days | Role |
|---|---|---|
| Baseline | −210 to −31 | Comparison period |
| Pre-index | −30 to −1 | Excluded: absorbs any build-up that led to the consultation |
| Early treatment | 1 to 90 | Primary exposure window |
| Later treatment | 91 to 180 | Secondary |

**Comparison groups**, defined from prescriptions after the index date:
- **Persistent:** at least two further laxative issues within 90 days.
- **Single-fill:** no further laxative issue within 180 days.
- **Negative control:** a first emollient prescription (BNF 13.2.1) at a non-acute consultation,
  with the same windows and exclusions, in people with no laxative in the same period.

Single-fill users share whatever prompted a laxative but received little treatment. Emollient
starters share the "new routine prescription" signal but have no gut mechanism.

## 3. Outcomes

- **Primary:** the rate of challenging-behaviour records (the study's code list, recurrent events),
  compared within person between the early-treatment window and baseline.
- **Secondary:**
  - the same in the later-treatment window;
  - new or increased antipsychotic prescriptions;
  - injury-related consultations;
  - sleep-problem codes.

## 4. Analysis

- **Model.** Conditional Poisson regression (each person as their own stratum) for window-specific
  rate ratios. Allow for overdispersion (robust variance, or negative binomial with person
  effects). Adjust for age and season as time-varying terms.
- **Primary estimate.** The ratio of rate ratios, early treatment against baseline, for persistent
  versus single-fill users. Pre-specified effect of interest: a fall of 15% or more (RRR ≤ 0.85).
- **Negative-control check.** The emollient rate ratio should be about 1. If it is not, the
  persistent-versus-single contrast is read against it.
- **Pre-specified subgroups.**
  - Autistic people (about 18% of the cohort).
  - Under-18s (103,542 person-years in the cohort).
  - People not on antipsychotics at index. Antipsychotics are themselves constipating, so a
    prescribing cascade could create a spurious pattern.
- **Sensitivity analyses.**
  1. Exclude anyone who started an opioid, anticholinergic or antipsychotic within ±90 days of
     index (the prescribing cascade).
  2. A 60-day pre-index exclusion instead of 30.
  3. Restrict to an index on the same day as an incident constipation code.
  4. The event-dependent-exposure extension of the self-controlled case series, as an alternative
     estimator.
- **Pre-registration.** Register the plan (OSF) before the outcome data are extracted or examined.

## 5. Power (rough, before seeing the data)

The power below assumes the whole-cohort rate of 0.10 challenging-behaviour records per
person-year (Millington et al., Table 2). It uses 180-day comparison windows, Poisson variance and a two-sided
5% test, for a 15% fall in the persistent group alone:

| Persistent laxative starters | Expected baseline events | Power |
|---|---|---|
| 2,000 | ~100 | ~0.2 |
| 5,000 | ~250 | ~0.4 |
| 10,000 | ~500 | ~0.7 |
| 20,000 | ~1,000 | ~0.95 |

The persistent-versus-single contrast needs roughly twice these numbers, and overdispersion will
reduce power further. **The first useful step is a feasibility count:** how many non-acute first
laxative starts are in the extract, by group and subgroup. If the counts are too low for the
autistic or under-18 subgroups, the full-cohort result is still informative, and the subgroups are
reported as descriptive.

## 6. Interpretation, decided in advance

| Result | Reading |
|---|---|
| Persistent group falls ≥15%, single-fill and emollient groups about flat | Consistent with treating constipation reducing challenging behaviour; motivates a trial with a behaviour outcome |
| Persistent and single-fill fall equally, emollient flat | A consultation or attention effect, or a crisis passing, rather than treatment |
| All groups fall, emollient included | Regression to the mean or a prescribing artefact; the design cannot separate effects |
| No fall, with adequate power | Lowers the ceiling on constipation pain as a driver of recorded challenging behaviour |

## 7. Limits

- GP-recorded challenging behaviour captures only what reaches the GP. Most is managed elsewhere
  (Millington et al. note this), so the outcome is a sample of events, not a measure of them.
- Laxatives are also bought over the counter, and adherence is incomplete. Both bias the result
  towards finding no effect.
- Prescription refills show that treatment continued, not that it worked.
- The approach needs the prescribing (therapy) file in the extract, and probably an ISAC
  (now RDG) protocol amendment.
