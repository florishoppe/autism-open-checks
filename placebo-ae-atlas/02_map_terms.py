"""Map reported adverse-event terms to a small set of categories by explicit regex rules.

Usage: python3 -I 02_map_terms.py <out_dir>
Reads ae_raw.tsv, writes term_mapping.tsv (one row per distinct term, with the rule that matched).
Rules are applied to the lower-cased term; the first matching rule wins. Unmatched terms are 'other'.
Review term_mapping.tsv by eye; edit RULES and rerun rather than editing the table by hand.
"""
import csv, os, re, sys
from collections import Counter

RULES = [
    ("seizure", r"seizure|convuls|epilep"),
    ("gastroenteritis", r"gastroenteritis|stomach (flu|virus|bug)"),
    ("self_injury", r"self[- ]?injur|self[- ]?harm|self[- ]?mutil|head bang|skin picking"),
    ("irritability_agitation_aggression", r"irritab|agitat|aggress|anger|angry|hostil|tantrum|\btemper\b|mood swing|affect labil|mood altered|emotional (disorder|lability|distress)|crying|frustrat|outburst|oppositional|disruptive"),
    ("insomnia_sleep_disturbance", r"insomnia|sleep (disorder|disturb|problem|terror|walking)|nightmare|abnormal dream|poor quality sleep|trouble sleeping|difficulty (falling )?a?sleep|night waking|dyssomnia|initial insomnia|middle insomnia"),
    ("somnolence_sedation_fatigue", r"somnolen|sedat|fatigue|letharg|hypersomnia|tired|drows|asthenia|sleepiness|excessive sleep"),
    ("appetite_increased", r"increased appetite|appetite increased|hyperphagia|appetite.*increase"),
    ("appetite_decreased", r"decreased appetite|appetite decreased|anorexia|appetite loss|loss of appetite|hypophagia|appetite.*decrease|reduced appetite"),
    ("weight_increased", r"weight increase|weight gain|increased weight|weight.*increase"),
    ("weight_decreased", r"weight decrease|weight loss|decreased weight|weight.*decrease"),
    ("vomiting", r"vomit|emesis"),
    ("nausea", r"nausea"),
    ("diarrhoea", r"diarrh"),
    ("constipation", r"constipat"),
    ("abdominal_pain_discomfort", r"abdominal (pain|discomfort|distension)|stomach ?ache|stomach (pain|upset|discomfort)|dyspepsia|gastrointestinal (pain|upset|disorder)|flatulence|abdominal pain upper"),
    ("headache", r"headache|migraine"),
    ("respiratory_ent_infection_cold", r"upper respiratory|nasopharyng|common cold|(?<!feeling )\bcold\b(?! ?(hands?|sores?|feet))|runny nose|sneez|sore throat|oropharyngeal pain|ear infection|otitis|\buri\b|sinusitis|pharyngitis|influenza|\bflu\b|rhinitis|rhinorrh|nasal congestion|bronchitis|respiratory tract infection|tonsillitis|croup"),
    ("cough", r"cough|tussis"),
    ("pyrexia", r"pyrexia|fever|febrile(?! neutropenia)"),
    ("hyperactivity_restlessness", r"hyperactiv|restless(?! legs)|psychomotor hyperactiv|hyperkines|impulsiv|increased (motor activity|energy)"),
    ("low_mood", r"depress(ed mood|ion|ive)|sadness|\bsad\b|tearful"),
    ("anxiety", r"(?<!less )anxi|nervous(?! system)|panic|\bfear"),
    ("enuresis", r"enuresis|urinary incontinence|bed ?wetting|wetting"),
    ("rash_skin", r"rash|dermatitis|eczema|urticaria|prurit"),
    ("dizziness", r"dizz|vertigo"),
    ("tremor_eps", r"tremor|extrapyramid|dyskines|dystoni|akathisia|parkinson|muscle rigidity|drooling|salivary hypersecretion"),
]
COMPILED = [(c, re.compile(p)) for c, p in RULES]


def classify(term):
    t = term.lower()
    for c, rx in COMPILED:
        m = rx.search(t)
        if m:
            return c, m.group(0)
    return "other", ""


def main(out_dir):
    trials = Counter()
    seen = {}
    with open(os.path.join(out_dir, "ae_raw.tsv")) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = r["term"].strip()
            seen.setdefault(key, set()).add(r["nct"])
    with open(os.path.join(out_dir, "term_mapping.tsv"), "w") as f:
        f.write("term\tcategory\tmatched_text\tn_trials\n")
        for term in sorted(seen, key=lambda k: (-len(seen[k]), k.lower())):
            c, m = classify(term)
            f.write(f"{term}\t{c}\t{m}\t{len(seen[term])}\n")


if __name__ == "__main__":
    main(sys.argv[1])
