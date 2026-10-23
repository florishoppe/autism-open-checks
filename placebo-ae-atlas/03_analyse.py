"""Placebo-arm adverse-event proportions per category, pooled across trials.

Usage: python3 -I 03_analyse.py <out_dir>
Reads trials.tsv, event_groups.tsv, ae_raw.tsv, term_mapping.tsv, group_overrides.tsv.
Writes analysis_set.tsv, per_trial_category.tsv, results_placebo.tsv, results_drug_vs_placebo.tsv,
and prints a short summary.

Unit of analysis is the trial: all eligible placebo groups in one trial are summed (they hold
different participants once crossover second periods and extensions are excluded).
Within a trial and arm, participants affected in a category = the largest numAffected among the
terms mapped to that category (serious or other). That is a lower bound: one child can appear
under two terms, but summing would double count. A category not listed for a trial counts as 0,
which is only correct if the event was below the registry reporting threshold or truly absent
(see README).
"""
import csv, math, os, re, sys
from collections import defaultdict

OPEN = re.compile(r"open[- ]?label|\bopen\b|extension|off treatment|control group|normal control", re.I)
APS = re.compile(r"risperid|aripipraz|lurasid|brexpipraz|olanzap|quetiap|ziprasid|paliperid|pimavanserin|haloperid", re.I)
GI = {"vomiting", "nausea", "diarrhoea", "constipation", "abdominal_pain_discomfort"}


def read(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def dl_logit(ks, ns):
    """DerSimonian-Laird random effects on the logit scale; 0.5 added to zero/full cells."""
    ys, vs = [], []
    for k, n in zip(ks, ns):
        if n == 0:
            continue
        if k == 0 or k == n:
            k, n = k + 0.5, n + 1.0
        ys.append(math.log(k / (n - k)))
        vs.append(1 / k + 1 / (n - k))
    m = len(ys)
    if m < 2:
        return (float("nan"),) * 5
    w = [1 / v for v in vs]
    yf = sum(wi * yi for wi, yi in zip(w, ys)) / sum(w)
    q = sum(wi * (yi - yf) ** 2 for wi, yi in zip(w, ys))
    c = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (q - (m - 1)) / c)
    wr = [1 / (v + tau2) for v in vs]
    yr = sum(wi * yi for wi, yi in zip(wr, ys)) / sum(wr)
    se = math.sqrt(1 / sum(wr))
    inv = lambda x: 1 / (1 + math.exp(-x))
    i2 = max(0.0, (q - (m - 1)) / q) if q > 0 else 0.0
    return inv(yr), inv(yr - 1.96 * se), inv(yr + 1.96 * se), i2, tau2


