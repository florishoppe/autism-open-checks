# Autism mentions in US emergency-department injury narratives (NEISS), 2013–2024

**Date:** 2026-10-22, updated the same evening with 2018–2024. **Verdict: GO, for a descriptive hazard study, with the caveats below.** The full period is now 2013–2024: 2,441 autism mentions.

## What was planned and what was possible

The plan was 2014–2024. CPSC's NEISS site blocked automated downloads (Akamai 403), and its query
tool showed "undergoing maintenance". DataLumos, which holds archived annual NEISS files, sits behind
a human-verification check, which was not bypassed. The analysis therefore used the copy of the
CPSC-released NEISS data in Hadley Wickham's open `neiss` R package
(github.com/hadley/neiss, `injuries.rda`). That copy covers **2013–2017: 1,865,651 cases with
narratives.** 2018–2024 still needs the CPSC files, either once the site is back or downloaded by
hand in a normal browser.

Scripts: `01_extract.R` (the count). The sample of 200 is in `sample200.tsv`, and the codes are in
`sample200_coded.tsv`, which merges `codes_all.txt`.

## 1. Count

Search: `AUTIS*`, `ASD`, `ASPERG*`, `PDD` anywhere in the narrative.

| Year | Cases | Autism mentions | Per 100,000 cases | Weighted national estimate |
|---|---|---|---|---|
| 2013 | 376,926 | 126 | 33 | ~3,500 |
| 2014 | 367,493 | 135 | 37 | ~3,300 |
| 2015 | 359,129 | 136 | 38 | ~3,500 |
| 2016 | 375,197 | 165 | 44 | ~3,500 |
| 2017 | 386,906 | 184 | 48 | ~5,000 |
| **Total** | **1,865,651** | **746** | | |

**About 150 mentions a year, rising**, against a go threshold of about 100. The weighted figures
estimate ED visits *where autism was written in the note*. They are not an estimate of all injuries
to autistic people. Ages skew towards childhood: 63% of mentions are aged 5–19, against 32% of all
NEISS cases.

## 2. Hand-read of 200 narratives

40 narratives per year were drawn at random (seed 20261022) and read in full. Each was coded for:
- whether the autistic person was the patient;
- the injury mechanism;
- whether the note describes distress or a behavioural context;
- whether the note adds prevention-relevant detail beyond the coded product.

**The reading and coding were done by Claude (AI), as a single coder.** A human second coder on at
least 50 notes is needed before any of this is published.

**Precision.** In 193 of 200 notes (96.5%) the patient is the autistic person. Six describe a
family member or carer injured by or while caring for an autistic person. One is a false positive:
"ASD" meaning atrial septal defect.

**Mechanisms**, among the 193:

| Mechanism | n | % |
|---|---|---|
| Accidental contact (ran into, struck, caught) | 45 | 23 |
| Fall | 39 | 20 |
| Self-injury (head-banging, hitting self) | 26 | 13 |
| Foreign body swallowed or inserted | 21 | 11 |
| Injury during distress or agitation (punching a window or wall, tantrum) | 18 | 9 |
| Poisoning (bleach, detergent, medicines, gasoline) | 17 | 9 |
| Seizure-related | 4 | 2 |
| Burns | 4 | 2 |
| Repetitive movement (rocking, jumping, rubbing) | 4 | 2 |
| Self-harm with suicidal intent | 3 | 2 |
| Drowning or submersion (2 bathtub, 1 pool during a seizure) | 3 | 2 |
| Injured during restraint | 2 | 1 |
| Other / assaulted | 7 | 4 |

**Findings that matter more than the counts:**

1. **A quarter of these injuries are behavioural, but NEISS codes them as products.** Self-injury,
   distress, self-harm and restraint together account for 49 of 193 (25%). In 34 of those 49 the
   coded "product" is a wall, window, door or floor. "Ceilings and walls" is the single most common
   product code across all 746 mentions (95). **A product-coded analysis of NEISS would read
   head-banging as a building-material hazard.** Only the narrative shows the difference, and that
   finding alone is worth a short paper.
