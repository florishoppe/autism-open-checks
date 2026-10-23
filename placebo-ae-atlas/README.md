# Placebo-arm side-effect atlas for autism trials (version 0.1)

> **Read this first.** This is a first-pass check by a family member of an autistic child, done with substantial AI help (Claude). It has not been peer reviewed. Every number should be checked independently before anyone relies on it. It is not medical advice.

## Why

Researchers who design or interpret autism drug and supplement trials need to know how often adverse events turn up in **placebo** arms. Events on placebo (colds, irritability, poor sleep, stomach upsets) make drugs look more harmful than they are, and they shape what families are told when they consent. Placebo-arm adverse events have been pooled for ADHD medication trials (Faraone et al. 2022, *Mol Psychiatry*, PMID 33972692). As far as this check found, no one has pooled them for autism trials. A related study compared risperidone safety profiles across diagnoses using a class-effect query (Hopkins et al. 2022, *Clin Drug Investig*, PMID 36350559). Both PMIDs were checked against PubMed on 2026-10-23.

## What was done

1. **Search** (`01_fetch_extract.py`). ClinicalTrials.gov API v2, run on 2026-10-22. Each query and its hit count is in `query_log.tsv`:

   | Step | Hits |
   |---|---|
   | A. condition "autism", results posted | 287 |
   | B. broad condition terms (autism, autistic, autism spectrum disorder, asperger, pervasive developmental disorder), results posted | 289 |
   | C. B + interventional | 283 |
   | D. C + randomised (downloaded in full) | 190 |
   | E. D + "placebo" anywhere (for comparison only) | 107 |
   | D with a placebo arm (arm type PLACEBO_COMPARATOR, or "placebo" in an intervention name) | 109 |
   | ... with at least one usable placebo adverse-event group, after manual review | **89** |

   The placebo filter was applied locally to the 190 randomised trials rather than with query E, because a local filter is more sensitive.

   **Positive controls.** All of these were retrieved and kept: risperidone (NCT00576732), aripiprazole (NCT00332241, NCT00337571 and 4 more), bumetanide (NCT03715153), balovaptan (NCT03504917, NCT02901431) and oxytocin (NCT01944046 and 10 more). The second phase 3 bumetanide trial, NCT03715166, was terminated and has no posted results, so it cannot be included.

2. **Extraction.** For each trial we took the adverse-event module: event groups, numbers at risk, serious and other events, MedDRA term, organ system, vocabulary, assessment type (systematic or not), reporting threshold and time frame. We also took arm types, ages, phase, masking and sponsor. Outputs: `trials.tsv` (190 trials), `event_groups.tsv`, and `ae_raw.tsv` (8,682 term-by-group rows).

3. **Group roles.** Event groups were labelled as placebo or active from their titles. Every unclear title was reviewed by hand, and each decision, with its reason, is in `group_overrides.tsv`. Excluded from the placebo analysis:
   - open-label extensions;
   - second periods of crossovers (the same children counted twice);
   - typically developing control groups;
   - two studies that appear to enrol healthy volunteers;
   - two device (laser) trials;
   - **randomised-withdrawal** placebo arms (NCT00870727, NCT01227668, NCT00872898). In those trials, children came off an open-label drug, so their "placebo" events partly reflect stopping the drug.

4. **Term mapping** (`02_map_terms.py`, `term_mapping.tsv`). 1,365 distinct terms were mapped by explicit regex rules to 26 categories plus "other". `gi_any` combines vomiting, nausea, diarrhoea, constipation and abdominal pain. The table lists, for each term, the category, the text that matched and the number of trials using the term. False matches found during review were fixed, for example "temper" matching "body temperature", "cold" matching "cold sores", "nervous" matching "nervous system disorders" and "psychomotor" matching "psychomotor retardation". Most trials use MedDRA preferred terms, but a sizeable minority use free-text terms or CTCAE terms.

5. **Analysis** (`03_analyse.py`). The unit is the trial.
   - Within a trial arm, the number affected in a category is the largest `numAffected` among that category's terms. This is a lower bound, because summing terms would count the same child twice.
   - A category a trial did not list counts as 0.
   - Outputs:
     - `per_trial_category.tsv`: every trial × arm × category;
     - `results_placebo.tsv`: pooled estimates for all trials, children, mixed ages, adults, and trials with a 0% reporting threshold;
     - `results_drug_vs_placebo.tsv`: a descriptive comparison of drug and placebo arms, for all trials and for 9 antipsychotic trials;
     - `analysis_set.tsv`: one row per included trial.

To reproduce:

```
python3 -I 01_fetch_extract.py <cache_dir> .
python3 -I 02_map_terms.py .
python3 -I 03_analyse.py .
```