def main(d):
    trials = {t["nct"]: t for t in read(os.path.join(d, "trials.tsv"))}
    groups = read(os.path.join(d, "event_groups.tsv"))
    ae = read(os.path.join(d, "ae_raw.tsv"))
    cat_of = {r["term"]: r["category"] for r in read(os.path.join(d, "term_mapping.tsv"))}
    ov = read(os.path.join(d, "group_overrides.tsv"))
    ov_trial = {o["nct"]: o for o in ov if o["group_title"] == "*"}
    ov_group = {(o["nct"], o["group_title"]): o["new_role"] for o in ov if o["group_title"] != "*"}

    # final role per group
    role = {}
    for g in groups:
        r = ov_group.get((g["nct"], g["title"]), g["role"])
        if r == "active" and OPEN.search(g["title"]):
            r = "exclude"
        if r in ("placebo_ambiguous", "total"):
            r = "exclude"
        role[(g["nct"], g["group_id"])] = r

    def n_at_risk(g):
        vals = [num(g["other_at_risk"]), num(g["serious_at_risk"])]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else 0

    eligible = []
    for nct, t in trials.items():
        if t["has_placebo_arm"] != "1" or nct in ov_trial:
            continue
        gs = [g for g in groups if g["nct"] == nct]
        if any(role[(nct, g["group_id"])] == "placebo" for g in gs):
            eligible.append(nct)
    withdrawal = [n for n in trials if any(role.get((n, g["group_id"])) == "placebo_withdrawal" for g in groups if g["nct"] == n)]

    # per trial x arm(placebo/active) x category
    affected = defaultdict(int)  # (nct, arm, group_id, cat) -> max affected
    assess = defaultdict(lambda: defaultdict(int))
    for r in ae:
        key = (r["nct"], r["group_id"])
        rr = role.get(key)
        if rr not in ("placebo", "active") or r["nct"] not in eligible:
            continue
        c = cat_of.get(r["term"].strip(), "other")
        k = num(r["num_affected"]) or 0
        cats = [c] + (["gi_any"] if c in GI else [])
        for cc in cats:
            kk = (r["nct"], rr, r["group_id"], cc)
            affected[kk] = max(affected[kk], k)
        if rr == "placebo":
            assess[r["nct"]][r["assessment"] or "NOT_GIVEN"] += 1

    cats = sorted({c for c in cat_of.values() if c != "other"} | {"gi_any"})
    per = []  # per trial x arm x category
    for nct in eligible:
        t = trials[nct]
        for arm in ("placebo", "active"):
            gs = [g for g in groups if g["nct"] == nct and role[(nct, g["group_id"])] == arm]
            if not gs:
                continue
            n = sum(n_at_risk(g) for g in gs)
            for c in cats:
                k = sum(affected.get((nct, arm, g["group_id"], c), 0) for g in gs)
                rep = any((nct, arm, g["group_id"], c) in affected for g in gs)
                per.append({"nct": nct, "arm": arm, "category": c, "affected": k, "n": n, "reported": int(rep),
                            "age_group": t["age_group"], "threshold": t["ae_threshold_pct"]})

    with open(os.path.join(d, "per_trial_category.tsv"), "w") as f:
        keys = list(per[0].keys())
        f.write("\t".join(keys) + "\n")
        for p in per:
            f.write("\t".join(str(p[k]) for k in keys) + "\n")

    with open(os.path.join(d, "analysis_set.tsv"), "w") as f:
        f.write("nct\tage_group\tphase\tmasking\tsponsor\tplacebo_n\tactive_n\tthreshold_pct\tassessment_types_placebo_rows\tinterventions\tae_timeframe\n")
        for nct in eligible:
            t = trials[nct]
            pn = next((p["n"] for p in per if p["nct"] == nct and p["arm"] == "placebo"), 0)
            an = next((p["n"] for p in per if p["nct"] == nct and p["arm"] == "active"), 0)
            a = ",".join(f"{k}:{v}" for k, v in sorted(assess[nct].items()))
            f.write(f"{nct}\t{t['age_group']}\t{t['phase']}\t{t['masking']}\t{t['sponsor']}\t{pn}\t{an}\t{t['ae_threshold_pct']}\t{a}\t{t['interventions']}\t{t['ae_timeframe'][:200]}\n")

    def pool(rows):
        ks, ns = [r["affected"] for r in rows], [r["n"] for r in rows]
        p, lo, hi = wilson(sum(ks), sum(ns))
        rp, rlo, rhi, i2, tau2 = dl_logit(ks, ns)
        rep = [r for r in rows if r["reported"]]
        pr = sum(r["affected"] for r in rep) / sum(r["n"] for r in rep) if rep and sum(r["n"] for r in rep) else float("nan")
        return {"trials": len(rows), "n": sum(ns), "affected": sum(ks), "trials_reporting": len(rep),
                "pooled_simple": p, "simple_lo": lo, "simple_hi": hi,
                "re_logit": rp, "re_lo": rlo, "re_hi": rhi, "I2": i2,
                "prop_in_reporting_trials": pr}

    def fmt(x):
        return "" if isinstance(x, float) and math.isnan(x) else f"{x:.4f}" if isinstance(x, float) else str(x)

    out = []
    for c in cats:
        for ag in ("all", "child", "mixed", "adult", "threshold_0_only"):
            rows = [p for p in per if p["arm"] == "placebo" and p["category"] == c and p["n"] > 0
                    and (ag == "all" or p["age_group"] == ag or (ag == "threshold_0_only" and num(p["threshold"]) == 0))]
            if rows:
                out.append(dict(category=c, subset=ag, **pool(rows)))
    with open(os.path.join(d, "results_placebo.tsv"), "w") as f:
        keys = list(out[0].keys())
        f.write("\t".join(keys) + "\n")
        for o in out:
            f.write("\t".join(fmt(o[k]) for k in keys) + "\n")

    cmp_ = []
    antipsy = {n for n in eligible if APS.search(trials[n]["interventions"])}
    for c, subset in [(c, s) for s in ("all", "antipsychotic_trials") for c in cats]:
        keep = lambda n: subset == "all" or n in antipsy
        both = {p["nct"] for p in per if p["arm"] == "active" and p["n"] > 0 and keep(p["nct"])}
        pl = [p for p in per if p["arm"] == "placebo" and p["category"] == c and p["nct"] in both and p["n"] > 0]
        ac = [p for p in per if p["arm"] == "active" and p["category"] == c and p["n"] > 0 and p["nct"] in both]
        a, b = pool(pl), pool(ac)
        cmp_.append({"category": c, "subset": subset, "trials": a["trials"], "placebo_n": a["n"], "placebo_affected": a["affected"],
                     "placebo_pct": 100 * a["pooled_simple"], "active_n": b["n"], "active_affected": b["affected"],
                     "active_pct": 100 * b["pooled_simple"],
                     "ratio_active_to_placebo": (b["pooled_simple"] / a["pooled_simple"]) if a["pooled_simple"] else float("nan")})
    with open(os.path.join(d, "results_drug_vs_placebo.tsv"), "w") as f:
        keys = list(cmp_[0].keys())
        f.write("\t".join(keys) + "\n")
        for o in cmp_:
            f.write("\t".join(fmt(o[k]) for k in keys) + "\n")

    print("eligible trials:", len(eligible), " withdrawal-design placebo trials excluded:", withdrawal)
    print("placebo participants:", sum(p["n"] for p in per if p["arm"] == "placebo" and p["category"] == "headache"))
    tot = defaultdict(int)
    for n in eligible:
        for k, v in assess[n].items():
            tot[k] += v
    print("assessment types (placebo rows):", dict(tot))


if __name__ == "__main__":
    main(sys.argv[1])
