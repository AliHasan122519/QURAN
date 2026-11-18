"""Builds the «الأمثال» tab from «الأمثال العامية» (أحمد تيمور باشا; public-domain text, see AMTHAL_SOURCE_NOTES.md).
Input: data/amthal/amthal_parsed.json (made by scripts/parse_amthal.py from the digital text in data/amthal/).
Output: content/amthal.json  [chapter, proverb, explanation]  + manifest (version, SHA-256, count).  usage: python3 -I scripts/build_amthal.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
E = json.load(open('data/amthal/amthal_parsed.json', encoding='utf8'))
rows = [[e['chapter'], e['proverb'], e['explanation']] for e in E if e['proverb'].strip()]
CL.publish('amthal', 'الأمثال', 'generic', {'h': rows}, len(rows))
