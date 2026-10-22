"""Compare autism-mention NEISS cases with cases whose narratives mention other conditions that
coders record in a similar, selective way (ADHD, Down syndrome, cerebral palsy, developmental
delay / intellectual disability). Recommended by the stress test as a fairer comparison than
'all other cases'. Cases mentioning autism are excluded from the other groups. Ages 2-25 only, to
limit age confounding. 2018-2024 CPSC files.
Usage: python3 -I 04_other_conditions.py <dir-with-neissYYYY.tsv>"""
import csv, re, sys, os, math, collections
csv.field_size_limit(10**8)
src = sys.argv[1]
G = [('autism', re.compile(r'AUTIS|\bASD\b|ASPERG|\bPDD\b')),
     ('ADHD', re.compile(r'\bADHD\b|ATTENTION DEFICIT')),
     ('Down syndrome', re.compile(r"DOWN'?S? SYNDROME|TRISOMY 21|\bDOWNS\b")),
     ('cerebral palsy', re.compile(r'CEREBRAL PALSY')),
     ('dev. delay / ID', re.compile(r'DEVELOPMENTAL(LY)? DELAY|INTELLECTUAL(LY)? DISAB|MENTAL RETARD|GLOBAL DELAY'))]
F = [('poisoning (dx 68)', lambda r, n: r['Diagnosis'] == '68'),
     ('ingested FB (dx 41)', lambda r, n: r['Diagnosis'] == '41'),
     ('fracture (dx 57)', lambda r, n: r['Diagnosis'] == '57'),
     ('head (bp 75)', lambda r, n: r['Body_Part'] == '75'),
     ('home (loc 1)', lambda r, n: r['Location'] == '1'),
     ('sports/rec (loc 9)', lambda r, n: r['Location'] == '9'),
     ('admitted', lambda r, n: r['Disposition'] == '4'),
     ('head-banging', lambda r, n: bool(re.search(r'BANG|HITTING (HIS|HER) HEAD|HIT (HIS|HER) HEAD (AGAINST|ON|INTO) (THE |A )?WALL', n))),
     ('punched wall/window/door', lambda r, n: bool(re.search(r'PUNCH\w* (A |THE )?(WALL|WINDOW|DOOR|GLASS)', n))),
     ('battery', lambda r, n: 'BATTER' in n),
     ('magnet', lambda r, n: 'MAGNET' in n),
     ('window fall', lambda r, n: bool(re.search(r'FELL (OUT |FROM |THROUGH )?(A |THE )?.{0,15}WINDOW', n))),
     ('drowning/submersion', lambda r, n: bool(re.search(r'DROWN|SUBMER', n))),
     ('seizure', lambda r, n: bool(re.search(r'SEIZ|\bSZ\b', n))),
     ('wandering/elopement', lambda r, n: bool(re.search(r'\bELOP(E|ED|ES|EMENT|ING)\b|\bWANDER|RAN AWAY|RAN OFF', n)))]
cnt = {g: collections.Counter() for g, _ in G}; N = collections.Counter()
for y in range(2018, 2025):
    with open(os.path.join(src, f'neiss{y}.tsv'), encoding='latin-1', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            age = int(r['Age'] or 0); a = (age - 200) / 12 if age > 200 else age
            if not (2 <= a <= 25): continue
            n = (r.get('Narrative_1') or '').upper()
            aut = G[0][1].search(n)
            for g, p in G:
                if (g == 'autism' and aut) or (g != 'autism' and not aut and p.search(n)):
                    N[g] += 1
                    for name, fn in F:
                        if fn(r, n): cnt[g][name] += 1
groups = [g for g, _ in G]
others = groups[1:]
pool_n = sum(N[g] for g in others)
print('cases (ages 2-25, 2018-2024):', dict(N))
hdr = f"{'feature':26s}" + ''.join(f'{g[:14]:>15s}' for g in groups) + f"{'autism vs pooled others (95% CI)':>36s}"
print(hdr)
rows = []
for name, _ in F:
    a = cnt['autism'][name]; b = sum(cnt[g][name] for g in others)
    pa, pb = a / N['autism'], b / pool_n
    if a and b:
        rr = pa / pb; se = math.sqrt(1/a - 1/N['autism'] + 1/b - 1/pool_n)
        ci = f'{rr:.2f} ({rr*math.exp(-1.96*se):.2f}-{rr*math.exp(1.96*se):.2f})'
    else:
        ci = 'n/a'
    line = f'{name:26s}' + ''.join(f'{100*cnt[g][name]/N[g]:14.1f}%' for g in groups) + f'{ci:>36s}'
    print(line)
    rows.append([name] + [round(100*cnt[g][name]/N[g], 1) for g in groups] + [ci])
with open('comparison_other_conditions_2018_2024.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t'); w.writerow(['feature'] + [g + ' %' for g in groups] + ['autism_vs_pooled_others']); w.writerows(rows)
