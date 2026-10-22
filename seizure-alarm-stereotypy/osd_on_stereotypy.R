# Run OpenSeizureDetector's OSD and Flap algorithms (default settings) over wrist accelerometer
# recordings of autistic participants with video-annotated rocking and hand-flapping.
#
# Data: Goodwin/Albinali stereotypy dataset
#   (bitbucket.org/mhealthresearchgroup/stereotypypublicdataset-sourcecodes; Study1 = MITes,
#   Study2 = Wockets; both wrists).
# Algorithm: re-implemented from OpenSeizureDetector/Android_Pebble_SD source (master,
#   cloned 2026-10-22): alg/SdAlgOsd.java, alg/SdAlgFlap.java, alg/SeizureDetector.java,
#   res/xml/sd_prefs_*.xml defaults.
#
# Usage: Rscript osd_on_stereotypy.R <data-dir> <out-dir>

suppressPackageStartupMessages(library(data.table))
args <- commandArgs(TRUE); DATA <- args[1]; OUT <- args[2]

FS <- 25; NS <- 125                     # 25 Hz, 5-s windows of 125 samples (SdDataSource)
OSD <- list(thresh = 100, ratio = 57, fmin = 3, fmax = 8)       # sd_prefs_osd.xml
FLAP <- list(thresh = 5000, ratio = 90, fmin = 2, fmax = 4)     # sd_prefs_flap.xml
FCUT <- 12
WARN_T <- 5; ALARM_T <- 10; PERIOD <- 5                          # sd_prefs_voting.xml

bin <- function(f) as.integer(NS * f / FS)                     # freq2FftBin

osd_window <- function(x) {
  # x: 125 magnitudes in milli-g. Mirrors SdAlgOsd.processSdData / SdAlgFlap.processSdData.
  X <- fft(x)                                     # same unnormalised DFT as JTransforms
  mag <- Mod(X)^2
  idx <- 0:(NS - 1)                               # bin index
  nc <- bin(FCUT)
  keep <- idx >= 1 & idx < NS / 2 & idx <= nc
  spec <- sum(mag[keep]) / NS / 2
  roi <- function(p) { i <- idx >= bin(p$fmin) & idx < bin(p$fmax); sum(mag[i]) / (bin(p$fmax) - bin(p$fmin)) }
  r_o <- roi(OSD)
  osd_spec <- as.integer(spec / 1000); osd_roi <- as.integer(r_o / 1000)
  if (osd_spec == 0) osd_spec <- 1L
  osd_hit <- osd_roi > OSD$thresh && (10 * osd_roi %/% osd_spec) > OSD$ratio
  r_f <- roi(FLAP) / 1000; s_f <- spec / 1000
  flap_hit <- r_f > FLAP$thresh && (10 * r_f / s_f) > FLAP$ratio
  c(osd_hit = osd_hit, flap_hit = flap_hit, osd_roi = osd_roi, osd_ratio = 10 * osd_roi / osd_spec)
}

# --- calibration: fit per-axis offset and scale so still periods have magnitude 1 g ----------
calibrate <- function(a) {
  # Gravity-range calibration. The wrist takes many orientations over a session, so the 1st and
  # 99th percentiles of 1-s mean acceleration on each axis approximate -1 g and +1 g.
  # Offset = midpoint, scale = half-range (counts per g). (A sphere fit on still periods was
  # tried first and was degenerate: the wrist rests in too few orientations.)
  a[, blk := t %/% 1000]
  s <- a[, .(mx = mean(x), my = mean(y), mz = mean(z), n = .N), by = blk][n > 10]
  q <- function(v) quantile(v, c(0.01, 0.99))
  qx <- q(s$mx); qy <- q(s$my); qz <- q(s$mz)
  par <- c(mean(qx), mean(qy), mean(qz), diff(qx) / 2, diff(qy) / 2, diff(qz) / 2)
  m <- sqrt(((s$mx - par[1]) / par[4])^2 + ((s$my - par[2]) / par[5])^2 + ((s$mz - par[3]) / par[6])^2)
  list(par = par, median_g = median(m), resid = sd(m), n_still = nrow(s))
}

read_ann <- function(f) {
  x <- readLines(f, warn = FALSE)
  lab <- sub(".*<LABEL>(.*)</LABEL>.*", "\\1", grep("<LABEL>", x, value = TRUE))
  st <- sub(".*<START_DT>(.*)</START_DT>.*", "\\1", grep("<START_DT>", x, value = TRUE))
  en <- sub(".*<STOP_DT>(.*)</STOP_DT>.*", "\\1", grep("<STOP_DT>", x, value = TRUE))
  data.table(label = lab, start = as.POSIXct(st, format = "%Y-%m-%d %H:%M:%OS", tz = "UTC"),
             stop = as.POSIXct(en, format = "%Y-%m-%d %H:%M:%OS", tz = "UTC"))
}

