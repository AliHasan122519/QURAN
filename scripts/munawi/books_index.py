import csv, re, json, sys, numpy as np, zlib
csv.field_size_limit(10**9)
MARK=re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def nk(t):
    t=MARK.sub('',t); t=re.sub('[إأآٱ]','ا',t); t=t.replace('ى','ي').replace('ة','ه')
    return re.sub(r'[^ء-ي ]',' ',t).split()
BASE='/tmp/claude-0/hd/Open-Hadith-Data/'
BOOKS={'bukhari':'Sahih_Al-Bukhari/sahih_al-bukhari_ahadith.utf8.csv','muslim':'Sahih_Muslim/sahih_muslim_ahadith.utf8.csv','abudawud':'Sunan_Abu-Dawud/sunan_abu-dawud_ahadith.utf8.csv','tirmidhi':'Sunan_Al-Tirmidhi/sunan_al-tirmidhi_ahadith.utf8.csv','nasai':'Sunan_Al-Nasai/sunan_al-nasai_ahadith.utf8.csv','ibnmajah':'Sunan_Ibn-Maja/sunan_ibn-maja_ahadith.utf8.csv','malik':'Maliks_Muwataa/maliks_muwataa_ahadith.utf8.csv','ahmad':'Musnad_Ahmad_Ibn-Hanbal/musnad_ahmad_ibn-hanbal_ahadith.utf8.csv','darimi':'Sunan_Al-Darimi/sunan_al-darimi_ahadith.utf8.csv'}
import os
K=4
def h(ws): return zlib.crc32(' '.join(ws).encode())&0xffffffff
out={}
for b,f in BOOKS.items():
    p=BASE+f
    if not os.path.exists(p):
        import glob; g=glob.glob(BASE+f.split('/')[0]+'/*ahadith.utf8.csv'); p=g[0] if g else None
    n=0; hs=set()
    for row in csv.reader(open(p,encoding='utf8')):
        ws=nk(row[-1]); n+=1
        for i in range(len(ws)-K+1): hs.add(h(ws[i:i+K]))
    out[b]=np.array(sorted(hs),dtype=np.uint32); print(b,n,len(hs),flush=True)
# Adab al-Mufrad from hadith-json
d=json.load(open('/tmp/claude-0/hd/hadith-json/db/by_book/other_books/aladab_almufrad.json',encoding='utf8'))
hs=set(); n=0
items=d['hadiths'] if isinstance(d,dict) else d
for x in items:
    t=x.get('arabic') or x.get('text') or ''
    ws=nk(t); n+=1
    for i in range(len(ws)-K+1): hs.add(h(ws[i:i+K]))
out['adab']=np.array(sorted(hs),dtype=np.uint32); print('adab',n,len(hs))
np.savez('/tmp/claude-0/hd/idx.npz',**out)
