"""Recompute prevalence statistics (Wilson 95% CIs) from data/full_labels_v3.json."""
import json, math, collections, sys
def wilson(k,n,z=1.96):
    if n==0: return None
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return [round(100*(c-h)/d,1), round(100*(c+h)/d,1)]
def dist(items, key=lambda l:l['primary_v3']):
    c=collections.Counter(key(l) for l in items); n=len(items)
    return {k:{'n':v,'pct':round(100*v/n,1),'ci95':wilson(v,n)} for k,v in c.most_common()}
def compute(L):
    ev=[l for l in L if l['primary_v3']!='EVAL-BROKEN']
    src=[l for l in L if l['has_source_patch']]; nos=[l for l in L if not l['has_source_patch']]
    sec=collections.Counter(t for l in L for t in l['secondary_v3'])
    sgp={}
    for p in sorted({l['primary_v3'] for l in L}):
        g=[l for l in L if l['primary_v3']==p]; c=collections.Counter(t for l in g for t in l['secondary_v3'])
        sgp[p]={t:{'n':v,'pct':round(100*v/len(g),1)} for t,v in c.most_common()}
    va=sum('VERIF-ABSENT' in l['secondary_v3'] for l in ev)
    se=[l for l in src if l['primary_v3']!='EVAL-BROKEN']; ne=[l for l in nos if l['primary_v3']!='EVAL-BROKEN']
    nm=sum(l['primary_v3'].startswith('NARROW') for l in se); lc=sum(l['primary_v3'].startswith('LOC') for l in ne)
    return dict(n=len(L), primary_overall=dist(L), primary_evaluable_only=dist(ev),
        primary_stratified=dict(has_source_patch=dict(n=len(src),dist=dist(src)), effective_no_patch=dict(n=len(nos),dist=dist(nos))),
        secondary_overall={t:{'n':v,'pct':round(100*v/len(L),1),'ci95':wilson(v,len(L))} for t,v in sec.most_common()},
        secondary_given_primary=sgp,
        verif_absent_among_evaluable=dict(n=va,denom=len(ev),pct=round(100*va/len(ev),1),ci95=wilson(va,len(ev))),
        separability_evaluable=dict(has_source_patch_evaluable_n=len(se),near_miss_share=dict(n=nm,pct=round(100*nm/len(se),1)),
            effective_no_patch_evaluable_n=len(ne),loc_share=dict(n=lc,pct=round(100*lc/len(ne),1))))
if __name__=='__main__':
    L=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'data/full_labels_v3.json'))
    print(json.dumps(compute(L),indent=1))
