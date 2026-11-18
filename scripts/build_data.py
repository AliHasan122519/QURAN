"""Build the Qur'an and al-Jami' al-Saghir data files into content/ (registered in content/manifest.json).
Inputs (data/raw): quran-cloud-quran.json, jami_parsed.json
Run: python3 -I scripts/build_data.py"""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
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
CL.publish('quran', 'القرآن الكريم', 'quran', {'surahs': surahs, 'a': qa}, len(qa))
# Jami' al-Saghir
j = json.load(open(f'{R}/jami_parsed.json', encoding='utf8'))
# Unreadable OCR noise (stray characters / symbol soup) is kept out of the search data but saved for review in data/jami_excluded.json.
AR_WORD = re.compile(r'^[\u0621-\u064A\u064B-\u065F\u0670]{2,}[،,.؛:؟!»«"()\-]*$')
def is_noise(r):
    toks = r['t'].split()
    if not toks: return True
    q = sum(1 for t in toks if AR_WORD.match(t)) / len(toks)
    return q < 0.5 or (len(toks) < 2 and r['cov'] < 0.5)
excluded = [r for r in j if not r.get('verified') and is_noise(r)]
json.dump([{'page': r['page'], 'text': r['t'], 'takhrij': r['k']} for r in excluded], open('data/jami_excluded.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
j = [r for r in j if r.get('verified') or not is_noise(r)]
rows = []
for r in j:
    L = first_letter(r['t'])
    tier = 'v' if r.get('verified') else ('h' if r['cov'] >= 0.9 else ('m' if r['cov'] >= 0.75 else 'l'))
    rows.append([r['page'], L, r['t'], r['k'], r['sym'], r['g'], tier, 1 if r['mahla'] else 0, r.get('n') or 0])
CL.publish('jami', 'السنة النبوية', 'hadith', {'letters': LETTER_NAMES, 'h': rows}, len(rows))
meta = {'quran_ayat': sum(len(x['verses']) for x in q), 'jami_entries': len(rows), 'jami_excluded_noise': len(excluded), 'jami_pages': 592,
        'jami_tiers': {t: sum(1 for r in rows if r[6] == t) for t in 'vhml'}, 'jami_verified_pages': len(set(r[0] for r in rows if r[6] == 'v'))}
os.makedirs('data/raw', exist_ok=True); json.dump(meta, open('data/meta.json', 'w', encoding='utf8'), ensure_ascii=False); print(meta)
