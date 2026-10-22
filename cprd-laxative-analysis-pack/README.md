# Analysis pack: laxative start and recorded challenging behaviour

A within-person analysis of whether starting a laxative is followed by fewer recorded
challenging-behaviour events, for UK primary-care records (CPRD) such as the cohort in
Millington et al., BMJ Open 2026 (doi:10.1136/bmjopen-2025-111117), which found incident
constipation followed by more challenging-behaviour records (HR 1.89). Nothing here has been run
on real CPRD data.

> **Read this first.** This pack was written with substantial help from an AI system (Anthropic's
> Claude), by someone who is not a statistician or clinician. It has been tested only on
> simulated data. Every part — design choices, code, code lists — needs review by the study's
> analyst and clinicians before any use on real data. Nothing here has touched CPRD data.

## Contents

| File | What it is |
|---|---|
| `R/laxative_analysis.R` | The analysis. Builds the cohort, counts events per window, fits within-person (person-stratified) quasi-Poisson models, and runs the primary contrast, subgroups and sensitivity analyses. Includes a small-cell suppression helper |
| `R/simulate_cprd_like.R` | Generates simulated tables in the expected input shape, with known true effects |
| `R/run_tests.R` | 9 checks that the analysis recovers known effects (see below) |
| `R/coverage_check.R` | Repeats the primary contrast over many simulated datasets to check bias and interval coverage |
| `codelists/*_DRAFT.csv` | Draft code lists, by substance and BNF section. **Not** CPRD product or medical codes: the team maps these to Aurum/Gold dictionaries and reviews them clinically |
| `RESULTS-TEMPLATE.md` | Tables and interpretation rules to fill from aggregate output |

## Inputs the analysis expects

Three analysis-ready tables, derived by the study team from their extract with their own code
lists:

- `patient`: patid, dob, sex, autism (0/1), regstart, regend (Date)
- `events`: patid, eventdate, type ∈ {cb, ed, injury, psychotropic_up}
- `prescriptions`: patid, issuedate, class ∈ {laxative, emollient, antipsychotic, opioid,
  anticholinergic}

Then:

```r
source("R/laxative_analysis.R")
out <- run_analysis(list(patient = patient, events = events, prescriptions = prescriptions))
suppress_small(out$feasibility)   # check before release
out$results                       # RR / RRR with 95% CI, people and events per analysis
```

Result terms:
- `early` and `later`: rate ratios for days 1–90 and 91–180 against baseline (days −210 to −31).
- `early_vs_ref` and `later_vs_ref`: ratios of rate ratios against the reference group (for
  "persistent vs single", the reference is single-fill).

## Testing done (simulated data only)

Run with R 4.x, using the data.table, gnm and survival packages, from this folder:

```bash
Rscript R/run_tests.R
```

All 9 checks pass:

- **True 30% fall in persistent users.** The persistent RR is 0.62 (0.52–0.74). The
  persistent-vs-single RRR is 0.70 (0.54–0.90). Single-fill and emollient are about 1.
- **No true effect, with 30% of starts prompted by a behaviour crisis.** After the non-acute
  filter, the RRs cover 1. The naive analysis that keeps acute starts shows a spurious fall
  (RR 0.79, 0.70–0.89). This is the reason the filter exists.
- Subgroup analyses run, and small cells are suppressed.

`Rscript R/coverage_check.R 30` runs 30 simulated datasets per scenario, each with 25,000 people:

| True RRR | Mean estimate | 95% CI coverage | Share finding an effect |
|---|---|---|---|
| 0.70 | 0.68 | 97% | 77% |
| 1.00 | 0.98 | 100% | 0% |

A bug was caught by these tests during development. The first version specified the group
interaction with R's default coding, and the person strata silently aliased it. That version gave
an RRR of 1.07 when the truth was 0.70. It now uses explicit indicator variables.

## Known gaps

- Not implemented:
  - the event-dependent-exposure self-controlled case series (plan §4, sensitivity 4);
  - the "same day as an incident constipation code" restriction;
  - adjustment for age and season as time-varying terms (plan §4). With 180-day windows inside
    each person, this is likely to matter little, but the analyst should decide.
- "psychotropic_up" needs dose-increase logic from quantity and strength fields. The pack treats it
  as a pre-labelled event type.
- The simulation does not model:
  - over-the-counter laxatives;
  - seasonality;
  - recurrent constipation episodes;
  - the real distribution of time-to-refill.
- The code has not been run on anything resembling the size of the real extract. Performance at
  ~167,000 people should be fine for data.table but is untested for gnm with many strata.
