# Simulate a small CPRD-like extract for testing laxative_analysis.R.
#
# The simulated tables have the same shape as the analysis-ready inputs that
# laxative_analysis.R expects (see README). They are NOT realistic in their rates;
# they exist only so the analysis can be checked against known true effects.

suppressPackageStartupMessages(library(data.table))

simulate_cprd_like <- function(
  n = 40000,
  base_rate = 0.30,          # challenging-behaviour records per person-year (cohort mean)
  frailty_shape = 1.5,       # gamma frailty; smaller = more between-person variation
  autism_prop = 0.18,
  autism_rr = 1.3,
  p_laxative = 0.25,         # share of people with a first laxative start
  p_emollient = 0.15,        # share (of non-laxative people) with a first emollient start
  p_crisis = 0.30,           # share of laxative starts prompted by a behaviour crisis
  crisis_rr = 2.0,           # rate multiplier during the 120 days before a crisis-prompted start
  p_persistent = 0.50, p_single = 0.35,  # rest are "intermediate" (excluded)
  rr_persistent = 1.0,       # TRUE effect of continued treatment, days 1-180
  rr_single = 1.0,           # TRUE effect in single-fill users, days 1-180
  p_antipsychotic = 0.10,
  seed = 1
) {
  set.seed(seed)
  origin <- as.Date("2009-01-01"); study_end <- as.Date("2019-12-31")

  pat <- data.table(patid = seq_len(n))
  pat[, regstart := origin + floor(runif(.N, 0, 3 * 365))]
  pat[, regend := pmin(study_end, regstart + floor(runif(.N, 3 * 365, 9 * 365)))]
  child <- runif(n) < 0.20
  age_at_start <- ifelse(child, runif(n, 3, 17), runif(n, 18, 80))
  pat[, dob := regstart - floor(age_at_start * 365.25)]
  pat[, sex := sample(c("F", "M"), .N, replace = TRUE, prob = c(0.42, 0.58))]
  pat[, autism := as.integer(runif(.N) < autism_prop)]
  pat[, u := rgamma(.N, shape = frailty_shape, rate = frailty_shape)]
  pat[, rate_day := base_rate / 365.25 * u * ifelse(autism == 1, autism_rr, 1)]

  # --- who starts a laxative or an emollient, and when -----------------------
  pat[, lax := runif(.N) < p_laxative]
  pat[, emol := !lax & runif(.N) < p_emollient]
  span <- as.integer(pat$regend - pat$regstart)
  ok <- span > 400 + 200
  pat[!ok, `:=`(lax = FALSE, emol = FALSE)]
  pat[, index := as.Date(NA)]
  pat[lax | emol, index := regstart + 400 +
        floor(runif(.N) * (as.integer(regend - regstart) - 600))]
  pat[, crisis := lax & runif(.N) < p_crisis]
  g <- runif(n)
  pat[, group := fifelse(!lax, NA_character_,
                 fifelse(g < p_persistent, "persistent",
                 fifelse(g < p_persistent + p_single, "single", "intermediate")))]

  # --- piecewise-constant challenging-behaviour rate ------------------------
  # Segments: [regstart, index-120), [index-120, index), [index, index+180], (index+180, regend]
  seg <- pat[, .(patid, regstart, regend, index, rate_day, crisis, group)]
  seg <- seg[, {
    if (is.na(index)) {
      list(s = regstart, e = regend, mult = 1)
    } else {
      post <- if (is.na(group)) 1 else switch(group, persistent = rr_persistent,
                                              single = rr_single, 1)
      list(s = c(regstart, index - 120, index + 1, index + 181),
           e = c(index - 121, index, index + 180, regend),
           mult = c(1, if (crisis) crisis_rr else 1, post, 1))
    }
  }, by = .(patid, rate_day)]
  seg <- seg[e >= s]
  seg[, n_ev := rpois(.N, rate_day * mult * (as.integer(e - s) + 1))]
  ev <- seg[n_ev > 0, .(eventdate = s + floor(runif(n_ev) * (as.integer(e - s) + 1))),
            by = .(patid, s, e, n_ev)][, .(patid, eventdate, type = "cb")]

  # Crisis-prompted starts: an acute contact and a behaviour record just before index
  cr <- pat[crisis == TRUE]
  ev <- rbind(ev,
    cr[, .(patid, eventdate = index - sample(1:14, .N, replace = TRUE), type = "ed")],
    cr[, .(patid, eventdate = index - sample(1:14, .N, replace = TRUE), type = "cb")])

  # Background emergency / injury contacts
  bg <- pat[, .(n_ed = rpois(1, 0.05 * as.integer(regend - regstart) / 365.25)),
            by = .(patid, regstart, regend)]
  ev <- rbind(ev, bg[n_ed > 0, .(eventdate = regstart + floor(runif(n_ed) *
            as.integer(regend - regstart)), type = "ed"), by = patid])

  # --- prescriptions ---------------------------------------------------------
  rx <- rbind(
    pat[lax == TRUE, .(patid, issuedate = index, class = "laxative")],
    pat[group == "persistent", .(issuedate = index + c(28, 56, 84), class = "laxative"),
        by = patid],
    pat[group == "intermediate", .(patid, issuedate = index + 120, class = "laxative")],
    pat[emol == TRUE, .(patid, issuedate = index, class = "emollient")]
  )
  ap <- pat[!is.na(index) & runif(.N) < p_antipsychotic]
  rx <- rbind(rx, ap[, .(patid, issuedate = index - sample(10:80, .N, replace = TRUE),
                         class = "antipsychotic")])

  list(
    patient = pat[, .(patid, dob, sex, autism, regstart, regend)],
    events = ev[order(patid, eventdate)],
    prescriptions = rx[order(patid, issuedate)],
    truth = pat[, .(patid, lax, emol, crisis, group, index)]
  )
}
