"""Builds the tab «المساعد الذكي» (content/assistant.json): the bank of phrases in which the assistant of the app speaks (data/assistant/phrases.json, a Saudi colloquial voice).
Each row is [category, phrase, '']; the assistant (src/lib/assistant.ts) picks a phrase of the category at random.  The tab is the FIRST item of the side menu «المزيد».
The assistant's knowledge is not here: it answers only from the references the app already holds (books, their texts and contents, the symbols dictionary, the interpreters).
usage: python3 -I scripts/build_assistant.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
P = json.load(open('data/assistant/phrases.json', encoding='utf8'))
rows = [[cat, ph, ''] for cat, lst in P.items() for ph in lst]
# the topics of the discussions (data/assistant/topics.json): which words call each, and what to look for in which reference — quotations only, no text of knowledge
TOPICS = json.load(open('data/assistant/topics.json', encoding='utf8'))
assert len({t['id'] for t in TOPICS}) == len(TOPICS) and all(set(t.get('follow', [])) <= {x['id'] for x in TOPICS} for t in TOPICS)
rows += [['topic', json.dumps(t, ensure_ascii=False, separators=(',', ':')), ''] for t in TOPICS]
assert all('{' not in ph or ph.count('{') == ph.count('}') for _, ph, _ in rows)
CL.publish('assistant', 'المساعد الذكي', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'assistant', 'menu': 'المساعد الذكي', 'sub': 'اسألني عن أي كتاب أو رمز، وأجاوبك من المراجع اللي في التطبيق بس.', 'placeholder': 'اكتب سؤالك'})
p = 'content/manifest.json'; m = json.load(open(p, encoding='utf8'))
a = [t for t in m['tabs'] if t['id'] == 'assistant']; rest = [t for t in m['tabs'] if t['id'] != 'assistant']
at = next((i for i, t in enumerate(rest) if t.get('drawer')), len(rest))           # the first of the side menu
m['tabs'] = rest[:at] + a + rest[at:]
json.dump(m, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1); open(p, 'a').write('\n')
print('assistant is item', at + 1, 'of', len(m['tabs']))