2. **About a fifth are swallowing and poisoning** (38 of 193). They include lithium coin cells from a
   light-up toy, a hearing-aid battery, a balloon causing bowel obstruction, bleach left in a cup,
   medicines in a purse or school bag, gasoline, and paint chips with a lead level of 39. Several are
   prevention-specific.
3. **Glass and tip-overs:**
   - children running or falling through glass doors (4);
   - punching windows during distress (5+);
   - TVs and dressers tipping onto young children (3);
   - two falls from second-storey windows, one with a movable screen.
4. **Seizures appear inside "falls" and drownings** (5 notes). This links to the seizure-alarm check in `../seizure-alarm-stereotypy/` (seizure
   alarms).
5. **Narratives add prevention-relevant detail beyond the product code in 50 of 193 (26%).** This
   was the second go criterion.

## 3. Go / no-go

| Criterion | Result |
|---|---|
| ~100 or more confirmed mentions a year | **Met:** ~150/year, 96.5% precision |
| Narratives more informative than the product codes | **Met:** 26% add hazard detail, and the coding misclassifies a quarter of injuries |
| Prior work using NEISS narratives for autism | None found (checked 2026-10-22) |

## Caveats

- **Mention-based.** Autism is written in the note only sometimes, and probably more often when it
  explains the injury. So the data show *patterns* of injury among recorded cases, not rates or risk
  relative to non-autistic people. Self-injury may be over-represented because staff note autism
  when it explains the mechanism.
- 2013–2017 only so far, and a single AI coder.
- Weighted estimates assume the mention is independent of NEISS sampling, which is untested.

## Next steps (not done)

1. Get 2018–2024 from CPSC once the site is back. A manual browser download by you would also work.
2. A second, human coder on 50+ notes, with a codebook and Cohen's kappa.
3. A comparison group: an age-matched random sample of non-mention narratives, for proportional
   mechanism ratios.
4. Approach injury epidemiologists already working on autism and ED data before writing anything.
   For example, the authors of the 2026 autism drowning study (PMID 40146314).


---

## Update: 2018–2024 added (2026-10-22, evening)

The official CPSC annual files were downloaded by hand from the CPSC website (`neiss2014.tsv`, `neiss2018.tsv` … `neiss2024.tsv`)
by hand. Two checks confirm the copies agree:
- the CPSC 2014 file has 133 `AUTIS` mentions, exactly as in the hadley/neiss copy;
- its case count matches to within one row.

Script: `02_extend_cpsc.py`. Output: `autism_mentions_2018_2024.tsv`.

| Year | Cases | Autism mentions | Per 100,000 cases | Weighted estimate |
|---|---|---|---|---|
| 2018 | 361,668 | 178 | 49 | ~4,900 |
| 2019 | 358,716 | 198 | 55 | ~5,700 |
| 2020 | 309,370 | 192 | 62 | ~5,400 |
| 2021 | 340,444 | 232 | 68 | ~6,500 |
| 2022 | 323,343 | 248 | 77 | ~7,700 |
| 2023 | 338,265 | 237 | 70 | ~7,900 |
| 2024 | 361,672 | 410 | 113 | ~14,500 |

**Across 2013–2024 there are 2,441 mentions.**

**The rise is mostly a recording effect, not evidence of more injuries.** Narratives lengthened
steadily: mean 87 characters in 2018, 116 in 2021, 118 in 2023 and 134 in 2024. Longer notes record
more of the patient's history, so autism gets written down more often. Autism diagnosis rates also
rose over the period. Mention counts must not be read as an injury trend.

**Accuracy in recent years is lower.** A random spot-check of 40 notes from 2022–2024
(`spotcheck40_2022_2024.tsv`, seed 20261023) found:
- 35 of 40 (87.5%) were about an autistic patient;
- 3 described someone else injured by an autistic child or adult;
- 2 were false matches: "ASD" meaning a heart defect, and a note about a *family history* of autism.

Longer narratives bring more incidental mentions, so recent years need a filter or a human check.
The 2013–2017 hand-read found 96.5%.

