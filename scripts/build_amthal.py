"""Builds the «الأمثال» tab from «الأمثال العامية» (أحمد تيمور باشا; public-domain text, see AMTHAL_SOURCE_NOTES.md) and «مجمع الأمثال» (الميداني).
Input: data/amthal/amthal_parsed.json (made by scripts/parse_amthal.py from the digital text in data/amthal/).
Output: content/amthal.json  [chapter, proverb, explanation]  + manifest (version, SHA-256, count).  usage: python3 -I scripts/build_amthal.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
E = json.load(open('data/amthal/amthal_parsed.json', encoding='utf8'))
import re
def fix_expl(t):
    t = re.sub(r'(?<=[.»:؛])\s+\d{1,3}\s*$', '', t.strip())            # a footnote number of the printed book left at the end
    t = re.sub(r'\s+([:،؛؟])', r'\1', t); return re.sub(r'\s+', ' ', t).strip()
FIX = {                                                                       # quotation marks the digital text left unpaired (checked against the sentence)
    'الجوز محرف عن الزوج': [('زوج أمك.»', 'زوج أمك.')],
    'يضرب للكناية عن المدة القليلة': [('فيها كلا ولا وقد شاع', 'فيها كلا ولا» وقد شاع')],
    'ويروى: «الكتكوت»': [('افتخار ا.ه. والشهاب', 'افتخار ا.ه.» والشهاب'), ('الألبا: 8 «', 'الألبا: «')],
    'لأن معاشرة مثله تحمل على الظن': [('المريب المتهم.» وفي', 'المريب المتهم. وفي')]}
def fix_row(e):
    x = fix_expl(e['explanation'])
    for k, subs in FIX.items():
        if x.startswith(k):
            for a, b in subs: x = x.replace(a, b, 1)
    return x
rows = [[e['chapter'], re.sub(r'\s+([:،؛؟])', r'\1', e['proverb']).strip(), fix_row(e)] for e in E if e['proverb'].strip()]
# + «مجمع الأمثال» (الميداني): the proverbs of the classical book, each with its explanation as printed (data/amthal/majma_parsed.json, scripts/parse_majma.py)
if os.path.exists('data/amthal/majma_parsed.json'):
    M = json.load(open('data/amthal/majma_parsed.json', encoding='utf8'))
    rows += [[e['chapter'], e['proverb'], e['explanation']] for e in M]
CL.publish('amthal', 'الأمثال', 'generic', {'h': rows}, len(rows))
