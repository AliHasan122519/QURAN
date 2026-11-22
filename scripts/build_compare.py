"""Builds the list «مقارنة المعبِّرين» of the «المزيد» menu (content/muqaranat.json): for a symbol, what EACH reference book says of it, one beside the other, each passage word for word with its book named.
A passage belongs to a symbol when the symbol is its subject — the same test the «الكتب» tab uses (the symbol is among the first four words of the passage: «ومن رأى ملكاً…», «الملك يدل على…»).
Only the choice of the symbols (data/compare/symbols.txt) is mine; the passages are the books' own, in the books' own order, at most 4 per book. A symbol enters the list when at least two books speak of it.
usage: python3 -I scripts/build_compare.py"""
import json, re, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def norm(s):
    s = MARKS.sub('', s); s = re.sub('[ٱأإآ]', 'ا', s); return s.replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')
def tokens(s): return re.findall('[ء-ي]+', norm(s))
def core(w): return re.sub(r'^(?:وال|فال|بال|كال|لل|ولل|ال|و)', '', w)           # the one-letter prefixes are left alone: «لحية» (a beard) is not «حية» (a snake)
def same(w, q): return w == q or (len(q) >= 3 and len(w) >= 3 and (w.startswith(q) or q.startswith(w)) and abs(len(w) - len(q)) <= 2)
ORDER = ['الإشارات في علم العبارات', 'القادري في التعبير', 'البدر المنير في علم التعبير', 'تعطير الأنام في تعبير المنام', 'منتخب الكلام في تفسير الأحلام', 'تعبير الرؤيا (ابن غنام المقدسي)', 'الإشارة إلى علم العبارة']
PER_BOOK = 3
def main():
    B = json.load(open('content/books.json', encoding='utf8'))['h']
    syms = [l.strip() for l in open('data/compare/symbols.txt', encoding='utf8') if l.strip() and not l.startswith('#')]
    idx = []
    for r in B:
        if r[3] not in ORDER or len(r[1]) < 25: continue
        idx.append((r[3], [core(w) for w in tokens(r[1])[:4]], r[1]))
    rows = []
    for s in syms:
        q = [core(w) for w in tokens(s)]
        per = collections.OrderedDict((b, []) for b in ORDER)
        for n, (b, tk, text) in enumerate(idx):
            if all(any(same(w, x) for w in tk) for x in q):
                pos = min(i for i, w in enumerate(tk) if any(same(w, x) for x in q)); per[b].append((pos, n, text))
        have = [(b, [t for _, _, t in sorted(v)[:PER_BOOK]]) for b, v in per.items() if v]       # the passages whose first words are the symbol come first
        if len(have) < 2: continue
        rows.append([s, '\n'.join(f'{t}\t{b}' for b, v in have for t in v), '', '', 'حرف ' + (s[0] if s[0] not in 'أإآ' else 'ا')])
    CL.publish('muqaranat', 'مقارنة المعبِّرين', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'rule', 'menu': 'مقارنة المعبِّرين', 'placeholder': 'اكتب هنا',
               'hint': 'رمز واحد وما قاله فيه كل كتاب، جنباً إلى جنب.', 'unit': 'رمزاً', 'l1': 'ما قالته الكتب فيه', 'l2': '', 'sub': 'ما قاله كل كتاب في الرمز نفسه'})
    return rows
if __name__ == '__main__':
    rows = main(); print(len(rows), 'symbols')
    c = collections.Counter(); 
    for r in rows: c[len({l.split('\t')[1] for l in r[1].split('\n')})] += 1
    print('books per symbol:', dict(sorted(c.items())))
