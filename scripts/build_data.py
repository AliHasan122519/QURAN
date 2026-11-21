"""Build the Qur'an and al-Jami' al-Saghir data files into content/ (registered in content/manifest.json).
Inputs (data/raw): quran-cloud-quran.json, jami_parsed.json
Run: python3 -I scripts/build_data.py"""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
import takhrij_natural as TN
R = 'data/raw'
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‎‏]')
def first_letter(t):
    t = DIAC.sub('', t); t = re.sub('[إأآٱ]', 'ا', t)
    m = re.search('[ء-ي]', t); return m.group(0) if m else ''
LETTER_NAMES = {'ا':'الهمزة','ب':'الباء','ت':'التاء','ث':'الثاء','ج':'الجيم','ح':'الحاء','خ':'الخاء','د':'الدال','ذ':'الذال','ر':'الراء','ز':'الزاي','س':'السين','ش':'الشين','ص':'الصاد','ض':'الضاد','ط':'الطاء','ظ':'الظاء','ع':'العين','غ':'الغين','ف':'الفاء','ق':'القاف','ك':'الكاف','ل':'اللام','م':'الميم','ن':'النون','ه':'الهاء','و':'الواو','ي':'الياء'}
# Quran: [surah, ayah, text]
q = json.load(open(f'{R}/quran-cloud-quran.json', encoding='utf8'))
surahs = [{'n': s['id'], 'name': s['name'], 'tr': s['transliteration'], 'type': s['type'], 'count': s['total_verses']} for s in q]
qa = [[s['id'], v['id'], v['text']] for s in q for v in s['verses']]
# The text is verified against the official digital text of the King Fahd Complex (KFGQPC Hafs v18, data/ref/hafsData_v18.json); where it differs the official text is used.
_k = json.load(open('data/ref/hafsData_v18.json', encoding='utf8'))
_K = {(r['sora'], r['aya_no']): re.sub('[\u00a0\u200f ]*[\u0660-\u0669]+\\s*$', '', r['aya_text']).strip() for r in _k}
assert len(_K) == 6236 and all((x[0], x[1]) in _K for x in qa), 'verse numbering differs from the official text'
_n = lambda t: t.replace('\u0640', '')
_fixed = 0
for x in qa:
    if _n(x[2]) != _n(_K[(x[0], x[1])]): x[2] = _K[(x[0], x[1])]; _fixed += 1
print('verses replaced by the official KFGQPC text:', _fixed)
CL.publish('quran', 'القرآن الكريم', 'quran', {'surahs': surahs, 'a': qa}, len(qa))
# Jami' al-Saghir
j = json.load(open(f'{R}/jami_parsed.json', encoding='utf8'))
# Unreadable OCR noise (stray characters / symbol soup) is kept out of the search data but saved for review in data/jami_excluded.json.
AR_WORD = re.compile(r'^[\u0621-\u064A\u064B-\u065F\u0670]{2,}[،,.؛:؟!»«"()\-]*$')
def is_noise(r):
    if 'noise_by_reference' in r.get('flags', []): return True   # matches nothing in the digital text and has no takhrij
    toks = r['t'].split()
    if not toks: return True
    q = sum(1 for t in toks if AR_WORD.match(t)) / len(toks)
    return q < 0.5 or (len(toks) < 2 and r['cov'] < 0.5)
excluded = [r for r in j if not r.get('verified') and is_noise(r)]
json.dump([{'page': r['page'], 'text': r['t'], 'takhrij': r['k']} for r in excluded], open('data/jami_excluded.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
j = [r for r in j if r.get('verified') or not is_noise(r)]
rows = []
for r in j:
    for f_ in ('t', 'k'): r[f_] = re.sub(r'[\u200B-\u200F\u202A-\u202E\uFEFF]', '', r[f_])
    L = first_letter(r['t'])
    tier = 'v' if r.get('verified') else ('h' if r['cov'] >= 0.9 else ('m' if r['cov'] >= 0.75 else 'l'))
    rows.append([r['page'], L, r['t'], r['k'], r['sym'], r['g'], tier, 1 if r['mahla'] else 0, r.get('n') or 0])
# The takhrij is written in plain words (the owner's request) instead of the printed symbols: index 3 = the words, index 9 = the takhrij exactly as printed.
# Entries whose takhrij the machine reading lost / merged / garbled were read by eye from the printed pages: data/jami_takhrij_fixes.json.
FIX = json.load(open('data/jami_takhrij_fixes.json', encoding='utf8'))['fixes']; used = set(); bad = []
for row in rows:
    f_ = FIX.get(str(row[8]))
    if f_:
        assert row[0] == f_['page'], ('fix on another page', row[8])
        if f_.get('cut'):
            assert row[2].rstrip().endswith(f_['cut']), ('text to cut not found', row[8]); row[2] = row[2].rstrip()[:-len(f_['cut'])].rstrip()
        if f_.get('mv'): row[2] = row[2].rstrip() + ' ' + f_['mv']
        if f_.get('t'): row[2] = f_['t']; row[1] = first_letter(row[2])
        row[3] = f_['k']; used.add(str(row[8]))
        gm = re.search(r'\(\s*(صح|ض|ح)(\s+ح)?\s*\)\s*$', f_['k'].strip())          # the grade follows the corrected takhrij
        row[5] = (gm.group(1) + (' ح' if gm.group(2) else '')) if gm else ''
    if re.search(r'(?:^|[\s(])صح(?:ـ)?[\s،,]+\(?ح\)?\s*\)?\s*$', row[3].strip()): row[5] = 'صح ح'      # the print gives both «صح ح»
    nat, pr = TN.natural(row[3], none=bool(f_ and f_.get('none')))
    if f_ and 'natural' in f_: nat, pr = f_['natural'], []
    if pr: bad.append((row[8], row[3], pr))
    row.append(row[3]); row[3] = nat
assert used == set(FIX), ('fixes not used', set(FIX) - used)
assert not bad, ('takhrij with something that is not a symbol of the key (add it to data/jami_takhrij_fixes.json after reading the printed page):', bad[:10])
CL.publish('jami', 'السنة النبوية', 'hadith', {'letters': LETTER_NAMES, 'h': rows}, len(rows))
meta = {'quran_ayat': sum(len(x['verses']) for x in q), 'jami_entries': len(rows), 'jami_excluded_noise': len(excluded), 'jami_pages': 592,
        'jami_tiers': {t: sum(1 for r in rows if r[6] == t) for t in 'vhml'}, 'jami_verified_pages': len(set(r[0] for r in rows if r[6] == 'v'))}
os.makedirs('data/raw', exist_ok=True); json.dump(meta, open('data/meta.json', 'w', encoding='utf8'), ensure_ascii=False); print(meta)
