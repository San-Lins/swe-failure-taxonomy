import json, re, collections
from datasets import load_from_disk
d=load_from_disk('/tmp/claude-0/hf/traj')
L=json.load(open('/home/claude/repo/data/full_labels_v3.json'))
RUNNER=re.compile(r'\b(pytest|py\.test|-m\s+unittest|tox\b|nox\b|runtests\.py|-m\s+mypy\.test|manage\.py\s+test)')
def real_run(m):
    created=set(); hits=[]
    for x in m:
        for tc in x.get('tool_calls') or []:
            fn=tc['function']; 
            try:a=json.loads(fn.get('arguments') or '{}')
            except: continue
            if fn['name']=='str_replace_editor' and a.get('command')=='create': created.add(a.get('path','').split('/')[-1])
            if fn['name']=='execute_bash':
                c=a.get('command','')
                if RUNNER.search(c):
                    # exclude runs that only target agent-created files
                    targets=re.findall(r'(\S+\.py)\b', c)
                    if targets and all(t.split('/')[-1].split('::')[0] in created for t in targets): continue
                    hits.append(c[:120])
    return hits
rows=[]
for l in L:
    h=real_run(d[l['idx']]['messages'])
    rows.append((l, bool(h)))
ev=[(l,h) for l,h in rows if l['primary_v3']!='EVAL-BROKEN']
old=sum(not l['tests_run_real'] for l,_ in ev); new=sum(not h for _,h in ev)
print('evaluable',len(ev),'VERIF-ABSENT old (mechanical)',old,'new (strict)',new)
print('flips old real->strict none:',sum(l['tests_run_real'] and not h for l,h in rows),' none->real:',sum((not l['tests_run_real']) and h for l,h in rows))
print('VERIF-ABSENT tag in labels on evaluable:',sum('VERIF-ABSENT' in l['secondary_v3'] for l,_ in ev))
bc=collections.defaultdict(lambda:[0,0])
for l,h in ev: bc[l['primary_v3']][0]+=1; bc[l['primary_v3']][1]+= (not h)
print({k:(v[1],v[0],round(100*v[1]/v[0],1)) for k,v in bc.items()})
json.dump({l['idx']:h for l,h in rows},open('strict_verif.json','w'))
