# Open checks on autism, health and safety

Small, reproducible analyses of public data on questions that matter to autistic people and their
families, shared so that researchers can check, reuse or extend them.

**Why this exists.** I'm a family member of an autistic child, not a researcher. This is an
experiment in using today's AI tools to be of some real use in this field. The idea is to look for
under-explored questions, run the cheap first checks that busy researchers rarely have time for, and
hand over the results openly. If a check turns up something worth pursuing, the hope is that people
with the right expertise and data take it further.

> **Please read first.** These analyses were done by a family member of an autistic child, not a
> researcher or clinician, with substantial help from an AI assistant (Anthropic's Claude). That
> assistant wrote much of the code and text. Citations were checked against PubMed, Europe PMC and
> ClinicalTrials.gov, and the code was tested where possible. All of it is still a starting point,
> not validated research. **Check everything independently before relying on it.** Nothing here is
> medical advice.

## Contents

| Folder | Question | Status |
|---|---|---|
| [`neiss-autism-injuries/`](neiss-autism-injuries/FEASIBILITY.md) | What injuries bring people with autism mentioned in their notes to US emergency departments? (NEISS narratives, 2013–2024) | Feasibility and descriptive comparison done. Coding by a single AI coder; needs a human second coder |
| [`seizure-alarm-stereotypy/`](seizure-alarm-stereotypy/RESULTS.md) | Does OpenSeizureDetector's default algorithm false-alarm on rocking and hand-flapping? | Run on public data (6 participants). Mostly no; flapping somewhat more |
| [`cprd-laxative-analysis-pack/`](cprd-laxative-analysis-pack/README.md) | Is starting a laxative followed by fewer recorded challenging-behaviour events? A within-person design for UK primary-care records | Code and plan only, tested on simulated data. Not run on real data |

## Headline findings

- **NEISS:**
  - 2,441 ED injury narratives mention autism.
  - A quarter of the hand-read cases were injuries during self-injury or distress, which the
    product coding records as walls, windows or floors.
  - Against age-, sex- and year-matched cases, the autism-mention case mix holds far more:
    - head-banging (12.6×);
    - seizures mentioned (8.4×);
    - batteries (6.5×);
    - poisoning (5.6×);
    - swallowed objects (4.5×);
  - and far fewer sports injuries (0.05×).
  - These are proportion ratios shaped by what staff choose to record, not risks.
- **Seizure alarms:**
  - OSD's default algorithm flagged rocking and flapping about as often as ordinary activity:
    1.4 against 1.1 alarm onsets per hour.
  - Rocking (about 1 Hz) falls mostly below its 3–8 Hz band.

## Data sources

- **NEISS:** US Consumer Product Safety Commission, public domain. The 2013–2017 data come via the
  [`neiss` R package](https://github.com/hadley/neiss). The 2018–2024 data come from the CPSC annual
  files. This repository includes only the extracted autism-mention narratives and the coded samples.
- **Stereotypy accelerometer data:** Goodwin, Albinali et al.
  ([Bitbucket](https://bitbucket.org/mhealthresearchgroup/stereotypypublicdataset-sourcecodes)).
  Not redistributed here; the script reads the original files.
- **OpenSeizureDetector:** algorithm re-implemented from
  [OpenSeizureDetector/Android_Pebble_SD](https://github.com/OpenSeizureDetector/Android_Pebble_SD).

## Reproducing

R 4.x with `data.table` (and `gnm` for the laxative pack), and Python 3. Each folder's script
header gives its usage.

## Licence

Code: MIT (see `LICENSE`). Text and derived tables: CC BY 4.0. Underlying datasets keep their own
terms.
