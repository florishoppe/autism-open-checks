"""Age- and year-matched comparison of autism-mention cases against other NEISS cases, 2018-2024.
For each mention, up to 10 non-mention cases with the same year, sex and single year of age
(children under 2 grouped) are drawn at random. Compares coded fields (diagnosis, body part,
location, disposition) and a few narrative keywords. Proportion ratios with Wald 95% CIs.
Usage: python3 -I 03_compare.py <dir-with-neissYYYY.tsv>"""
import csv, re, sys, os, random, math, collections
random.seed(20261023)
csv.field_size_limit(10**8)
pat = re.compile(r'AUTIS|\bASD\b|ASPERG|\bPDD\b')
src = sys.argv[1]
cases, pool = [], collections.defaultdict(list)
for y in range(2018, 2025):
    with open(os.path.join(src, f'neiss{y}.tsv'), encoding='latin-1', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            nar = (r.get('Narrative_1') or '').upper()
            age = int(r['Age'] or 0); a = 1 if age > 200 else age   # under-2s grouped
            rec = dict(y=y, sex=r['Sex'], age=a, diag=r['Diagnosis'], body=r['Body_Part'],
                       loc=r['Location'], disp=r['Disposition'], nar=nar)
            (cases if pat.search(nar) else pool[(y, r['Sex'], a)]).append(rec)
ctrl = []
for c in cases:
    p = pool[(c['y'], c['sex'], c['age'])]
    ctrl += random.sample(p, min(10, len(p)))
print(f'autism-mention cases {len(cases)}, matched comparison cases {len(ctrl)}')
feats = [
    ('Diagnosis: poisoning (68)', lambda r: r['diag'] == '68'),
    ('Diagnosis: ingested foreign body (41)', lambda r: r['diag'] == '41'),
    ('Diagnosis: laceration (59)', lambda r: r['diag'] == '59'),
    ('Diagnosis: fracture (57)', lambda r: r['diag'] == '57'),
    ('Diagnosis: internal organ injury / head injury (62)', lambda r: r['diag'] == '62'),
    ('Diagnosis: submersion (69)', lambda r: r['diag'] == '69'),
    ('Body part: head (75)', lambda r: r['body'] == '75'),
    ('Body part: face (76)', lambda r: r['body'] == '76'),
    ('Body part: hand or finger (82, 92)', lambda r: r['body'] in ('82', '92')),
    ('Location: home (1)', lambda r: r['loc'] == '1'),
    ('Location: school (8)', lambda r: r['loc'] == '8'),
    ('Location: sports/recreation (9)', lambda r: r['loc'] == '9'),
    ('Admitted (4)', lambda r: r['disp'] == '4'),
    ('Text: head-banging', lambda r: bool(re.search(r'BANG|HITTING (HIS|HER) HEAD|HIT (HIS|HER) HEAD (AGAINST|ON|INTO) (THE |A )?WALL', r['nar']))),
    ('Text: punched wall/window/door', lambda r: bool(re.search(r'PUNCH\w* (A |THE )?(WALL|WINDOW|DOOR|GLASS)', r['nar']))),
    ('Text: battery', lambda r: 'BATTER' in r['nar']),
    ('Text: magnet', lambda r: 'MAGNET' in r['nar']),
    ('Text: window fall', lambda r: bool(re.search(r'FELL (OUT |FROM |THROUGH )?(A |THE )?.{0,15}WINDOW', r['nar']))),
    ('Text: drowning/submersion', lambda r: bool(re.search(r'DROWN|SUBMER', r['nar']))),
    ('Text: seizure', lambda r: bool(re.search(r'SEIZ|\bSZ\b', r['nar']))),
    ('Text: sports', lambda r: bool(re.search(r'BASKETBALL|FOOTBALL|SOCCER|BASEBALL|SOFTBALL|HOCKEY|LACROSSE|VOLLEYBALL', r['nar']))),
]
print(f"{'feature':52s} {'autism %':>8s} {'comp %':>7s} {'ratio':>6s}  95% CI")
rows = []
for name, fn in feats:
    a = sum(fn(r) for r in cases); b = sum(fn(r) for r in ctrl)
    pa, pb = a / len(cases), b / len(ctrl)
    if a and b:
        rr = pa / pb; se = math.sqrt(1/a - 1/len(cases) + 1/b - 1/len(ctrl))
        lo, hi = rr * math.exp(-1.96 * se), rr * math.exp(1.96 * se)
        ci = f'{lo:.2f}-{hi:.2f}'
    else:
        rr, ci = float('nan'), 'n/a'
    rows.append((name, a, round(100*pa, 1), b, round(100*pb, 1), round(rr, 2), ci))
    print(f'{name:52s} {100*pa:8.1f} {100*pb:7.1f} {rr:6.2f}  {ci}   (n={a} vs {b})')
with open('comparison_2018_2024.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['feature', 'autism_n', 'autism_pct', 'comparison_n', 'comparison_pct', 'ratio', 'ci95']); w.writerows(rows)
