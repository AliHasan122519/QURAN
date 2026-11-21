import re, json, sys
MARK=re.compile('[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]')
def nk(t):
    t=MARK.sub('',t); t=re.sub('[إأآٱ]','ا',t); t=t.replace('ى','ي').replace('ة','ه')
    return re.sub(r'[^ء-ي ]',' ',t).split()
