"""Optional: add the proverbs book («الأمثال العامية» لأحمد تيمور باشا) to the app.
No authorised dataset was available when phase 1 was built, so the tab «الأمثال» reports that the book is not included.
To activate it, put a JSON file at data/raw/amthal.json  ->  [{"book": "...", "author": "...", "proverb": "...", "explanation": "..."}, ...]
(`explanation` may be empty) and run:  python3 -I scripts/build_amthal.py   (or add the entries through the MCP server: tool add_entries)
The tab then searches it with the same engine and shows the «شرح» button for entries that have an explanation.
Make sure you hold the right to use the text before publishing it."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
src = 'data/raw/amthal.json'
if not os.path.exists(src): sys.exit('missing ' + src)
rows = json.load(open(src, encoding='utf8'))
h = [[(r.get('book', '') + ' ' + r.get('author', '')).strip(), r['proverb'].strip(), (r.get('explanation') or '').strip()] for r in rows if r.get('proverb', '').strip()]
CL.publish('amthal', 'الأمثال', 'generic', {'h': h}, len(h))
