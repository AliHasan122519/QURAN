import re, json, sys, collections
sys.path.insert(0,'scripts'); sys.path.insert(0,'scripts/munawi')
import takhrij_natural as TN
from fayd import sym_tokens
d=json.load(open('content/jami.json',encoding='utf8'))['h']; by={r[8]:r for r in d}
fy=json.load(open(sys.argv[1]))
EXP={'ق':['خ','م'],'4':['د','ن','ت','ه'],'3':['د','ن','ت']}
def expand(l): 
    o=[]
    for x in l: o+=EXP.get(x,[x])
    return o
def groups_syms(text):
    out=[]
    for m in re.finditer(r'\(([^()]*)\)',text): out+=sym_tokens(m.group(1))
    return expand(out)
res=[]
for n,t in fy.items():
    r=by.get(int(n))
    if not r: continue
    A=set(groups_syms(r[9])); B=set(groups_syms(t[:420]))
    kind='equal' if A==B else 'theirs_subset' if B<A else 'ours_subset' if A<B else 'different'
    res.append((int(n),r[6],kind,sorted(A),sorted(B)))
cc=collections.defaultdict(collections.Counter)
for n,t,k,a,b in res: cc[t][k]+=1
for t in 'vhml': print(t,dict(cc[t]))
json.dump(res,open(sys.argv[2],'w'))
