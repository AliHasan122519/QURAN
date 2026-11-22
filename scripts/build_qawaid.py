"""Builds the list «قواعد علم التعبير» of the «المزيد» menu (content/qawaid.json) out of data/qawaid/excerpts.json,
which scripts/extract_qawaid.py copies word for word from the books of dream interpretation (nothing is written here but the arrangement).
Each entry:  [ref = the rule's name,  text = the passages that state the rule (one per line: «النص<TAB>اسم الكتاب»),
              explanation = the passages that give examples (same shape),  source = '',  by = the group of the rule].
usage: python3 -I scripts/build_qawaid.py   (after python3 -I scripts/extract_qawaid.py)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
def lines(ps): return '\n'.join(f"{p['text']}\t{p['book']}" for p in ps)
def main():
    ex = json.load(open('data/qawaid/excerpts.json', encoding='utf8'))
    rows = [[e['title'], lines(e['rule']), lines(e['ex']), '', e['group']] for e in ex]
    CL.publish('qawaid', 'قواعد علم التعبير', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'rule', 'menu': 'قواعد علم التعبير', 'placeholder': 'اكتب هنا',
               'hint': 'أصول التأويل وضوابطه كما نصّت عليها كتب التعبير: الاشتقاق، والتصحيف، والتشبيه، والضد، والمثل، والشعر…، مع أمثلتها.'})
    return rows
if __name__ == '__main__':
    rows = main(); print(len(rows), 'rules')
