"""«التأويل العميق» (content/taweel.json): الصف الأول مقدّمة القائمة، وما بعده «أصول التأويل» (data/taweel/rules.py): رمزٌ، وما يدلّ عليه، ووجه ذلك، ودليله.
 - الدليل نصّ حرفي يُجلب من بيانات التطبيق نفسها (الجامع الصغير، أحاديث الرؤيا، القرآن)، ويتوقف البناء إن لم يوجد حرفاً بحرف.
 - لكل قاعدة «anchors»: عبارة حرفية من كتاب من «الكتب» تنصّ على معناها؛ ويتوقف البناء إن لم توجد.
المحرّك نفسه (src/lib/taweel.ts) يركّب منها تأويلاً متسلسلاً بصيغة المعبِّر. usage: python3 -I scripts/build_taweel.py"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'taweel'))
import content_lib as CL
from rules import RULES, ACTS, COMBOS
from families import FAMILIES
from lexicon import ROOTS, CATS, COLORS, AS, QS
MARKS = re.compile('[ً-ٰٟۖ-ۭـ]')
def fold(s, deep=False):
    s = MARKS.sub('', s); s = re.sub('[أإآٱ]', 'ا', s).replace('ى', 'ي').replace('ئ', 'ي').replace('ؤ', 'و').replace('ة', 'ه')
    s = re.sub(r'\s+', ' ', re.sub(r'[^ء-ي ]', ' ', s)).strip()
    return s.replace('ء', '').replace('ا', '').replace(' ', '') if deep else s            # (the Uthmani spelling keeps or drops alefs differently from the plain one: compare without them)
def fold_map(s):
    """the folded text and, for every folded character, its place in the original"""
    out, idx = [], []
    for i, ch in enumerate(s):
        if ch == '\u0670': ch = 'ا'                                                 # the dagger alef is an alef
        elif MARKS.match(ch): continue
        c = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ئ': 'ي', 'ؤ': 'و', 'ة': 'ه'}.get(ch, ch)
        if c in ('ء', 'ا'): continue                                            # the Uthmani spelling (ءَامَنُواْ، هَٰذِه) against the plain one (آمنوا، هذه): letters compared without alefs
        if not re.match('[ء-ي]', c): continue                                   # (spaces too: Uthmani spelling joins «يا أيها» into one word)
        if c == ' ' and out and out[-1] == ' ': continue
        out.append(c); idx.append(i)
    return ''.join(out), idx
def load(name): return json.load(open(f'content/{name}.json', encoding='utf8'))
def sources():
    J = [r[2] for r in load('jami')['h']]; R = [r[1] for r in load('ruyahadith')['h']]; Q = [r[2] for r in load('quran')['a']]
    A = [r[1] for r in load('amthal')['h']]; Sh = [r[1] for r in load('shawahid')['h']]; Al = [r[3] + ' … ' + r[4] for r in load('alfiya')['h']]
    return {'jami': J, 'ruya': R, 'quran': Q, 'amthal': A, 'shawahid': Sh, 'alfiya': Al}
def resolve(ev, S):
    """the quotation, word for word, as the source prints it"""
    q = ev['q']
    for t in S[ev['src']]:
        if ev['src'] == 'quran':                                     # the verse keeps its marks: locate by letters, cut the original
            f, idx = fold_map(t); n = fold(q, True); k = f.find(n)
            if k >= 0:
                end = idx[k + len(n) - 1] + 1
                while end < len(t):                                                  # the marks and the alef that belong to the last word (it was skipped in the comparison)
                    if MARKS.match(t[end]): end += 1
                    elif t[end] in 'اٱأإآ' and (end + 1 >= len(t) or t[end + 1] == ' ' or MARKS.match(t[end + 1])): end += 1
                    else: break
                start = idx[k]
                while start > 0 and (t[start - 1] in 'اٱأإآ' or MARKS.match(t[start - 1])): start -= 1      # the alef that opens the first word
                return t[start:end]
        elif q in t: return q
    raise SystemExit(f'evidence not found in {ev["src"]}: {q[:60]}')
def check_anchor(a, books, qawaid):
    n = fold(a['needle'])
    if 'qawaid' in a:                                                       # a rule of the method (word for word from the books, in «قواعد علم التعبير»)
        if any(r[0] == a['qawaid'] and n in fold(r[1]) for r in qawaid): return
        raise SystemExit(f'method anchor not found in qawaid {a["qawaid"]}: {a["needle"][:60]}')
    for r in books:
        if a['book'] in (r[3] or '') and n in fold(r[1]): return
    raise SystemExit(f'anchor not found in {a["book"]}: {a["needle"][:60]}')
def main():
    S = sources(); books = load('books')['h']; qawaid = load('qawaid')['h']; rows = [['التأويل العميق', 'اكتب رؤياك أو رموزها، واختر عمرك وحالتك الاجتماعية، فيأتيك التأويل من أصول علم التعبير وكتبه.', '', '', '']]
    for r in RULES:
        assert r['anchors'], r['id']
        for a in r['anchors']: check_anchor(a, books, qawaid)
        rule = {k: r[k] for k in ('id', 'stems', 'name', 'kind', 'family', 'verdict', 'm') if k in r}
        for k in ('acts', 'why', 'dua', 'owner', 'play', 'tail'):
            if k in r: rule[k] = r[k]
        rule['ev'] = [{'t': e['t'], 'q': resolve(e, S)} for e in r.get('ev', [])]
        if 'alts' in r: rule['alts'] = [{**{k: v for k, v in a.items() if k != 'ev'}, 'ev': [{'t': e['t'], 'q': resolve(e, S)} for e in a.get('ev', [])]} for a in r['alts']]
        rows.append([r['id'], json.dumps(rule, ensure_ascii=False, separators=(',', ':')), '', '', 'rule'])
    for c in COMBOS:
        assert c['anchors'], c['id']
        for a in c['anchors']: check_anchor(a, books, qawaid)
        o = {k: c[k] for k in ('id', 'm', 'all', 'name', 'family', 'verdict', 'why')}; o['ev'] = [{'t': e['t'], 'q': resolve(e, S)} for e in c['ev']]
        rows.append([c['id'], json.dumps(o, ensure_ascii=False, separators=(',', ':')), '', '', 'combo'])
    # the general lexicon: roots (الاشتقاق), analogies (القياس والتشبيه والضد), colours; every one with a method rule of the books and a verse that is checked word for word
    METHOD_RULE = {'الاشتقاق': AS, 'القياس': QS, 'التشبيه': QS, 'الضد': {'qawaid': 'التأويل بالضد والمقلوب', 'needle': 'في البكاء إنه فرح'}}
    for m_, a_ in METHOD_RULE.items(): check_anchor(a_, books, qawaid)
    for r_, cn, rd, fam_, q, ex in ROOTS:
        o = {'t': 'root', 'r': r_, 'cn': cn, 'rd': rd, 'fam': fam_, 'ex': ex, 'ev': [{'t': 'آية', 'q': resolve({'t': 'آية', 'src': 'quran', 'q': q}, S)}]}
        rows.append(['جذر ' + r_, json.dumps(o, ensure_ascii=False, separators=(',', ':')), '', '', 'gen'])
    for id_, words, rd, fam_, m_, why, qs in CATS:
        o = {'t': 'cat', 'id': id_, 'words': words, 'rd': rd, 'fam': fam_, 'm': m_, 'why': why, 'ev': [{'t': 'آية', 'q': resolve({'t': 'آية', 'src': 'quran', 'q': q}, S)} for q in qs]}
        rows.append(['باب ' + id_, json.dumps(o, ensure_ascii=False, separators=(',', ':')), '', '', 'gen'])
    for id_, words, rd, fam_, why, q in COLORS:
        o = {'t': 'color', 'id': id_, 'words': words, 'rd': rd, 'fam': fam_, 'why': why, 'ev': [{'t': 'آية', 'q': resolve({'t': 'آية', 'src': 'quran', 'q': q}, S)}]}
        rows.append(['لون ' + id_, json.dumps(o, ensure_ascii=False, separators=(',', ':')), '', '', 'gen'])
    fams = {k: {'label': v['label'], 'maal': v['maal'], 'ev': [{'t': e['t'], 'q': resolve(e, S)} for e in v['ev']]} for k, v in FAMILIES.items()}
    rows.append(['الأبواب', json.dumps(fams, ensure_ascii=False, separators=(',', ':')), '', '', 'fams'])
    acts = ['الأفعال', json.dumps(ACTS, ensure_ascii=False, separators=(',', ':')), '', '', 'acts']
    rows.append(acts)
    CL.publish('taweel', 'التأويل العميق', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'deep', 'menu': 'التأويل العميق', 'placeholder': 'اكتب هنا', 'hint': 'اكتب رؤياك فيأتيك تأويلها من الأصول.'})
    m = json.load(open('content/manifest.json', encoding='utf8')); tabs = m['tabs']; t = next(x for x in tabs if x['id'] == 'taweel'); tabs.remove(t)
    first = next(i for i, x in enumerate(tabs) if x.get('drawer')); tabs.insert(first, t)       # first among the side-menu entries
    json.dump(m, open('content/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); open('content/manifest.json', 'a').write('\n')
    return len(RULES)
if __name__ == '__main__': print(main(), 'rules ok')
