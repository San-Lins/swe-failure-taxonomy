import json, re, collections
from datasets import load_from_disk
d=load_from_disk('/tmp/claude-0/hf/traj')
L=json.load(open('/home/claude/repo/data/full_labels_v3.json'))
def summ(t):
    t=re.sub(r'\x1b\[[0-9;]*m','',t)
    lines=re.findall(r'(?m)^=+ ((?:\d+ \w+(?:, )?)+.*?) in [\d.]+s', t)
    if lines:
        s=lines[-1]; g=lambda k:(int(m.group(1)) if (m:=re.search(r'(\d+) '+k,s)) else 0)
        return dict(src='pytest',passed=g('passed'),failed=g('failed'),errors=g('error'))
    m=re.search(r'Results \([\d.]+s\):\s*\n((?:\s+\d+ \w+\n?)+)', t)
    if m:
        s=m.group(1); g=lambda k:(int(x.group(1)) if (x:=re.search(r'(\d+) '+k,s)) else 0)
        return dict(src='rich',passed=g('passed'),failed=g('failed'),errors=g('error'))
    return None
bad=[]; kinds=collections.Counter()
for l in L:
    tr=d[l['idx']]['test_result']; s=summ(tr['test_output']); ts=l['test_signal']
    if s is None:
        kinds['no_summary']+=1
        if ts['passed'] is not None or ts['failed'] is not None: bad.append((l['idx'],l['instance_id'],l['primary_v3'],ts,s,'label has counts but no summary'))
        continue
    kinds[s['src']]+=1
    lp=ts['passed'] or 0; lf=ts['failed']
    if lp!=s['passed'] or (lf if lf is not None else 0) not in (s['failed'], s['failed']+s['errors']):
        bad.append((l['idx'],l['instance_id'],l['primary_v3'],ts,s,'count mismatch'))
print(dict(kinds)); print(len(bad))
for b in bad: print(b)
