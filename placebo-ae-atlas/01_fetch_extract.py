"""Fetch autism placebo-controlled trials with posted results from ClinicalTrials.gov (API v2)
and extract their adverse-event modules into a flat table.

Usage: python3 -I 01_fetch_extract.py <cache_dir> <out_dir>
  cache_dir: where downloaded JSON is stored (treated as data, not committed)
  out_dir:   this folder; writes query_log.tsv, trials.tsv, ae_raw.tsv, event_groups.tsv
Standard library only.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

API = "https://clinicaltrials.gov/api/v2/studies"
COND = 'autism OR autistic OR "autism spectrum disorder" OR asperger OR "pervasive developmental disorder"'


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "placebo-ae-atlas/0.1 (research script)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), url
        except Exception:
            time.sleep(2 + 3 * attempt)
    raise RuntimeError("failed: " + url)


def count(params):
    p = dict(params, countTotal="true", pageSize=1, fields="NCTId")
    d, url = get(p)
    return d["totalCount"], url


def fetch_all(params, cache_dir):
    studies, token = [], None
    while True:
        p = dict(params, pageSize=200, format="json")
        if token:
            p["pageToken"] = token
        d, _ = get(p)
        studies += d["studies"]
        token = d.get("nextPageToken")
        if not token:
            break
    with open(os.path.join(cache_dir, "studies.json"), "w") as f:
        json.dump(studies, f)
    return studies


def years(s):
    """'17 Years' -> 17.0; months/weeks converted; None if absent."""
    if not s:
        return None
    m = re.match(r"([\d.]+)\s*(\w+)", s)
    if not m:
        return None
    v, u = float(m.group(1)), m.group(2).lower()
    return v if u.startswith("year") else v / 12 if u.startswith("month") else v / 52.18 if u.startswith("week") else v / 365.25


PLACEBO = re.compile(r"placebo|sugar pill|dummy|inactive", re.I)
AMBIG = re.compile(r"\bthen\b|followed|switch|extension|open[- ]label|cross-?over|\bto\b|->|→|/|\+|\bplus\b|\bwith\b|\band\b|period|phase", re.I)
TOTAL = re.compile(r"^\s*(total|all (participants|subjects|patients)|overall)", re.I)


def group_role(title):
    if TOTAL.search(title):
        return "total"
    if PLACEBO.search(title):
        return "placebo_ambiguous" if AMBIG.search(title) else "placebo"
    return "active"


def main(cache_dir, out_dir):
    os.makedirs(cache_dir, exist_ok=True)
    base = {"query.cond": COND, "filter.advanced": "AREA[HasResults]true"}
    steps = [
        ("A cond=autism (simple), has results", {"query.cond": "autism", "filter.advanced": "AREA[HasResults]true"}),
        ("B cond=broad autism terms, has results", base),
        ("C B + interventional", dict(base, **{"filter.advanced": "AREA[HasResults]true AND AREA[StudyType]INTERVENTIONAL"})),
        ("D C + randomized", dict(base, **{"filter.advanced": "AREA[HasResults]true AND AREA[StudyType]INTERVENTIONAL AND AREA[DesignAllocation]RANDOMIZED"})),
        ("E D + 'placebo' anywhere (query.term)", dict(base, **{"filter.advanced": "AREA[HasResults]true AND AREA[StudyType]INTERVENTIONAL AND AREA[DesignAllocation]RANDOMIZED", "query.term": "placebo"})),
    ]
    log = []
    for label, p in steps:
        n, url = count(p)
        log.append((label, n, url))
        print(label, n)
    studies = fetch_all(steps[3][1], cache_dir)  # step D; placebo classified locally (more sensitive than E)

    trials, groups, rows = [], [], []
    for s in studies:
        ps, rs = s.get("protocolSection", {}), s.get("resultsSection", {})
        nct = ps["identificationModule"]["nctId"]
        arms = ps.get("armsInterventionsModule", {})
        arm_types = sorted({a.get("type", "") for a in arms.get("armGroups", [])})
        intr = "; ".join(i.get("name", "") for i in arms.get("interventions", []))
        has_pbo_arm = "PLACEBO_COMPARATOR" in arm_types or bool(PLACEBO.search(intr))
        el = ps.get("eligibilityModule", {})
        amin, amax = years(el.get("minimumAge")), years(el.get("maximumAge"))
        agegrp = "child" if amax is not None and amax < 18 else "adult" if amin is not None and amin >= 18 else "mixed"
        ae = rs.get("adverseEventsModule", {})
        egs = ae.get("eventGroups", [])
        roles = {g["id"]: group_role(g.get("title", "")) for g in egs}
        design = ps.get("designModule", {})
        trials.append({
            "nct": nct, "title": ps["identificationModule"].get("briefTitle", ""),
            "conditions": "; ".join(ps.get("conditionsModule", {}).get("conditions", [])),
            "interventions": intr, "arm_types": "; ".join(arm_types), "has_placebo_arm": int(has_pbo_arm),
            "masking": design.get("designInfo", {}).get("maskingInfo", {}).get("masking", ""),
            "model": design.get("designInfo", {}).get("interventionModel", ""),
            "phase": "; ".join(design.get("phases", [])),
            "enrollment": design.get("enrollmentInfo", {}).get("count", ""),
            "min_age": el.get("minimumAge", ""), "max_age": el.get("maximumAge", ""), "age_group": agegrp,
            "sponsor": ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", ""),
            "ae_threshold_pct": ae.get("frequencyThreshold", ""),
            "ae_timeframe": (ae.get("timeFrame", "") or "").replace("\t", " ").replace("\n", " "),
            "ae_description": (ae.get("description", "") or "").replace("\t", " ").replace("\n", " ")[:500],
            "n_event_groups": len(egs), "n_placebo_groups": sum(r == "placebo" for r in roles.values()),
        })
        for g in egs:
            groups.append({"nct": nct, "group_id": g["id"], "title": g.get("title", ""), "role": roles[g["id"]],
                           "serious_affected": g.get("seriousNumAffected", ""), "serious_at_risk": g.get("seriousNumAtRisk", ""),
                           "other_affected": g.get("otherNumAffected", ""), "other_at_risk": g.get("otherNumAtRisk", ""),
                           "description": (g.get("description", "") or "").replace("\t", " ").replace("\n", " ")[:300]})
        for kind in ("seriousEvents", "otherEvents"):
            for ev in ae.get(kind, []):
                for st in ev.get("stats", []):
                    rows.append({"nct": nct, "kind": "serious" if kind == "seriousEvents" else "other",
                                 "term": ev.get("term", ""), "organ_system": ev.get("organSystem", ""),
                                 "vocab": ev.get("sourceVocabulary", ""), "assessment": ev.get("assessmentType", ""),
                                 "group_id": st.get("groupId", ""), "role": roles.get(st.get("groupId", ""), "?"),
                                 "num_affected": st.get("numAffected", ""), "num_events": st.get("numEvents", ""),
                                 "num_at_risk": st.get("numAtRisk", "")})

    def write(name, recs):
        with open(os.path.join(out_dir, name), "w") as f:
            keys = list(recs[0].keys())
            f.write("\t".join(keys) + "\n")
            for r in recs:
                f.write("\t".join(str(r[k]).replace("\t", " ") for k in keys) + "\n")

    write("trials.tsv", trials)
    write("event_groups.tsv", groups)
    write("ae_raw.tsv", rows)
    with open(os.path.join(out_dir, "query_log.tsv"), "w") as f:
        f.write("step\thits\turl\n")
        f.write("".join(f"{a}\t{b}\t{c}\n" for a, b, c in log))
        f.write(f"fetched (step D)\t{len(studies)}\tdownloaded {time.strftime('%Y-%m-%d')}\n")
        f.write(f"with placebo arm (arm type PLACEBO_COMPARATOR or 'placebo' in intervention name)\t{sum(t['has_placebo_arm'] for t in trials)}\tlocal filter\n")
        f.write(f"... and >=1 cleanly placebo-titled AE group\t{sum(t['has_placebo_arm'] and t['n_placebo_groups'] > 0 for t in trials)}\tlocal filter\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
