# Feasibility count: autism mentions in NEISS narratives.
# Input: injuries.rda and products.rda from github.com/hadley/neiss (NEISS 2013-2017,
# as released by CPSC). Usage: Rscript 01_extract.R <dir-with-rda> <out-dir>
args <- commandArgs(TRUE); src <- args[1]; out <- args[2]
suppressPackageStartupMessages(library(data.table))
load(file.path(src, "injuries.rda")); load(file.path(src, "products.rda"))
x <- as.data.table(injuries)
x[, year := as.integer(format(trmt_date, "%Y"))]
x <- x[year >= 2013 & year <= 2017]
n <- toupper(x$narrative)
# Broad pattern first; precision is checked by hand-reading a sample.
x[, hit_autis := grepl("AUTIS", n)]
x[, hit_asd := grepl("\\bASD\\b", n, perl = TRUE)]
x[, hit_asperger := grepl("ASPERG", n)]
x[, hit_pdd := grepl("\\bPDD\\b", n, perl = TRUE)]
x[, hit := hit_autis | hit_asd | hit_asperger | hit_pdd]
x[, wt := weight]
cat("Total cases:", nrow(x), "\n")
print(x[, .(cases = .N, autism_mentions = sum(hit), autis = sum(hit_autis), asd = sum(hit_asd),
            asperger = sum(hit_asperger), pdd = sum(hit_pdd),
            per_100k_cases = round(1e5 * mean(hit), 1),
            weighted_national_est = round(sum(wt[hit]))), by = year][order(year)])
h <- x[hit == TRUE]
h[, age_years := fifelse(age > 200, (age - 200) / 12, as.numeric(age))]  # NEISS codes <2y as 2xx months
h[, age_band := cut(age_years, c(-Inf, 4, 9, 14, 19, 29, Inf),
                    labels = c("0-4", "5-9", "10-14", "15-19", "20-29", "30+"))]
cat("\nAge bands among mentions:\n"); print(h[, .N, by = age_band][order(age_band)])
cat("\nAll cases age bands (for comparison, %):\n")
x[, age_years := fifelse(age > 200, (age - 200) / 12, as.numeric(age))]
print(round(100 * prop.table(table(cut(x$age_years, c(-Inf, 4, 9, 14, 19, 29, Inf)))), 1))
p <- as.data.table(products); setnames(p, c("code", "title"))
h <- merge(h, p, by.x = "prod1", by.y = "code", all.x = TRUE)
cat("\nTop 25 coded products among autism mentions:\n")
print(h[, .N, by = title][order(-N)][1:25])
cat("\nDisposition among mentions (4 = admitted, 5 = held for observation, 8 = died):\n")
print(h[, .N, by = disposition][order(-N)])
fwrite(h[, .(case_num, year, trmt_date, age_years, sex, prod1, product = title, diag, body_part,
             disposition, location, weight, hit_autis, hit_asd, hit_asperger, hit_pdd, narrative)],
       file.path(out, "autism_mentions_2013_2017.tsv"), sep = "\t")
cat("\nWrote", nrow(h), "rows\n")
