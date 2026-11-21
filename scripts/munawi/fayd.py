import re, json, sys, collections
sys.path.insert(0,'scripts'); sys.path.insert(0,'scripts/munawi')
import takhrij_natural as TN
import os; OD=os.environ.get('OITI','/tmp/claude-0/oiti')+'/1050AH/data/1031CabdRaufMunawi/1031CabdRaufMunawi.FaydQadir/'
KEYS=set(TN.FULL)|{'٣','٤'}
def sym_tokens(grp):
    res=[]
    for t in grp.split():
        if t=='عن' or (t.startswith('عن') and len(t)<=4): break
        t=TN.ALIAS.get(t,t).translate(TN.DIG)
        if t.startswith('و') and t[1:] in KEYS: t=t[1:]
        seg=TN.segment(t) if t not in ('صح','ض','ح') else None
        if seg: res+=seg
        else: res=res; 
    return res
def parse(fn):
    sec={}; cur=None; paras=None
    txt=open(OD+fn,encoding='utf8').read().split('\n')
    for l in txt:
        m=re.match(r'### \| (\d+) - ',l)
        if m: cur=int(m.group(1)); sec.setdefault(cur,[]); paras=None; continue
        if l.startswith('###'): continue
        if cur is None: continue
        if l.startswith('# '):
            l2=re.sub(r'ms\d+|PageV\d+P\d+','',l[2:]); paras=[l2]; sec[cur].append(paras)
        elif l.startswith('~~') and paras is not None: paras.append(re.sub(r'ms\d+|PageV\d+P\d+','',l[2:]))
    res={}
    for n,ps in sec.items():
        cands=[]
        for p in ps:
            t=' '.join(p).strip()
            m=re.match(r'\(([^()]*)\)',t)
            if not m: continue
            toks=m.group(1).split()
            # a takhrij paragraph: its first group starts with symbols
            lead=[]; 
            for x in toks:
                if x.startswith('عن') and len(x)<=4: break
                lead.append(x)
            if lead and TN.segment(TN.ALIAS.get(lead[0],lead[0]).translate(TN.DIG).lstrip('و') or 'x') and all((TN.segment(TN.ALIAS.get(x,x).translate(TN.DIG).lstrip('و')) or x in ('و',)) for x in lead[:2]):
                cands.append(t)
        if cands: res[n]=cands[0]
    return res
if __name__=='__main__':
    r=parse(sys.argv[1]); json.dump(r,open(sys.argv[2],'w'),ensure_ascii=False); print(len(r),'takhrij paragraphs')
    for n in (1,2,5,6,100,5000): print(n,r.get(n,'-')[:150])

def first_tk(ps):
    for p in ps:
        t=' '.join(p).strip(); m=re.match(r'\(([^()]*)\)',t)
        if not m: continue
        lead=[]
        for x in m.group(1).split():
            if x.startswith('عن') and len(x)<=4: break
            lead.append(x)
        nz=lambda x: TN.ALIAS.get(x,x).translate(TN.DIG).lstrip('و')
        if lead and TN.segment(nz(lead[0]) or 'x') and all((TN.segment(nz(x)) or x=='و') for x in lead[:2]): return t
def parse_inline(fn):
    cur=0; sec={}; paras=None
    for l in open(OD+fn,encoding='utf8'):
        l=l.rstrip('\n')
        if l.startswith('###'): continue
        if l.startswith('# ') and not l.startswith('# PageV'):
            body=re.sub(r'ms\d+|PageV\d+P\d+','',l[2:])
            m=None
            for mm in re.finditer(r'(?<![\d])(\d{1,5}) - \(',body):
                if cur+1<=int(mm.group(1))<=cur+3: m=mm; break
            if m: cur=int(m.group(1)); sec[cur]=[]; body=body[m.end()-1:]
            paras=[body]; 
            if cur in sec: sec[cur].append(paras)
        elif l.startswith('~~') and paras is not None: paras.append(re.sub(r'ms\d+|PageV\d+P\d+','',l[2:]))
    return {n:t for n,ps in sec.items() for t in [first_tk(ps)] if t}
