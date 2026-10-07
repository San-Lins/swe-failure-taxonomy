from PIL import Image, ImageDraw, ImageFont
import json
S=json.load(open('/home/claude/repo/data/prevalence_stats_v3.json'))
ev=S['primary_evaluable_only']; sep=S['separability_evaluable']
segs=[('NARROW-INCOMPLETE','#38bdf8'),('NARROW-REGRESSIVE','#818cf8'),('LOC-REPAIR','#f59e0b'),('LOC-EXPLORE','#f97316')]
other=100-sum(ev[k]['pct'] for k,_ in segs)
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BG='#0f172a'; WHITE='#ffffff'; GREY='#94a3b8'; LIGHT='#cbd5e1'; TXT='#e2e8f0'
def render(W,H,L,out):
    # L: layout dict in pixels
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    f=lambda p,s: ImageFont.truetype(p,s)
    x=L['x']
    d.text((x,L['title_y']),'Near-Misses, Not Wrong Turns',font=f(B,L['title']),fill=WHITE)
    d.text((x,L['sub_y']),'A Stratified Failure Taxonomy for SWE Coding Agents',font=f(R,L['sub']),fill=GREY)
    d.text((x,L['cap_y']),f"Primary failure modes, evaluable runs (n = {S['separability_evaluable']['has_source_patch_evaluable_n']+S['separability_evaluable']['effective_no_patch_evaluable_n']})",font=f(R,L['cap']),fill=LIGHT)
    bw=L['bar_w']; cx=x; y0,y1=L['bar_y'],L['bar_y']+L['bar_h']
    for k,c in segs:
        w=bw*ev[k]['pct']/100; d.rectangle([cx,y0,cx+w,y1],fill=c); cx+=w
    d.rectangle([cx,y0,x+bw,y1],fill='#64748b')
    lf=f(R,L['leg']); sq=L['sq']
    rows=[[segs[0],segs[1]],[segs[2],segs[3]]]
    for ri,row in enumerate(rows):
        lx=x; ly=L['leg_y']+ri*L['leg_dy']
        for k,c in row:
            d.rectangle([lx,ly,lx+sq,ly+sq],fill=c)
            t=f"{k} {ev[k]['pct']}%"; d.text((lx+sq+L['gap'],ly-L['leg_off']),t,font=lf,fill=TXT)
            lx+=sq+L['gap']+d.textlength(t,font=lf)+L['col']
    d.text((x,L['key_y']),f"Source patch → {sep['near_miss_share']['pct']}% near-miss  ·  No effective patch → {sep['loc_share']['pct']}% localization",font=f(B,L['key']),fill=WHITE)
    d.text((x,L['foot_y']),'250 GPT-4o / OpenHands trajectories  ·  Wilson 95% CIs  ·  github.com/San-Lins/swe-failure-taxonomy',font=f(R,L['foot']),fill=GREY)
    im.save(out)
L1=dict(x=64,title_y=62,title=54,sub_y=135,sub=28,cap_y=208,cap=24,bar_y=250,bar_h=65,bar_w=993,leg_y=343,leg_dy=44,leg=22,sq=23,gap=10,leg_off=0,col=36,key_y=466,key=22,foot_y=508,foot=18)
render(1120,560,L1,'/home/claude/cover_v31/cover_1120x560.png')
L2={k:(v/2 if isinstance(v,(int,float)) else v) for k,v in L1.items()}; L2={k:int(round(v)) for k,v in L2.items()}
render(560,280,L2,'/home/claude/cover_v31/cover_560x280.png')
L3=dict(x=96,title_y=95,title=60,sub_y=178,sub=30,cap_y=272,cap=26,bar_y=318,bar_h=73,bar_w=1089,leg_y=425,leg_dy=48,leg=24,sq=25,gap=10,leg_off=0,col=44,key_y=573,key=24,foot_y=623,foot=20)
render(1280,720,L3,'/home/claude/cover_v31/cover_1280x720.png')
