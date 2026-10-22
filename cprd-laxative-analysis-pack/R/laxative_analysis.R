# Within-person laxative-start analysis of recorded challenging behaviour.
#
# Implements ANALYSIS-PLAN.md. Input: three analysis-ready tables (see README):
#   patient       patid, dob, sex, autism (0/1), regstart, regend
#   events        patid, eventdate, type  in {cb, ed, injury, psychotropic_up}
#   prescriptions patid, issuedate, class in {laxative, emollient, antipsychotic,
#                                             opioid, anticholinergic}
# The study team maps CPRD medcodes/prodcodes to these labels with their own,
# clinically reviewed code lists. All outputs are aggregate and pass through
# suppress_small() before leaving the analysis environment.
#
# Status: written with AI assistance and tested only on simulated data
# (run_tests.R). It needs review by the study's analyst before any real use.

suppressPackageStartupMessages({
  library(data.table)
  library(gnm)
})

WINDOWS <- data.table(
  window = c("baseline", "early", "later"),
  from   = c(-210L, 1L, 91L),
  to     = c(-31L, 90L, 180L)
)
WINDOWS[, days := to - from + 1L]

ACUTE_TYPES <- c("cb", "ed", "injury", "psychotropic_up")
CASCADE_CLASSES <- c("antipsychotic", "opioid", "anticholinergic")

# ---------------------------------------------------------------------------
# 1. Index events
# ---------------------------------------------------------------------------

first_start <- function(rx, patient, cls, lookback = 365L, followup = 180L) {
  # First issue of `cls` with >= lookback days of prior registration, no prior issue
  # of the same class in the lookback, and full follow-up to day `followup`.
  x <- rx[class == cls][order(patid, issuedate)]
  x <- x[, .SD[1], by = patid]
  x <- merge(x, patient, by = "patid")
  x <- x[issuedate - regstart >= lookback & regend - issuedate >= followup &
           issuedate - regstart >= -WINDOWS[window == "baseline", from]]
  x[, .(patid, index = issuedate)]
}

classify_laxative <- function(idx, rx) {
  # persistent: >= 2 further laxative issues in days 1-90
  # single:     no further laxative issue in days 1-180
  # otherwise:  intermediate (excluded from the primary contrast)
  f <- merge(idx, rx[class == "laxative", .(patid, issuedate)], by = "patid")
  f[, rel := as.integer(issuedate - index)]
  s <- f[, .(n90 = sum(rel >= 1 & rel <= 90), n180 = sum(rel >= 1 & rel <= 180)),
         by = patid]
  out <- merge(idx, s, by = "patid", all.x = TRUE)
  out[, group := fifelse(n90 >= 2, "persistent",
                 fifelse(n180 == 0, "single", "intermediate"))]
  out[, .(patid, index, group)]
}

flag_acute <- function(idx, events, exclusion_days = 30L) {
  # TRUE if any acute contact in [-exclusion_days, 0] around the index date.
  e <- merge(idx[, .(patid, index)], events[type %in% ACUTE_TYPES], by = "patid")
  e <- e[eventdate - index >= -exclusion_days & eventdate - index <= 0]
  idx[, acute := patid %in% e$patid]
  idx
}

flag_cascade <- function(idx, rx, days = 90L) {
  # TRUE if a constipating drug class was issued within +/- days of index
  e <- merge(idx[, .(patid, index)], rx[class %in% CASCADE_CLASSES], by = "patid")
  e <- e[abs(as.integer(issuedate - index)) <= days]
  idx[, cascade := patid %in% e$patid]
  idx
}

flag_antipsychotic_at_index <- function(idx, rx, days = 90L) {
  e <- merge(idx[, .(patid, index)], rx[class == "antipsychotic"], by = "patid")
  e <- e[index - issuedate >= 0 & index - issuedate <= days]
  idx[, on_ap := patid %in% e$patid]
  idx
}

build_cohort <- function(d, exclusion_days = 30L) {
  lax <- first_start(d$prescriptions, d$patient, "laxative")
  lax <- classify_laxative(lax, d$prescriptions)
  emo <- first_start(d$prescriptions, d$patient, "emollient")
  # emollient controls: no laxative issue from 365 days before to 180 after index
  le <- merge(emo, d$prescriptions[class == "laxative", .(patid, issuedate)], by = "patid")
  bad <- le[issuedate - index >= -365 & issuedate - index <= 180, unique(patid)]
  # each person contributes one index only: laxative starters are never emollient controls
  emo <- emo[!patid %in% bad & !patid %in% lax$patid][, group := "emollient"]
  idx <- rbind(lax, emo)
  idx <- flag_acute(idx, d$events, exclusion_days)
  idx <- flag_cascade(idx, d$prescriptions)
  idx <- flag_antipsychotic_at_index(idx, d$prescriptions)
  idx <- merge(idx, d$patient[, .(patid, dob, autism)], by = "patid")
  idx[, age_at_index := as.numeric(index - dob) / 365.25]
  idx[, child := age_at_index < 18]
  idx[]
}

# ---------------------------------------------------------------------------
# 2. Window counts (person x window)
# ---------------------------------------------------------------------------

