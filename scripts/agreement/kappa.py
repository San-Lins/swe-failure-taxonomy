import json, glob, collections, math
meta={m['case']:m for m in json.load(open('meta.json'))}
L={l['idx']:l for l in json.load(open('/home/claude/repo/data/full_labels_v3.json'))}
B={}
for f in sorted(glob.glob('out/batch*.json')):
    for x in json.load(open(f)): B[x['case']]=x
print('annotated',len(B))
def kappa(pairs):
    n=len(pairs); po=sum(a==b for a,b in pairs)/n
    ca=collections.Counter(a for a,_ in pairs); cb=collections.Counter(b for _,b in pairs)
    pe=sum(ca[k]*cb[k] for k in set(ca)|set(cb))/n/n
    return po,(po-pe)/(1-pe)
def boot(pairs,R=2000):
    import random; rng=random.Random(0); ks=[]
    for _ in range(R):
        s=[pairs[rng.randrange(len(pairs))] for _ in pairs]
        try: ks.append(kappa(s)[1])
        except ZeroDivisionError: pass
    ks.sort(); return ks[int(.025*len(ks))], ks[int(.975*len(ks))]
rows=[]
for c,m in meta.items():
    l=L[m['idx']]; b=B[c]
    rows.append(dict(case=c,idx=m['idx'],iid=m['instance_id'],k=m['in_kappa_sample'],rev=m['in_review'],
      v3=l['primary_v3'],new=b['primary'],conf=b.get('confidence'),reason=b.get('reason'),
      sec_v3=set(l['secondary_v3']),sec_new=set(b.get('secondary',[])),failed=l['test_signal']['failed'],passed=l['test_signal']['passed']))
S=[r for r in rows if r['k']]
pairs=[(r['v3'],r['new']) for r in S]
po,k=kappa(pairs); print(f'n={len(S)} agree={sum(a==b for a,b in pairs)} po={po:.3f} kappa={k:.3f} CI={boot(pairs)}')
# coarse branch
def br(x): return x.split('-')[0] if x.split('-')[0] in('NARROW','LOC') else x
bp=[(br(a),br(b)) for a,b in pairs]; po2,k2=kappa(bp); print(f'branch-level agree={sum(a==b for a,b in bp)} kappa={k2:.3f}')
# excluding gate
ng=[(a,b) for a,b in pairs if a!='EVAL-BROKEN' and b!='EVAL-BROKEN']
print('gate agreement:', sum((a=='EVAL-BROKEN')==(b=='EVAL-BROKEN') for a,b in pairs), '/',len(pairs))
print('non-gate n',len(ng),'kappa %.3f'%kappa(ng)[1], 'agree',sum(a==b for a,b in ng))
print('confusion:'); print(collections.Counter((a,b) for a,b in pairs if a!=b))
for t in ['HYG','VERIF-ABSENT','TOOL','CONFAB']:
    p=[(t in r['sec_v3'], t in r['sec_new']) for r in S]; 
    try: print(t, 'agree',sum(a==b for a,b in p),'kappa %.3f'%kappa(p)[1], 'v3',sum(a for a,_ in p),'new',sum(b for _,b in p))
    except ZeroDivisionError: print(t,'n/a')
print('\nDISAGREEMENTS (kappa sample):')
for r in S:
    if r['v3']!=r['new']: print(r['case'],r['iid'],r['v3'],'->',r['new'],r['conf'],f"p={r['passed']} f={r['failed']}",'|',r['reason'])
print('\nREVIEW 23 (INCOMPLETE, failed>4):')
R=[r for r in rows if r['rev']]; print(collections.Counter(r['new'] for r in R))
for r in R: print(r['case'],r['iid'],r['new'],r['conf'],f"p={r['passed']} f={r['failed']}",'|',r['reason'])
json.dump([{**r,'sec_v3':sorted(r['sec_v3']),'sec_new':sorted(r['sec_new'])} for r in rows],open('merged.json','w'),indent=1)
