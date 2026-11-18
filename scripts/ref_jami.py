"""Parses the digital text of al-Jami' al-Saghir (data/ref/jamic_saghir.txt, an OpenITI file of the Dar al-Fikr edition: hadith text only, numbered 1..10031)
into {number: text}. Used ONLY to check and correct the reading of the scanned book, entry by entry, by printed number."""
import re, json, sys
def parse(path='data/ref/jamic_saghir.txt'):
    t = open(path, encoding='utf8').read().split('#META#Header#End#', 1)[1]
    lines = [re.sub(r'^(# |~~)', '', l).strip() for l in t.split('\n')]
    txt = ' '.join(l for l in lines if l)
    txt = re.sub(r'PageV\d+P\d+|\bms\d+\b', ' ', txt); txt = re.sub(r'باب: حرف \S+', ' ', txt)
    out = {}
    ms = [m for m in re.finditer(r'(?<![\d/])(\d{1,5})\s*-\s', txt) if 1 <= int(m.group(1)) <= 10031]
    # the markers of the real entries are the longest strictly increasing run of numbers (years and other numbers inside the text fall out of it)
    import bisect
    tails, idx, prev = [], [], [-1] * len(ms)
    for k, m in enumerate(ms):
        n = int(m.group(1)); pos = bisect.bisect_left(tails, n)
        if pos == len(tails): tails.append(n); idx.append(k)
        else: tails[pos] = n; idx[pos] = k
        prev[k] = idx[pos - 1] if pos else -1
    chain, k = [], idx[-1]
    while k != -1: chain.append(k); k = prev[k]
    keep = [ms[k] for k in reversed(chain)]
    for i, m in enumerate(keep):
        end = keep[i + 1].start() if i + 1 < len(keep) else len(txt)
        out[int(m.group(1))] = re.sub(r'\s+', ' ', txt[m.end():end]).strip()
    return out
if __name__ == '__main__':
    d = parse(); print(len(d), 'entries; last', max(d)); json.dump(d, open('data/ref/jamic_saghir.json', 'w', encoding='utf8'), ensure_ascii=False)