The scripts use only the Python standard library. The raw JSON is cached outside the repo and is not committed.

## Main result: placebo arms, 89 trials, 2,905 participants on placebo

Children = maximum eligible age under 18 (66 trials). Adults = minimum age 18 or older (13 trials). The other 10 trials enrolled mixed ages.

**How to read the columns:**
- *All trials %* is the pooled proportion (total affected / total on placebo, Wilson 95% CI), with unlisted categories counted as 0. It is a **lower bound**.
- *% within listing trials* uses only the trials that listed that category. It is an **upper-leaning** figure, because trials list a term mainly when it is common.
- The true placebo-arm rate is probably between the two.
- I² comes from a DerSimonian-Laird logit model. It is a rough guide to heterogeneity only (see limits).

| Category | All trials: % (95% CI) | Trials listing it (of 89) | % within listing trials | Children | Adults | I² |
|---|---|---|---|---|---|---|
| respiratory/ENT infection, cold | 11.3 (10.2-12.5) | 57 | 16.0 | 12.3 | 8.2 | 75% |
| irritability, agitation, aggression | 9.3 (8.3-10.4) | 55 | 14.1 | 11.1 | 0.3 | 71% |
| any GI (vomiting, nausea, diarrhoea, constipation, abdominal pain) | 9.2 (8.2-10.3) | 67 | 11.2 | 10.0 | 6.0 | 68% |
| headache | 7.0 (6.1-7.9) | 53 | 9.7 | 7.3 | 3.1 | 49% |
| diarrhoea | 6.1 (5.3-7.1) | 45 | 9.9 | 6.4 | 4.8 | 61% |
| insomnia / sleep disturbance | 5.9 (5.1-6.8) | 47 | 9.9 | 6.6 | 3.1 | 57% |
| vomiting | 5.9 (5.1-6.8) | 44 | 9.8 | 6.8 | 0.9 | 55% |
| somnolence, sedation, fatigue | 5.2 (4.4-6.0) | 49 | 8.5 | 5.8 | 0.9 | 56% |
| cough | 4.0 (3.3-4.7) | 39 | 7.3 | 4.4 | 0.3 | 46% |
| fever | 3.6 (3.0-4.3) | 36 | 7.1 | 4.2 | 0.0 | 30% |
| hyperactivity, restlessness | 3.3 (2.7-4.1) | 30 | 8.5 | 4.0 | 0.0 | 38% |
| appetite decreased | 3.3 (2.7-4.1) | 29 | 8.3 | 4.0 | 0.0 | 40% |
| appetite increased | 2.9 (2.4-3.6) | 27 | 7.7 | 3.5 | 0.0 | 51% |
| constipation | 2.9 (2.3-3.6) | 32 | 6.1 | 3.5 | 0.0 | 17% |
| rash / skin | 2.8 (2.2-3.5) | 37 | 6.3 | 3.3 | 0.3 | 36% |
| abdominal pain / discomfort | 2.8 (2.2-3.5) | 38 | 5.6 | 3.0 | 0.6 | 29% |
| anxiety | 2.1 (1.6-2.6) | 33 | 4.4 | 1.9 | 2.3 | 0% |
| enuresis | 1.8 (1.4-2.4) | 22 | 5.9 | 2.2 | 0.0 | 30% |
| nausea | 1.6 (1.2-2.1) | 25 | 4.6 | 1.5 | 2.6 | 0% |
| gastroenteritis | 1.1 (0.8-1.6) | 17 | 4.0 | 1.3 | 0.0 | 12% |
| low mood | 1.1 (0.8-1.6) | 21 | 3.9 | 1.2 | 0.6 | 0% |
| dizziness | 1.1 (0.8-1.6) | 18 | 3.9 | 0.7 | 3.1 | 0% |
| tremor / extrapyramidal / drooling | 1.1 (0.8-1.5) | 19 | 3.4 | 1.2 | 0.0 | 17% |
| self-injury | 0.9 (0.6-1.3) | 17 | 3.5 | 0.9 | 0.0 | 0% |
| weight increased | 0.7 (0.5-1.1) | 12 | 3.3 | 0.9 | 0.0 | 0% |
| weight decreased | 0.4 (0.2-0.7) | 5 | 3.5 | 0.5 | 0.0 | 0% |
| seizure | 0.3 (0.2-0.6) | 16 | 1.1 | 0.3 | 0.0 | 0% |

**Sensitivity check: trials with a 0% reporting threshold.** In the 47 trials that list every event, the figures are close to the main ones:
- irritability: 12.1%
- respiratory/ENT infection: 11.6%
- any GI: 9.7%
- sleep: 5.9%
- somnolence: 4.5%