run_session <- function(dir, sensor_file) {
  a <- fread(file.path(dir, sensor_file), header = FALSE, col.names = c("t", "x", "y", "z"), integer64 = "double")
  a <- a[order(t)][!duplicated(t)]
  cal <- calibrate(copy(a)); p <- cal$par
  a[, mg := 1000 * sqrt(((x - p[1]) / p[4])^2 + ((y - p[2]) / p[5])^2 + ((z - p[3]) / p[6])^2)]
  # resample to 25 Hz by averaging within each 40-ms slot (simple anti-alias), then fill gaps
  a[, slot := t %/% 40]
  r <- a[, .(mg = mean(mg)), by = slot]
  full <- data.table(slot = seq(min(r$slot), max(r$slot)))
  r <- r[full, on = "slot"]
  r[, gap := is.na(mg)]
  r[, mg := approx(slot[!gap], mg[!gap], xout = slot, rule = 2)$y]
  r[, win := (slot - min(slot)) %/% NS]
  w <- r[, if (.N == NS && mean(gap) < 0.2) as.list(osd_window(mg)) , by = win]
  w[, t_start := (min(r$slot) + win * NS) * 40 / 1000]           # seconds since epoch
  ann <- read_ann(file.path(dir, "Annotator1Stereotypy.annotation.xml"))
  ann[, `:=`(s = as.numeric(start), e = as.numeric(stop))]
  # The annotation clock and sensor clock are both local wall time in the published data;
  # check alignment via the "Good Data" span.
  good <- ann[label == "Good Data"]
  stereo <- ann[label %in% c("Rock", "Flap", "Flap-Rock")]
  ov <- function(ws, L) { we <- ws + 5; sum(pmax(0, pmin(we, L$e) - pmax(ws, L$s))) }
  w[, in_good := sapply(t_start, function(s0) ov(s0, good)) >= 2.5]
  w[, stereo_sec := sapply(t_start, function(s0) ov(s0, stereo))]
  w[, lab := fifelse(stereo_sec >= 2.5, "stereotypy", fifelse(stereo_sec == 0, "other", "partial"))]
  for (k in c("Rock", "Flap", "Flap-Rock")) {
    Lk <- ann[label == k]; w[, (k) := sapply(t_start, function(s0) ov(s0, Lk)) >= 2.5]
  }
  # alarm escalation (SeizureDetector.java): +5 s per positive window; WARNING > 5 s, ALARM > 10 s
  esc <- function(hit) { t <- 0; st <- character(length(hit))
    for (i in seq_along(hit)) {
      if (isTRUE(hit[i])) { t <- t + PERIOD; st[i] <- if (t > ALARM_T) "ALARM" else if (t > WARN_T) "WARNING" else "OK" }
      else if (t > ALARM_T) { st[i] <- "WARNING"; t <- WARN_T + 1 } else { st[i] <- "OK"; t <- 0 } }
    st }
  w[, osd_state := esc(osd_hit == 1)]
  w[, flap_state := esc(flap_hit == 1)]
  list(w = w[in_good == TRUE], cal = cal, n_ann = nrow(stereo))
}

sessions <- list()
for (study in c("Study1", "Study2")) {
  for (d in list.dirs(file.path(DATA, study), recursive = FALSE)) {
    fs <- list.files(d, pattern = "(Left|Right)-[Ww]rist")
    for (sf in fs) {
      res <- tryCatch(run_session(d, sf), error = function(e) { message(d, " ", sf, ": ", conditionMessage(e)); NULL })
      if (is.null(res) || nrow(res$w) == 0) next
      res$w[, `:=`(study = study, session = basename(d), sensor = sf,
                   participant = sub("^(URI-)?0*([0-9]+).*", "\\2", basename(d)))]
      sessions[[length(sessions) + 1]] <- res$w
      cat(sprintf("%s %s %-44s win %4d stereo %4d | scale %5.0f %5.0f %5.0f counts/g | median |a| %.2f g\n",
                  study, basename(d), sf, nrow(res$w), sum(res$w$lab == "stereotypy"),
                  res$cal$par[4], res$cal$par[5], res$cal$par[6], res$cal$median_g))
    }
  }
}
W <- rbindlist(sessions, fill = TRUE)
fwrite(W, file.path(OUT, "windows.tsv"), sep = "\t")

summ <- function(x, by) x[, .(windows = .N, hours = round(.N * 5 / 3600, 2),
  osd_positive_pct = round(100 * mean(osd_hit == 1), 1),
  osd_alarm_windows_pct = round(100 * mean(osd_state == "ALARM"), 1),
  osd_alarm_onsets_per_hour = round(sum(osd_state == "ALARM" & shift(osd_state, fill = "OK") != "ALARM") / (.N * 5 / 3600), 1),
  flap_positive_pct = round(100 * mean(flap_hit == 1), 1),
  flap_alarm_windows_pct = round(100 * mean(flap_state == "ALARM"), 1)), by = by]
options(width = 250)
cat("\nBy window label (all sessions, both wrists):\n"); print(summ(W[lab != "partial"], "lab"))
fwrite(summ(W[lab != "partial"], "lab"), file.path(OUT, "summary_by_label.tsv"), sep = "\t")
# Sensitivity of the OSD power threshold to calibration error: rescale units by k (power by k^2)
sens <- rbindlist(lapply(c(0.5, 0.75, 1, 1.25, 1.5), function(k) {
  W[lab != "partial", .(scale_factor = k,
    osd_positive_pct = round(100 * mean(osd_roi * k^2 > OSD$thresh & osd_ratio > OSD$ratio), 1)), by = lab]
}))
cat("\nSensitivity of OSD-positive windows to a unit-calibration error of factor k:\n"); print(dcast(sens, scale_factor ~ lab, value.var = "osd_positive_pct"))
cat("\nBy stereotypy type:\n")
W[, type := fifelse(`Flap-Rock`, "Flap-Rock", fifelse(Flap, "Flap", fifelse(Rock, "Rock", fifelse(lab == "other", "other", "partial"))))]
print(summ(W[type != "partial"], "type"))
cat("\nBy participant (stereotypy windows only):\n")
print(summ(W[lab == "stereotypy"], "participant")[order(participant)])
cat("\nBy study and label:\n"); print(summ(W[lab != "partial"], c("study", "lab")))
