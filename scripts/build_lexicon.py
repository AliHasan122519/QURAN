"""Build a word-frequency lexicon (original spelling, tashkeel removed) used ONLY as a spell-check dictionary for the OCR text.
Sources: the Qur'anic text (quran-cloud) and the Arabic hadith corpus of the `hadith` npm package (all 16 collections), counted word by word.
Only the frequency list is kept (data/raw/lexicon.json); none of those texts is stored in or shown by the app.
usage: python3 -I scripts/build_lexicon.py /path/to/hadith.db"""
import sqlite3, json, re, sys, collections
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ‎‏]')
W = re.compile(r'[ء-يٱ]+')
def words(t):
    t = DIAC.sub('', t).replace('ٱ', 'ا')
    return W.findall(t)
cnt = collections.Counter()
for s in json.load(open('data/raw/quran-cloud-quran.json', encoding='utf8')):
    for v in s['verses']: cnt.update(words(v['text']))
c = sqlite3.connect(sys.argv[1])
for (txt,) in c.execute("select narrator_prefix || ' ' || content || ' ' || narrator_postfix from hadith"): cnt.update(words(txt or ''))
lex = {w: n for w, n in cnt.items() if len(w) >= 1}
json.dump(lex, open('data/raw/lexicon.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('lexicon words:', len(lex), 'tokens counted:', sum(cnt.values()))