**Hazard keywords across all 2,441 mentions.** These are crude text matches, not coded, and counts
include some non-patient and incidental cases.

| Hazard | Mentions |
|---|---|
| Head-banging or hitting head against a wall | 286 |
| Wandering or elopement ("ran away", "wander", "elope") | 5 (corrected 2026-10-22; first published as 63 because "ELOP" also matched "devELOPmental") |
| Batteries (11 naming button or lithium coin cells) | 31 |
| Drowning or submersion | 17 |
| Falls from windows | 16 |
| Magnets | 14 |
| Restraint | 10 |
| Water beads | 6 |

Three things stood out in the recent spot-check:
- **Battery chewing and swallowing:** AAA batteries in 3 of 40 notes.
- **Water beads:** a child passing them in stool. CPSC has issued safety warnings about water beads.
- **A 14-year-old who swallowed 12 quarters** while mouthing coins for their taste. The note itself
  says this was to provide stimulus, which points to sensory seeking.

**Revised next steps:**
1. A human-coded sample from 2018–2024, stratified by year, with a filter for incidental mentions.
2. The comparison group and the second coder, as above.
3. Use mechanism *proportions*, not counts, given the narrative-length change.
4. Discuss with injury epidemiologists already working on autism and ED data before writing anything up.

---

## Comparison group: what is different about injuries with autism in the note (2018–2024)

Script: `03_compare.py`. Output: `comparison_2018_2024.tsv`.

Each of the 1,695 autism-mention cases was matched to up to 10 other NEISS cases with the same
year, sex and single year of age, giving 16,923 comparison cases. The table compares the *share* of
cases with each feature, using CPSC's coded fields and a few text keywords. These are
**proportion ratios within ED-treated injuries, not risks.** They say what kind of injury brings
someone with autism in their note to the ED, compared with same-age peers.

| Feature | Autism % | Comparison % | Ratio (95% CI) |
|---|---|---|---|
| Head-banging (text) | 13.6 | 1.1 | **12.6** (10.5–15.2) |
| Seizure mentioned (text) | 5.2 | 0.6 | **8.4** (6.3–11.1) |
| Battery (text) | 1.4 | 0.2 | **6.5** (3.9–10.8) |
| Diagnosis: poisoning | 6.3 | 1.1 | **5.6** (4.5–7.1) |
| Window fall (text) | 0.6 | 0.1 | 5.0 (2.4–10.3) |
| Diagnosis: submersion | 0.6 | 0.1 | 4.6 (2.3–9.3) |
| Diagnosis: ingested foreign body | 7.5 | 1.7 | **4.5** (3.6–5.5) |
| Magnet (text) | 0.7 | 0.2 | 4.3 (2.2–8.4) |
| Punched a wall, window or door (text) | 2.7 | 0.8 | 3.3 (2.4–4.6) |
| Diagnosis: internal organ / head injury | 20.2 | 9.8 | 2.1 (1.9–2.3) |
| Body part: head | 27.5 | 16.0 | 1.7 (1.6–1.9) |
| Admitted to hospital | 8.0 | 4.8 | 1.7 (1.4–2.0) |
| Location: home | 47.0 | 29.8 | 1.6 (1.5–1.7) |
| Location: school | 9.5 | 7.9 | 1.2 (1.0–1.4) |
| Diagnosis: laceration | 17.7 | 19.2 | 0.9 (0.8–1.0) |
| Hand or finger | 9.0 | 12.9 | 0.7 (0.6–0.8) |
| Diagnosis: fracture | 6.3 | 16.0 | **0.4** (0.3–0.5) |
| Location: sports or recreation | 3.4 | 20.1 | **0.17** (0.13–0.22) |
| Organised sports (text) | 0.8 | 16.7 | **0.05** (0.03–0.08) |

**Reading it:**

- **Self-injury, swallowing and poisoning define the pattern.** Head-banging is 13 times more
  common in the case mix. Swallowed objects, poisoning, batteries and magnets are 4–6 times more
  common.