window_counts <- function(idx, events, outcome = "cb") {
  e <- merge(idx[, .(patid, index)], events[type == outcome, .(patid, eventdate)],
             by = "patid")
  e[, rel := as.integer(eventdate - index)]
  grid <- CJ(patid = idx$patid, window = WINDOWS$window)
  grid <- merge(grid, WINDOWS, by = "window")
  hits <- e[WINDOWS, on = .(rel >= from, rel <= to), nomatch = 0L,
            .(patid, window = i.window)][, .(count = .N), by = .(patid, window)]
  out <- merge(grid, hits, by = c("patid", "window"), all.x = TRUE)
  out[is.na(count), count := 0L]
  out <- merge(out, idx[, .(patid, group)], by = "patid")
  out[, window := factor(window, levels = WINDOWS$window)]
  out[]
}

# ---------------------------------------------------------------------------
# 3. Models
# ---------------------------------------------------------------------------

fit_within_person <- function(wc, groups) {
  # Conditional (person-stratified) quasi-Poisson rate ratios, window vs baseline.
  # People with no events in any window carry no information and are dropped.
  x <- wc[group %in% groups]
  inf <- x[, .(tot = sum(count)), by = patid][tot > 0, patid]
  x <- x[patid %in% inf]
  if (uniqueN(x$patid) < 2) return(NULL)
  # Explicit indicators: R's default coding of window:group without a group main
  # effect creates columns that the person strata alias unpredictably.
  x[, `:=`(windowearly = as.numeric(window == "early"),
           windowlater = as.numeric(window == "later"))]
  if (length(groups) == 1) {
    m <- gnm(count ~ windowearly + windowlater + offset(log(days)),
             eliminate = factor(patid), family = quasipoisson, data = x, verbose = FALSE)
  } else {
    # Interaction terms compare groups[2] with the reference groups[1]
    x[, g2 := as.numeric(group == groups[2])]
    x[, `:=`(windowearly_vs_ref = windowearly * g2,
             windowlater_vs_ref = windowlater * g2)]
    m <- gnm(count ~ windowearly + windowlater + windowearly_vs_ref +
               windowlater_vs_ref + offset(log(days)),
             eliminate = factor(patid), family = quasipoisson, data = x, verbose = FALSE)
  }
  list(model = m, n_people = uniqueN(x$patid), n_events = sum(x$count))
}

tidy_rr <- function(fit, label) {
  if (is.null(fit)) return(data.table(analysis = label, term = NA_character_,
                                      estimate = NA_real_, lo = NA_real_, hi = NA_real_))
  cf <- summary(fit$model)$coefficients
  cf <- cf[grepl("^window", rownames(cf)), , drop = FALSE]
  data.table(analysis = label, term = rownames(cf),
             estimate = exp(cf[, 1]),
             lo = exp(cf[, 1] - 1.96 * cf[, 2]),
             hi = exp(cf[, 1] + 1.96 * cf[, 2]),
             people = fit$n_people, events = fit$n_events)
}

run_contrasts <- function(wc, label) {
  rbind(
    tidy_rr(fit_within_person(wc, "persistent"), paste(label, "| persistent")),
    tidy_rr(fit_within_person(wc, "single"), paste(label, "| single-fill")),
    tidy_rr(fit_within_person(wc, "emollient"), paste(label, "| emollient")),
    # ratio of rate ratios: terms early_vs_ref / later_vs_ref, reference = first group
    tidy_rr(fit_within_person(wc, c("single", "persistent")),
            paste(label, "| persistent vs single (RRR)")),
    tidy_rr(fit_within_person(wc, c("emollient", "persistent")),
            paste(label, "| persistent vs emollient (RRR)")),
    fill = TRUE
  )
}

# ---------------------------------------------------------------------------
# 4. Full analysis
# ---------------------------------------------------------------------------

run_analysis <- function(d, outcome = "cb") {
  idx <- build_cohort(d)
  idx60 <- build_cohort(d, exclusion_days = 60L)

  feas <- idx[, .N, by = .(group, acute, autism, child)][order(group, acute)]

  main <- idx[acute == FALSE & group != "intermediate"]
  wc <- window_counts(main, d$events, outcome)
  res <- rbind(
    run_contrasts(wc, "Primary (non-acute index)"),
    run_contrasts(wc[patid %in% main[autism == 1, patid]], "Autistic"),
    run_contrasts(wc[patid %in% main[child == TRUE, patid]], "Under 18"),
    run_contrasts(wc[patid %in% main[on_ap == FALSE, patid]], "Not on antipsychotic"),
    run_contrasts(wc[patid %in% main[cascade == FALSE, patid]], "No cascade drug +/-90d"),
    run_contrasts(window_counts(idx60[acute == FALSE & group != "intermediate"],
                                d$events, outcome), "60-day acute exclusion"),
    run_contrasts(window_counts(idx[group != "intermediate"], d$events, outcome),
                  "Naive: acute index included (should be biased)"),
    fill = TRUE
  )
  res[, term := sub("^window", "", term)]
  list(feasibility = feas, results = res)
}

# ---------------------------------------------------------------------------
# 5. Disclosure control
# ---------------------------------------------------------------------------

suppress_small <- function(tab, min_cell = 10L, count_cols = c("N", "people", "events")) {
  # Replace counts 1..(min_cell-1) with "<min_cell". Follow the CPRD RDG rules that
  # apply to the study; min_cell is a parameter, not a recommendation.
  t <- copy(tab)
  for (cc in intersect(count_cols, names(t))) {
    v <- t[[cc]]
    t[[cc]] <- ifelse(!is.na(v) & v > 0 & v < min_cell, paste0("<", min_cell),
                      as.character(v))
  }
  t
}
