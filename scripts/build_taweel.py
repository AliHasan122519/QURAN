"""Registers the «التأويل العميق» entry of the «المزيد» menu (content/taweel.json: one row, the introduction). The feature itself is the app's code (src/lib/taweel.ts):
it reads the dream, takes the symbols, and speaks the books' own sentences about them to the dreamer (without naming a book or an author) according to his age and marital state.
The entry is placed first in the menu.   usage: python3 -I scripts/build_taweel.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
def main():
    rows = [['التأويل العميق', 'اكتب رؤياك أو رموزها، واختر عمرك وحالتك الاجتماعية، فيأتيك التأويل من أصول علم التعبير وكتبه.', '', '', '']]
    CL.publish('taweel', 'التأويل العميق', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'deep', 'menu': 'التأويل العميق', 'placeholder': 'اكتب هنا', 'hint': 'اكتب رؤياك فيأتيك تأويلها من الأصول.'})
    m = json.load(open('content/manifest.json', encoding='utf8')); tabs = m['tabs']; t = next(x for x in tabs if x['id'] == 'taweel'); tabs.remove(t)
    first = next(i for i, x in enumerate(tabs) if x.get('drawer')); tabs.insert(first, t)       # first among the side-menu entries
    json.dump(m, open('content/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); open('content/manifest.json', 'a').write('\n')
if __name__ == '__main__': main(); print('ok')
