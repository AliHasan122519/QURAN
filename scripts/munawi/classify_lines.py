import json,re,sys,collections
sys.path.insert(0,'/home/user/quran/scripts'); sys.path.insert(0,'/home/user/quran/scripts/munawi')
import takhrij_natural as TN
from nk import nk
fy=json.load(open('../cmp/fy_sh.json'))
EXP={'ق':['خ','م'],'4':['د','ن','ت','ه'],'3':['د','ن','ت']}; GRADE={'صح','ض','ح'}
GR=re.compile(r'\(([^()]*)\)')
def syms(g):
    o=[]
    for t in g.split():
        t=TN.ALIAS.get(t,t).translate(TN.DIG)
        if t in GRADE: continue
        s=TN.segment(t)
        if s: o+=s
    return o
def ex(l):
    o=set()
    for x in l: o.update(EXP.get(x,[x]))
    return o
isg=lambda g: all(t in GRADE for t in g.split())
def grade_of(raw):
    m=GR.findall(raw); 
    return m[-1].strip() if m and isg(m[-1]) else ''
files=sys.argv[1:]
res={}
for f in files:
    for x in json.load(open(f,encoding='utf8')): res[x['n']]=x
skel=lambda t:' '.join(nk(GR.sub(' ',t)))
cls=collections.defaultdict(list); info={}
for n,x in res.items():
    if not x.get('decode'): cls['noline'].append(n); continue
    R=x['ours']; D=x['decode']
    og=[m.group(1) for m in GR.finditer(R) if syms(m.group(1))]; dgall=[m.group(1) for m in GR.finditer(D)]
    dg=[g for g in dgall if syms(g)]; dg=dg[-len(og):] if len(dg)>=len(og) else dg
    aligned = bool(skel(R)) and (skel(R) in skel(D) or skel(D).endswith(skel(R)[-25:]))
    O=ex([s for g in og for s in syms(g)]); Dd=ex([s for g in dg for s in syms(g)])
    M=ex([s for m in GR.finditer(fy.get(str(n),'')[:260]) for s in syms(m.group(1).split(' عن')[0])])
    gr_o=grade_of(R); gr_d=grade_of(D)
    k=None
    if not aligned: k='unaligned'
    elif O==Dd: k='model=ours'
    elif M and Dd==M: k='model=munawi!=ours'
    elif M and O==M: k='ours=munawi!=model'
    else: k='three_way'
    cls[k].append(n); info[n]=(R,D,k,gr_o,gr_d)
    if k=='model=ours' and gr_o!=gr_d and gr_d: cls['grade_differs'].append(n)
print({k:len(v) for k,v in cls.items()})
json.dump({'cls':cls,'res':{str(n):res[n] for n in res}},open('classified.json','w'),ensure_ascii=False)