- **Sports injuries are almost absent:** a twentieth of the comparison rate. Autistic children and
  adults may play fewer organised sports. Notes about sports injuries may also be less likely to
  mention autism.
- **Injuries happen at home far more,** and lead to admission more often (1.7×).
- **Seizures appear 8 times more often in the notes.** This fits the seizure-alarm check in `../seizure-alarm-stereotypy/`: seizure-related injuries
  are a visible share of these ED visits.

**What inflates these ratios.** Staff are more likely to write "autistic" when it explains the
injury, as with head-banging or swallowing a battery, than when it doesn't, as with a sports
sprain. So the ratios mix real differences with *recording* differences. The direction of the big
ones is plausible. Their size is not a measure of excess risk. About 12% of mentions in these years
are incidental or concern someone else, which dilutes the ratios towards 1.

**Why it is still useful:** it says where prevention attention should go — batteries and magnets
in the home, poisons stored within reach, window safety, bath and pool supervision, and seizure
safety. And it says the NEISS product codes alone would miss most of this.

---

## Fairer comparison: autism against other conditions recorded the same way (2018–2024)

Script: `04_other_conditions.py`. Output: `comparison_other_conditions_2018_2024.tsv`.

**Why.** The comparison above is against all other cases. Coders write a condition into a note
mainly when it helps explain the injury, so "everyone else" is a biased reference: any
condition-mention group would look different from it. The project's own stress test recommended
comparing against notes that mention *other* conditions recorded in the same selective way. That
was not done in the first version, and this section corrects it.

**Groups**, ages 2–25, 2018–2024. Notes mentioning autism are excluded from the other groups.

| Group | Autism | ADHD | Down syndrome | Cerebral palsy | Developmental delay / ID |
|---|---|---|---|---|---|
| Cases | 1,381 | 175 | 86 | 93 | 189 |

| Feature | Autism | ADHD | Down | CP | DD/ID | Autism vs pooled others (95% CI) |
|---|---|---|---|---|---|---|
| Head-banging (text) | 13.3% | 10.9% | 4.7% | 1.1% | 4.8% | **2.18** (1.53–3.12) |
| Fracture | 6.1% | 4.0% | 9.3% | 17.2% | 9.0% | **0.69** (0.49–0.97) |
| Ingested foreign body | 8.5% | 6.3% | 4.7% | 3.2% | 10.6% | 1.21 (0.85–1.72) |
| Poisoning | 7.2% | 12.0% | 8.1% | 1.1% | 2.1% | 1.18 (0.81–1.73) |
| Battery (text) | 1.6% | 1.7% | 0% | 1.1% | 2.1% | 1.08 (0.48–2.41) |
| Seizure (text) | 5.0% | 3.4% | 2.3% | 6.5% | 9.0% | 0.88 (0.58–1.32) |
| Admitted | 7.9% | 7.4% | 9.3% | 10.8% | 14.3% | 0.74 (0.55–1.00) |
| Home | 49.3% | 39.4% | 39.5% | 62.4% | 48.7% | 1.06 (0.95–1.18) |
| Sports or recreation | 3.8% | 4.6% | 14.0% | 0% | 5.3% | 0.68 (0.44–1.06) |

Magnets, window falls, drowning and wandering are too rare in these groups to compare.

**This changes the reading of the earlier table.** Against peers with no condition recorded,
autism-mention cases showed 4–8 times more swallowing, poisoning, batteries and seizures. Against
other conditions recorded the same way, **most of that excess disappears.** Swallowed objects,
poisoning, batteries and seizures are about as common in ADHD, Down syndrome, CP and
developmental-delay notes. So the big earlier ratios mostly describe *what a condition-mention
note looks like*, not something specific to autism.

**What survives:**
- head-banging, about 2 times the other conditions (ADHD is close behind);
- fewer fractures.

The comparison groups are small, so the confidence intervals are wide. The prevention messages
about batteries, poisons and swallowed objects still stand, but as messages for children with
neurodevelopmental conditions generally, not for autism specifically.
