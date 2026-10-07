"""Gemma 4 hit@5 by the GPT-4o agent's failure branch, from results/ and the current labels."""
import json, csv, collections, math
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return [round(100*(c-h)/d,1), round(100*(c+h)/d,1)]
L=json.load(open('data/full_labels_v3.json'))
by=collections.defaultdict(list)
for l in L: by[l['instance_id']].append(l['primary_v3'])
def branch(labs):
    if any(x.startswith("LOC") for x in labs): return "LOC-*"
    if any(x.startswith("NARROW") for x in labs): return "NARROW-*"
    return "other"
rows=list(csv.DictReader(open('results/localization-hygiene/localization_by_branch.csv')))  # rows are in sorted instance_id order
for col in ['BM25 (paths)','gemma-4-e4b-it','gemma-4-12b-it']:
    for b in ['LOC-*','NARROW-*']:
        s=[r for i,r in zip(sorted(by),rows) if branch(by[i])==b]; k=sum(int(float(r[col])) for r in s)
        print(f"{col:15s} {b:9s} n={len(s):3d} hit@5={100*k/len(s):.1f} {wilson(k,len(s))}")
