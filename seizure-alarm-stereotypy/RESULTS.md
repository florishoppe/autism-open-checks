# Does OpenSeizureDetector's default algorithm alarm on rocking and hand-flapping?

**Date:** 2026-10-22. **Answer, in this data: mostly no.** Rocking and flapping set off the
OpenSeizureDetector (OSD) algorithm about as often as ordinary activity in the same sessions.
Hand-flapping did so somewhat more. Its 15-second persistence rule suppresses almost all of it.

## What was done

- **Data.** The public stereotypy dataset of Goodwin, Albinali and colleagues
  (bitbucket.org/mhealthresearchgroup/stereotypypublicdataset-sourcecodes), cloned 2026-10-22.
  - Six autistic participants, 25 sessions, recorded in a lab and a classroom in 2008–2011.
  - Accelerometers on both wrists: MITes in Study 1 and Wockets in Study 2.
  - Rocking, flapping and both together were labelled from video by Annotator 1.
- **Algorithm.** OSD's default seizure algorithm, re-implemented line by line from the
  OpenSeizureDetector Android source (`alg/SdAlgOsd.java`, `alg/SeizureDetector.java`; defaults
  from `res/xml/sd_prefs_*.xml`):
  - 5-second windows at 25 Hz;
  - FFT of acceleration magnitude in milli-g;
  - "positive" when power in the 3–8 Hz band is above 100 and its ratio to total power (up to
    12 Hz) is above 5.7;
  - escalation: WARNING after 2 positive windows in a row, **ALARM after 3 (15 s)**.
  - OSD's optional "Flap" detector (2–4 Hz, off by default) was also run with its defaults.
- **Processing.** Raw counts were converted to g using each recording's own gravity range
  (median magnitude came out at 0.9–1.0 g, as expected). Then resampled to 25 Hz, cut into 5-second
  windows, and each window labelled as stereotypy (≥2.5 s of annotated rocking or flapping) or
  other. Only windows inside the annotators' "Good Data" spans were kept.

Script: `osd_on_stereotypy.R`. Per-window output: `windows.tsv`.

## Results

| Windows | Hours | OSD positive (single window) | Time in ALARM | ALARM onsets per hour | Flap detector positive |
|---|---|---|---|---|---|
| Stereotypy | 5.7 | 3.2% | 0.2% | 1.4 | 5.9% |
| Other activity, same sessions | 13.2 | 3.9% | 0.2% | 1.1 | 5.1% |

| Stereotypy type | Hours | OSD positive | ALARM onsets per hour |
|---|---|---|---|
| Rocking | 3.8 | 2.4% | 0.8 |
| Flapping | 1.2 | 5.5% | 3.4 |
| Flap + rock | 0.5 | 4.5% | 1.9 |

**Per participant**, stereotypy windows: OSD-positive rates ranged from 0.7% to 6.7%, and ALARM
onsets from 0 to 3.3 per hour of stereotypy. No participant's stereotypy produced sustained alarms.

**Calibration sensitivity.** The power threshold depends on units, and the gravity-range
calibration is approximate. The check rescaled units by 0.5–1.5×. Stereotypy windows ranged from
3.6% to 6.5% positive, and other windows from 3.8% to 5.0%. These figures use the unrounded ratio,
so they run slightly higher than the table above. Stereotypy never stands out by more than a
factor of about 1.3.

## Reading it

- **Rocking sits mostly below OSD's 3–8 Hz band.** Body rocking is roughly 1 Hz, so the algorithm
  largely ignores it.
- **Hand-flapping is faster and lands in the band more often**, about 2.4× the alarm-onset rate
  of ordinary activity. But flapping bouts are usually shorter than the 15 s needed for an ALARM.
- **The bigger practical point is false alarms during any awake activity**, about one alarm onset
  per hour in these classroom sessions, stereotypy or not. OSD is designed and mostly used for
  sleep, where this matters less.
- **The hypothesis that stereotypy makes wrist alarms unusable is not supported for this
  algorithm.** That's a useful negative result. It can reassure families considering an
  open-source alarm for an autistic child who rocks.

## Limits

- **Six participants**, short sessions (about 19 hours in total), and an awake lab or classroom
  rather than the night.
- **Old sensors**, with approximate calibration. A modern watch's sampling and filtering differ.
- **One open algorithm.** The commercial devices (Empatica EpiMonitor, NightWatch and others) use
  closed algorithms and other signals, such as heart rate and electrodermal activity, and were not
  tested. OSD's newer machine-learning option (`SdAlgMl`) was not tested either.
- **Night-time rocking and head-banging** in sleep may differ from daytime stereotypy, and none
  was recorded here.
- **Not done:** the Open Seizure Database comparison. Downloading it needs an IEEE DataPort
  account, so it was not attempted.

## What would make this worth sending to the OSD developers

- Rerun with OSD's ML algorithm, and on night-time stereotypy recordings if any exist.
- Ask OSD's maintainers whether their labelled false alarms include rocking or flapping users.
- These results were shared with the OSD project on GitHub Discussions (OpenSeizureDetector discussion #320).