**Drug arms vs placebo arms (descriptive only, not a treatment-effect estimate).** Across all 89 trials (3,737 participants in drug arms), most categories are similar in drug and placebo arms. Drug arms show more:
- somnolence: 8.5% vs 5.2%;
- decreased appetite: 5.2% vs 3.3%;
- tremor/EPS: 1.9% vs 1.1%.

Irritability is listed slightly *less* often on drug (7.8% vs 9.3%), as is hyperactivity (2.2% vs 3.3%). In the 9 antipsychotic trials (411 on placebo, 693 on drug), the expected pattern shows up:

| Category | Drug | Placebo |
|---|---|---|
| somnolence | 18.8% | 7.1% |
| vomiting | 10.8% | 4.6% |
| increased appetite | 9.4% | 5.8% |
| tremor/EPS | 5.1% | 1.2% |
| weight increased | 3.9% | 2.4% |

These pattern checks make it more likely that the extraction is working.

## What this suggests (to be checked)

- In children's autism trials, roughly **1 in 9 children on placebo** has irritability, agitation or aggression recorded as an adverse event, about 1 in 8 a cold or similar infection, 1 in 10 a GI complaint, and about 1 in 15 a sleep problem. Those figures are lower bounds.
- Irritability is often both the condition being treated and an adverse event. Unless a trial accounts for this placebo-arm rate, an "irritability" signal in a drug arm says little.
- Weight gain is rarely listed as an adverse event on placebo or on drug. In antipsychotic trials it is usually measured as an outcome instead, so this registry layer understates it.

## Limits

- **Reporting thresholds.** 36 of 89 trials list "other" adverse events only above 5%, and 6 more above 1-4%. Below-threshold events are invisible and are counted here as 0. This is why the main column is a lower bound.
- **Unknown ascertainment.** The registry records whether a term was "systematically" assessed (61% of placebo rows), "non-systematically" assessed (34%) or not stated (5%). It does not say whether the trial used a structured side-effect checklist, open questions or parent diaries, or who reported the event. Checklists raise the reported rates. Coding this from protocols and papers is the obvious next step.
- **Selection.** Only trials with posted results are included. Older trials (before about 2008), most non-US trials, academic trials that never posted results and terminated trials (for example NCT03715166) are missing. Trials that post results may differ from those that do not.
- **Term harmonisation.** Mapping used regex rules on reported terms, not a MedDRA hierarchy. Composite free-text terms ("nausea/vomiting/diarrhea") go to the first matching category, and a few remaining misfits are likely. `term_mapping.tsv` is meant to be reviewed.
- **Counting.** Taking the largest term per category undercounts children with several related terms. Summing would overcount. Participant-level data would be needed to do better.
- **Heterogeneity and pooling.** Trials differ in duration (days to 6 months), age, background medication and the diagnosis targeted (irritability, ADHD symptoms, anxiety, social function). The random-effects logit estimates in `results_placebo.tsv` (`re_logit` columns) use a 0.5 continuity correction. Because many trials have zero cells, this inflates rare categories (seizure: 2.6% by random effects vs 0.3% simple), so they are not the headline. A proper analysis would use a GLMM or a beta-binomial model in R.
- **Crossover trials.** Only the first period was kept where the sequence could be identified. Some crossover placebo groups may still pool both periods.
- **Group roles** come from group titles plus a manual review (`group_overrides.tsv`). A few groups may be mislabelled.
- **Age groups** come from eligibility limits, not the ages actually enrolled.

## Files

| File | What it holds |
|---|---|
| `01_fetch_extract.py` | API queries and extraction |
| `02_map_terms.py` | term-to-category rules |
| `03_analyse.py` | pooling |
| `query_log.tsv` | every query, hit count and URL |
| `trials.tsv`, `event_groups.tsv`, `ae_raw.tsv` | raw extracted tables |
| `group_overrides.tsv` | manual group-role decisions |
| `term_mapping.tsv` | reviewable term mapping |
| `analysis_set.tsv`, `per_trial_category.tsv` | analysis set |
| `results_placebo.tsv`, `results_drug_vs_placebo.tsv` | results |

## Possible next steps

1. Have someone with pharmacovigilance or MedDRA experience review `term_mapping.tsv` and `group_overrides.tsv`.
2. Code how each trial asked about adverse events (checklist, open question, diary; parent or clinician) from protocols and papers, and test whether checklist trials report more placebo-arm events.
3. Add trials without posted results from published papers (CONSORT harms tables).
4. Refit the pooled model with a binomial GLMM in R.
