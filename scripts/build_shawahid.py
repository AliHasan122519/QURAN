"""Builds the «أبيات الاستشهاد» tab: [heading, «first hemistich … second hemistich», '', source(s)].  Input data/shawahid/verses_parsed.json (scripts/parse_shawahid.py).
usage: python3 -I scripts/build_shawahid.py"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
V = json.load(open('data/shawahid/verses_parsed.json', encoding='utf8'))
rows = []
for e in V:
    ref = e['ref']
    if re.match(r'^(?:و?أنشد|وأنشد|الكتاب|الشاهد|الباب|فصل)', ref) or len(ref) > 70: ref = ''     # «وأنشد بعده، وهو الإنشاد الثالث»، «الكتاب الثاني»، «الشاهد الخامس»: a running number, not a title
    ref = re.sub(r'\s+', ' ', ref).strip()
    rows.append([ref, f"{e['a']} … {e['b']}", '', ' · '.join(e['srcs'])])
CL.publish('shawahid', 'أبيات الاستشهاد', 'generic', {'h': rows}, len(rows), extra={'card': 'verse', 'smart': 'full',
    'placeholder': 'اكتب كلمة بالفصحى أو العامية… مثال: سفينة، قارب، سيف، أسد، ناقة', 'hint': 'اكتب الكلمة ويفهم التطبيق مرادفاتها وما يقابلها بالعامية، وتظهر الأبيات التي ورد فيها المعنى.'})
