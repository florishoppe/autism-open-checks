# Repeat the primary contrast over many simulated datasets and report how often
# the 95% interval covers the true value (should be close to 95%).
# Run from the analysis-pack folder:  Rscript R/coverage_check.R [n_reps]
suppressPackageStartupMessages(library(data.table))
source(file.path("R", "simulate_cprd_like.R"))
source(file.path("R", "laxative_analysis.R"))
reps <- as.integer(commandArgs(TRUE)[1]); if (is.na(reps)) reps <- 30L

one <- function(seed, rr) {
  d <- simulate_cprd_like(n = 25000, rr_persistent = rr, p_crisis = 0.3, crisis_rr = 2.5,
                          seed = seed)
  idx <- build_cohort(d)
  wc <- window_counts(idx[acute == FALSE & group %in% c("single", "persistent")], d$events)
  r <- tidy_rr(fit_within_person(wc, c("single", "persistent")), "x")
  r[term == "windowearly_vs_ref", .(seed, true = rr, est = estimate, lo, hi)]
}
out <- rbindlist(c(lapply(seq_len(reps), one, rr = 0.70),
                   lapply(seq_len(reps) + 1000L, one, rr = 1.00)))
out[, covered := lo <= true & hi >= true]
out[, rejects_null := hi < 1 | lo > 1]
print(out[, .(reps = .N, mean_estimate = round(exp(mean(log(est))), 3),
              coverage_95 = round(mean(covered), 2), share_rejecting_null = round(mean(rejects_null), 2)),
          by = true])
