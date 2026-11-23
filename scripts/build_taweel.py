"""«التأويل العميق» (content/taweel.json): الصف الأول مقدّمة القائمة، وما بعده «أصول التأويل» (data/taweel/rules.py): رمزٌ، وما يدلّ عليه، ووجه ذلك، ودليله.
 - الدليل نصّ حرفي يُجلب من بيانات التطبيق نفسها (الجامع الصغير، أحاديث الرؤيا، القرآن)، ويتوقف البناء إن لم يوجد حرفاً بحرف.
 - لكل قاعدة «anchors»: عبارة حرفية من كتاب من «الكتب» تنصّ على معناها؛ ويتوقف البناء إن لم توجد.
المحرّك نفسه (src/lib/taweel.ts) يركّب منها تأويلاً متسلسلاً بصيغة المعبِّر. usage: python3 -I scripts/build_taweel.py"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'taweel'))
import content_lib as CL
from rules import RULES, ACTS
MARKS = re.compile('[ً-ٰٟۖ-ۭـ]')
def fold(s, deep=False):
    s = MARKS.sub('', s); s = re.sub('[أإآٱ]', 'ا', s).replace('ى', 'ي').replace('ة', 'ه')
    s = re.sub(r'\s+', ' ', re.sub(r'[^ء-ي ]', ' ', s)).strip()
    return re.sub('ا+', 'ا', s.replace('ء', '')) if deep else s
def fold_map(s):
    """the folded text and, for every folded character, its place in the original"""
    out, idx = [], []
    for i, ch in enumerate(s):
        if ch == '\u0670': ch = 'ا'                                                 # the dagger alef is an alef
        elif MARKS.match(ch): continue
        c = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه'}.get(ch, ch)
        if c == 'ء' or (c == 'ا' and out and out[-1] == 'ا'): continue        # the Uthmani spelling (ءَامَنُواْ) against the plain one (آمنوا)
        if not re.match('[ء-ي]', c): c = ' '
        if c == ' ' and out and out[-1] == ' ': continue
        out.append(c); idx.append(i)
    return ''.join(out), idx
def load(name): return json.load(open(f'content/{name}.json', encoding='utf8'))
def sources():
    J = [r[2] for r in load('jami')['h']]; R = [r[1] for r in load('ruyahadith')['h']]; Q = [r[2] for r in load('quran')['a']]
    return {'jami': J, 'ruya': R, 'quran': Q}
def resolve(ev, S):
    """the quotation, word for word, as the source prints it"""
    q = ev['q']
    for t in S[ev['src']]:
        if ev['src'] == 'quran':                                     # the verse keeps its marks: locate by letters, cut the original
            f, idx = fold_map(t); n = fold(q, True); k = f.find(n)
            if k >= 0:
                end = idx[k + len(n) - 1] + 1
                while end < len(t) and MARKS.match(t[end]): end += 1                 # the marks that belong to the last letter
                return t[idx[k]:end]
        elif q in t: return q
    raise SystemExit(f'evidence not found in {ev["src"]}: {q[:60]}')
def check_anchor(a, books):
    n = fold(a['needle'])
    for r in books:
        if a['book'] in (r[3] or '') and n in fold(r[1]): return
    raise SystemExit(f'anchor not found in {a["book"]}: {a["needle"][:60]}')
def main():
    S = sources(); books = load('books')['h']; rows = [['التأويل العميق', 'اكتب رؤياك أو رموزها، واختر عمرك وحالتك الاجتماعية، فيأتيك التأويل من أصول علم التعبير وكتبه.', '', '', '']]
    for r in RULES:
        assert r['anchors'], r['id']
        for a in r['anchors']: check_anchor(a, books)
        rule = {k: r[k] for k in ('id', 'stems', 'name', 'kind', 'family', 'verdict') if k in r}
        for k in ('acts', 'why', 'dua', 'owner'):
            if k in r: rule[k] = r[k]
        rule['ev'] = [{'t': e['t'], 'q': resolve(e, S)} for e in r.get('ev', [])]
        rows.append([r['id'], json.dumps(rule, ensure_ascii=False, separators=(',', ':')), '', '', 'rule'])
    acts = ['الأفعال', json.dumps(ACTS, ensure_ascii=False, separators=(',', ':')), '', '', 'acts']
    rows.append(acts)
    CL.publish('taweel', 'التأويل العميق', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'deep', 'menu': 'التأويل العميق', 'placeholder': 'اكتب هنا', 'hint': 'اكتب رؤياك فيأتيك تأويلها من الأصول.'})
    m = json.load(open('content/manifest.json', encoding='utf8')); tabs = m['tabs']; t = next(x for x in tabs if x['id'] == 'taweel'); tabs.remove(t)
    first = next(i for i, x in enumerate(tabs) if x.get('drawer')); tabs.insert(first, t)       # first among the side-menu entries
    json.dump(m, open('content/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); open('content/manifest.json', 'a').write('\n')
    return len(RULES)
if __name__ == '__main__': print(main(), 'rules ok')
