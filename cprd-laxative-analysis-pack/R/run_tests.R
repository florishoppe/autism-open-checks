# Check that laxative_analysis.R recovers known effects in simulated data.
# Run from the analysis-pack folder:  Rscript R/run_tests.R

suppressPackageStartupMessages(library(data.table))
here <- function(f) file.path("R", f)
source(here("simulate_cprd_like.R"))
source(here("laxative_analysis.R"))

row <- function(res, a, t) res[res$analysis == a & res$term == t]

check <- function(name, ok, detail) {
  cat(sprintf("%-4s %s\n      %s\n", if (ok) "PASS" else "FAIL", name, detail))
  invisible(ok)
}

results <- list()
fmt <- function(r) sprintf("RR %.2f (%.2f-%.2f), %s people, %s events",
                           r$estimate, r$lo, r$hi, r$people, r$events)

# ---- Scenario A: true 30% fall with continued treatment, none otherwise ----
dA <- simulate_cprd_like(rr_persistent = 0.70, rr_single = 1.00, seed = 11)
rA <- run_analysis(dA)$results
a1 <- row(rA, "Primary (non-acute index) | persistent", "early")
a2 <- row(rA, "Primary (non-acute index) | single-fill", "early")
a3 <- row(rA, "Primary (non-acute index) | persistent vs single (RRR)", "early_vs_ref")
a4 <- row(rA, "Primary (non-acute index) | emollient", "early")
results$A <- c(
  check("A1 persistent RR covers the true 0.70", a1$lo <= 0.70 && a1$hi >= 0.70, fmt(a1)),
  check("A2 single-fill RR covers the true 1.00", a2$lo <= 1 && a2$hi >= 1, fmt(a2)),
  check("A3 RRR persistent vs single covers 0.70 and excludes 1", a3$lo <= 0.70 &&
          a3$hi >= 0.70 && a3$hi < 1, fmt(a3)),
  check("A4 emollient negative control covers 1.00", a4$lo <= 1 && a4$hi >= 1, fmt(a4))
)

# ---- Scenario B: no effect anywhere, but 30% of starts are crisis-prompted ----
dB <- simulate_cprd_like(rr_persistent = 1.00, rr_single = 1.00, p_crisis = 0.30,
                         crisis_rr = 2.5, seed = 22)
rB <- run_analysis(dB)$results
b1 <- row(rB, "Primary (non-acute index) | persistent vs single (RRR)", "early_vs_ref")
b2 <- row(rB, "Primary (non-acute index) | persistent", "early")
b3 <- row(rB, "Naive: acute index included (should be biased) | persistent", "early")
results$B <- c(
  check("B1 null: RRR covers 1.00", b1$lo <= 1 && b1$hi >= 1, fmt(b1)),
  check("B2 null: persistent RR covers 1.00 after the non-acute filter",
        b2$lo <= 1 && b2$hi >= 1, fmt(b2)),
  check("B3 naive analysis (acute starts kept) shows a spurious fall",
        b3$hi < 1, fmt(b3))
)

# ---- Scenario C: subgroups and disclosure control run without error ----
outC <- run_analysis(simulate_cprd_like(n = 8000, rr_persistent = 0.8, seed = 33))
supp <- suppress_small(outC$feasibility)
results$C <- c(
  check("C1 all subgroup analyses returned rows",
        all(c("Autistic | persistent", "Under 18 | persistent",
              "Not on antipsychotic | persistent") %in% outC$results$analysis), ""),
  check("C2 small cells suppressed in the feasibility table",
        !any(suppressWarnings(as.integer(supp$N)) %in% 1:9),
        paste(sum(grepl("^<", supp$N)), "cells suppressed"))
)

cat("\nPrimary results, scenario A (true RR 0.70 in persistent users):\n")
print(rA[grepl("^Primary", analysis) & term %in% c("early", "early_vs_ref"),
         .(analysis, term, estimate = round(estimate, 2), lo = round(lo, 2),
           hi = round(hi, 2), people, events)])

all_ok <- all(unlist(results))
cat(sprintf("\n%s: %d of %d checks passed\n", if (all_ok) "ALL PASSED" else "FAILURES",
            sum(unlist(results)), length(unlist(results))))
quit(status = if (all_ok) 0 else 1)
