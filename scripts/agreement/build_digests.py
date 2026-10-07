import json, random, re, collections
from datasets import load_from_disk
d = load_from_disk('/tmp/claude-0/hf/traj')
L = json.load(open('/home/claude/repo/data/full_labels_v3.json'))
pool = [l for l in L if l['provenance'] in ('v2_kept','gate_eval_broken','v2_kept+lit_mapped')]
quota = {'NARROW-INCOMPLETE':27,'EVAL-BROKEN':8,'NARROW-REGRESSIVE':6,'LOC-REPAIR':5,'LOC-EXPLORE':3,'LIT-TASK':1}
rng = random.Random(2026)
samp = []
for c,q in quota.items():
    cand = sorted([l for l in pool if l['primary_v3']==c], key=lambda l:l['idx'])
    samp += rng.sample(cand, q)
review = [l for l in L if l['primary_v3']=='NARROW-INCOMPLETE' and (l['test_signal']['failed'] or 0)>4]
items = {l['idx']: l for l in samp + review}
order = sorted(items); rng.shuffle(order)
def text_of(c):
    if c is None: return ''
    if isinstance(c,str): return c
    if isinstance(c,list): return ''.join(x.get('text','') if isinstance(x,dict) else str(x) for x in c)
    return str(c)
def clip(s,n): s=s.strip(); return s if len(s)<=n else s[:n]+f' …[+{len(s)-n} chars]'
def digest(idx):
    r = d[idx]; m = r['messages']; tr = r['test_result']
    out = []
    issue = ''
    for x in m:
        if x.get('role')=='user':
            t=text_of(x.get('content')); mm=re.search(r'<pr_description>(.*?)</pr_description>', t, re.S)
            issue = mm.group(1) if mm else t; break
    out.append('## ISSUE\n'+clip(issue,3000))
    out.append('## ACTIONS (assistant tool calls; OBS = first lines of the following observation)')
    step=0
    for i,x in enumerate(m):
        if x.get('role')!='assistant': continue
        txt = text_of(x.get('content'))
        if txt.strip() and not x.get('tool_calls'):
            out.append(f'[text] {clip(txt,300)}')
        for tc in (x.get('tool_calls') or []):
            step+=1
            fn=tc.get('function',{}); name=fn.get('name')
            try: a=json.loads(fn.get('arguments') or '{}')
            except Exception: a={'_raw':fn.get('arguments')}
            if name=='str_replace_editor':
                desc=f"editor {a.get('command')} {a.get('path','')}"
                if a.get('command')=='str_replace': desc+=f"\n   old: {clip(a.get('old_str') or '',300)}\n   new: {clip(a.get('new_str') or '',300)}"
                elif a.get('command')=='create': desc+=f"\n   content: {clip(a.get('file_text') or '',300)}"
                elif a.get('command')=='insert': desc+=f"\n   insert: {clip(a.get('new_str') or '',300)}"
                elif a.get('view_range'): desc+=f" range={a.get('view_range')}"
            elif name=='execute_bash': desc='bash: '+clip(a.get('command',''),300)
            elif name=='finish': desc='finish'
            else: desc=f'{name} {clip(json.dumps(a),300)}'
            obs=''
            for n in m[i+1:i+3]:
                if n.get('role')=='tool': obs=text_of(n.get('content')); break
            out.append(f'{step}. {desc}\n   OBS: {clip(obs,400)}')
            if txt.strip(): out.append(f'   [thought] {clip(txt,200)}')
    out.append('## FINAL PATCH\n'+clip(tr.get('git_patch',''),5000))
    ts=items[idx]['test_signal']
    out.append(f"## TEST RESULT (official evaluation after the run)\nparsed counts: passed={ts['passed']} failed={ts['failed']} eval_interrupted={ts['eval_interrupted']}")
    to=tr.get('test_output','')
    fails=sorted(set(re.findall(r'^(?:FAILED|ERROR)\s+(\S+)', to, re.M)))
    out.append('failed/error test ids: '+(', '.join(fails[:40]) if fails else '(none listed)'))
    out.append('tail of test output:\n'+to[-2500:])
    return '\n'.join(out)
import os
os.makedirs('/tmp/claude-0/agr/digests',exist_ok=True)
meta=[]
for k,idx in enumerate(order):
    cid=f'C{k+1:02d}'
    open(f'/tmp/claude-0/agr/digests/{cid}.md','w').write(f'# CASE {cid}\n\n'+digest(idx))
    meta.append(dict(case=cid, idx=idx, instance_id=items[idx]['instance_id'], in_kappa_sample=items[idx] in samp, in_review=items[idx] in review))
json.dump(meta, open('/tmp/claude-0/agr/meta.json','w'), indent=1)
print(len(order), sum(x['in_kappa_sample'] for x in meta), sum(x['in_review'] for x in meta), sum(x['in_kappa_sample'] and x['in_review'] for x in meta))
