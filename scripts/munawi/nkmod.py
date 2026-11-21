import csv, re, json, sys, numpy as np, zlib
csv.field_size_limit(10**9)
MARK=re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def nk(t):
    t=MARK.sub('',t); t=re.sub('[إأآٱ]','ا',t); t=t.replace('ى','ي').replace('ة','ه')
    return re.sub(r'[^ء-ي ]',' ',t).split()
