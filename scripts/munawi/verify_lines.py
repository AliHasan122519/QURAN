"""Second reading of the takhrij lines with the line recogniser + scoring of competing readings (ours vs al-Munawi) on the line image.
usage: verify.py LEADS.json OUT.json [first last]"""
import sys, os, subprocess, csv, io, re, tempfile, json, math, collections
sys.path.insert(0,'/home/user/quran/scripts'); sys.path.insert(0,'/home/user/quran/scripts/munawi')
import torch, torch.nn as nn, crnn as C
import takhrij_natural as TN
from nk import nk
from rapidfuzz import fuzz
from PIL import Image
torch.set_num_threads(1)
MP='/tmp/claude-0/-home-user/8907d1ac-af27-5fdc-884f-50315362f320/scratchpad/jami_crnn3.pt'
ck=torch.load(MP); chars=ck['chars']; cid={c:i+1 for i,c in enumerate(chars)}; net=C.Net(len(chars)); net.load_state_dict(ck['state']); net.eval()
PDF='/home/user/sunnah-sense-finder/public/assets/al-jami-al-saghir.pdf'
d=json.load(open('/home/user/quran/content/jami.json',encoding='utf8'))['h']; by={r[8]:r for r in d}
fy=json.load(open('/tmp/claude-0/-home-user-quran/8907d1ac-af27-5fdc-884f-50315362f320/scratchpad/cmp/fy_sh.json'))
leads=json.load(open(sys.argv[1])); 
if len(sys.argv)>3: leads=[l for l in leads if int(sys.argv[3])<=l['page']<=int(sys.argv[4])]
ctc=nn.CTCLoss(blank=0,zero_infinity=True,reduction='none')
def page_lines(page,tmp):
    subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','300','-gray','-png','-singlefile',PDF,tmp+'/p'],check=True)
    tsv=subprocess.run(['tesseract',tmp+'/p.png','-','-l','ara','--psm','6','tsv'],capture_output=True,text=True,env=dict(os.environ,OMP_THREAD_LIMIT='1')).stdout
    rows=list(csv.DictReader(io.StringIO(tsv),delimiter='\t',quoting=csv.QUOTE_NONE)); lines=[r for r in rows if r['level']=='4' and int(r['width'])>80]
    im=Image.open(tmp+'/p.png').convert('L'); out=[]; imgs=[]
    for i,r in enumerate(lines):
        x,y,w,h=int(r['left']),int(r['top']),int(r['width']),int(r['height'])
        c=im.crop((max(0,x-10),max(0,y-10),min(im.width,x+w+150),min(im.height,y+h+10))); p=f'{tmp}/l{i}.png'; c.save(p); imgs.append((p,C.load_img(p),(x,y,w,h)))
    with torch.no_grad():
        for i in range(0,len(imgs),8):
            x,_=C.batchify([t for _,t,_ in imgs[i:i+8]]); logp=net(x); dec=C.decode(logp,chars)
            for k,(p,t,b) in enumerate(imgs[i:i+8]): out.append({'path':p,'box':b,'text':dec[k],'logp':logp[k,:math.ceil(t.shape[2]/4)].clone()})
    return out
def nll(L,s):
    s=re.sub(r'\s+',' ',s)
    if any(c not in cid for c in s): return 1e9
    tgt=torch.tensor([cid[c] for c in s]); lp=L['logp']
    return float(ctc(lp[:,None,:],tgt,torch.tensor([lp.shape[0]]),torch.tensor([len(s)])))
GR=re.compile(r'\(([^()]*)\)')
KEYS=set(TN.FULL)|{'٣','٤'}
def is_symgroup(g): 
    ts=[t for t in g.split()]
    return bool(ts) and all((t in KEYS or t in ('صح','ض','ح') or (TN.segment(TN.ALIAS.get(t,t).translate(TN.DIG)) is not None)) for t in ts[:3])
SH=os.environ.get('SHARD','0/1').split('/'); SH=(int(SH[0]),int(SH[1]))
res=[]; bypage=collections.defaultdict(list)
for l in leads: bypage[l['page']].append(l)
for page in [p for p in sorted(bypage) if p%SH[1]==SH[0]]:
    tmp=tempfile.mkdtemp(); L=page_lines(page,tmp)
    for l in bypage[page]:
        n=l['n']; r=by[n]; raw=r[9]
        target=re.sub(r'[()]','',raw)
        best=max(range(len(L)),key=lambda i:fuzz.partial_ratio(' '.join(nk(target)[:8]),' '.join(nk(L[i]['text']))) ) if L else None
        sc=fuzz.partial_ratio(' '.join(nk(target)[:8]),' '.join(nk(L[best]['text']))) if best is not None else 0
        rec={'n':n,'page':page,'ours':raw,'munawi':l.get('munawi','')[:100],'line_score':sc,'line_text':L[best]['text'] if best is not None else '','crop':None}
        if best is not None and sc>=80:
            D=L[best]['text']; rec['decode']=D
            fg=[' '.join(TN.segment(t) and [t] or []) for t in []]
            # alternative group strings: from ours, from al-Munawi's paragraph
            alts=set()
            for m in GR.finditer(raw): alts.add(m.group(1).strip())
            for m in GR.finditer(fy.get(str(n),'')[:260]):
                g=m.group(1).split(' عن')[0].strip()
                if g and is_symgroup(g): alts.add(g)
            groups=[m for m in GR.finditer(D) if is_symgroup(m.group(1))]
            base=nll(L[best],D); rec['base_nll']=round(base,2); changes=[]
            for gi,m in enumerate(groups):
                cur=m.group(1).strip(); cands={cur}
                for a in alts:
                    if a!=cur and TN_dist(cur,a)<=3 if False else a!=cur: cands.add(a)
                sc2={}
                for c in cands:
                    s=D[:m.start(1)]+c+D[m.end(1):]; sc2[c]=round(nll(L[best],s),2)
                order=sorted(sc2.items(),key=lambda x:x[1]); changes.append({'group_in_decode':cur,'scores':order[:5]})
            rec['groups']=changes
            # keep the line crop for manual look
            dst=f'/tmp/claude-0/-home-user-quran/8907d1ac-af27-5fdc-884f-50315362f320/scratchpad/vl/crops/{n}.png'; os.makedirs(os.path.dirname(dst),exist_ok=True)
            Image.open(L[best]['path']).save(dst); rec['crop']=dst
        res.append(rec)
    print('page',page,len(bypage[page]),flush=True)
json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
