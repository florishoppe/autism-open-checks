"""Count autism mentions in official CPSC NEISS annual .tsv files (2018-2024 here).
Usage: python3 -I 02_extend_cpsc.py <dir-with-neissYYYY.tsv> <products.tsv> <out-dir>"""
import csv, re, sys, os, collections
src, prodf, out = sys.argv[1:4]
csv.field_size_limit(10**8)
prod = {}
for r in csv.DictReader(open(prodf), delimiter='\t'):
    prod[r['code']] = r['title']
pat = re.compile(r'AUTIS|\bASD\b|ASPERG|\bPDD\b')
rows, summary = [], []
for fn in sorted(os.listdir(src)):
    m = re.match(r'neiss(\d{4})\.tsv$', fn)
    if not m or int(m.group(1)) < 2018: continue
    y = int(m.group(1)); n = hits = 0; wsum = 0.0
    with open(os.path.join(src, fn), encoding='latin-1', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            n += 1
            nar = (r.get('Narrative_1') or '') + ' ' + (r.get('Narrative_2') or '')
            if pat.search(nar.upper()):
                hits += 1; w = float(r['Weight'] or 0); wsum += w
                age = int(r['Age'] or 0); age_y = (age - 200) / 12 if age > 200 else age
                rows.append(dict(case_num=r['CPSC_Case_Number'], year=y, trmt_date=r['Treatment_Date'],
                                 age_years=round(age_y, 2), sex=r['Sex'], prod1=r['Product_1'],
                                 product=prod.get(r['Product_1'], 'code ' + r['Product_1']),
                                 diag=r['Diagnosis'], disposition=r['Disposition'], weight=w,
                                 narrative=nar.strip()))
    summary.append((y, n, hits, round(1e5 * hits / n, 1), round(wsum)))
print('year cases mentions per100k weighted')
for s in summary: print(*s)
with open(os.path.join(out, 'autism_mentions_2018_2024.tsv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t'); w.writeheader(); w.writerows(rows)
ages = collections.Counter('5-19' if 5 <= r['age_years'] < 20 else 'other' for r in rows)
print('total', len(rows), 'age 5-19 share', round(100 * ages['5-19'] / len(rows)))
print('top products:')
for k, v in collections.Counter(r['product'] for r in rows).most_common(15): print(f'  {v:4d} {k[:60]}')
