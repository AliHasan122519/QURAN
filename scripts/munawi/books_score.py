import json, re, sys, zlib, numpy as np, collections
sys.path.insert(0,'/home/user/quran/scripts'); sys.path.insert(0,'/tmp/claude-0/hd')
import takhrij_natural as TN
from nkmod import nk
K=4
idx=dict(np.load('/tmp/claude-0/hd/idx.npz'))
def h(ws): return zlib.crc32(' '.join(ws).encode())&0xffffffff
d=json.load(open('/home/user/quran/content/jami.json',encoding='utf8'))['h']
MAP={'خ':['bukhari'],'م':['muslim'],'ق':['bukhari','muslim'],'د':['abudawud'],'ت':['tirmidhi'],'ن':['nasai'],'ه':['ibnmajah'],'4':['abudawud','nasai','tirmidhi','ibnmajah'],'3':['abudawud','nasai','tirmidhi'],'حم':['ahmad'],'خد':['adab']}
GR=re.compile(r'\(([^()]*)\)')
def syms(raw):
    o=[]
    for m in GR.finditer(raw):
        for t in m.group(1).split():
            t=TN.ALIAS.get(t,t).translate(TN.DIG)
            if t in ('صح','ض','ح','؟'): continue
            s=TN.segment(t)
            if s: o+=s
    return o
res=[]
for r in d:
    ws=nk(r[2])
    sh=[h(ws[i:i+K]) for i in range(len(ws)-K+1)]
    if len(sh)<3: res.append((r[8],None)); continue
    a=np.array(sh,dtype=np.uint32)
    fr={b:float((v[np.minimum(np.searchsorted(v,a),len(v)-1)]==a).mean()) for b,v in idx.items()}
    res.append((r[8],fr))
json.dump(res,open('/tmp/claude-0/hd/scores.json','w'))
by={r[8]:r for r in d}
flag=[];ok=collections.Counter();tot=collections.Counter()
for n,fr in res:
    if not fr: continue
    r=by[n]; S=syms(r[9]); best=max(fr.values())
    for s in set(S):
        if s not in MAP: continue
        got=max(fr[b] for b in MAP[s]) if s not in ('4','3','ق') else min(fr[b] for b in MAP[s])
        tot[s]+=1
        if got>=0.4: ok[s]+=1
        elif best>=0.6 and max(fr[b] for b in MAP[s])<0.2: flag.append((n,r[6],s,round(got,2),max(fr,key=fr.get),round(best,2)))
print({s:(ok[s],tot[s]) for s in tot})
print(len(flag),collections.Counter(f[1] for f in flag))
json.dump(flag,open('/tmp/claude-0/hd/flag.json','w'))
for f in flag[:20]: print(f)
