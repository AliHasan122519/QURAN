"""Copies, word for word, the sentences that the classical biographical dictionaries say about the interpreters named in the «رؤى وتعبيرها» list
-> data/muabbirun/excerpts.json  (read by scripts/build_more_lists.py).
Sources (OpenITI digital texts; point OITI at the folder that holds them, default /tmp/claude-0/oiti):
  سير أعلام النبلاء للذهبي (0748Dhahabi.SiyarAclamNubala.Shamela0010906)      — the Companions and Successors
  الأعلام للزركلي (1396KhayrDinZirikli.Aclam.Shamela0012286)                    — the authors of the books and Ja'far al-Sadiq
Each excerpt is a whole sentence (or a whole paragraph) of the entry of that person, only the footnote numbers and the page marks are removed.
Nothing is paraphrased. The script fails if a sentence it was asked for is not found in the entry.   usage: python3 -I scripts/extract_muabbirun.py"""
import re, os, json, sys
OITI = os.environ.get('OITI', '/tmp/claude-0/oiti')
SIYAR = f'{OITI}/0750AH/data/0748Dhahabi/0748Dhahabi.SiyarAclamNubala/0748Dhahabi.SiyarAclamNubala.Shamela0010906-ara1.mARkdown'
ALAM = f'{OITI}/1400AH/data/1396KhayrDinZirikli/1396KhayrDinZirikli.Aclam/1396KhayrDinZirikli.Aclam.Shamela0012286-ara1.mARkdown'
S_NAME = 'سير أعلام النبلاء للذهبي'; A_NAME = 'الأعلام للزركلي'
def clean(t):
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\(\d+\)', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()
def load(path):
    return open(path, encoding='utf8', errors='ignore').read().split('\n')
def entry(L, heading_re, nth=0):
    """the paragraphs of the entry whose heading line matches heading_re (nth match)"""
    hits = [i for i, l in enumerate(L) if l.startswith('### ') and re.search(heading_re, l)]
    i = hits[nth]; out = []; cur = None
    for l in L[i + 1:]:
        if l.startswith('### '): break
        if l.startswith('# ') or l == '#': cur = [l[2:]]; out.append(cur)
        elif l.startswith('~~') and cur is not None: cur.append(l[2:])
    return [clean(' '.join(c)) for c in out if clean(' '.join(c))]
def entry_at(L, first_re):
    """the paragraphs of an entry of al-A'lam found by the first words of its text (its date line, just before, is kept)"""
    i = next(k for k, l in enumerate(L) if l.startswith('# ') and re.search(first_re, l))
    if re.match(r'^# \(.*ه', L[i - 1]): i -= 1
    out = []; cur = None
    for l in L[i:]:
        if l.startswith('### ') and out: break
        if l.startswith('# ') or l == '#': cur = [l[2:]]; out.append(cur)
        elif l.startswith('~~') and cur is not None: cur.append(l[2:])
    return [clean(' '.join(c)) for c in out if clean(' '.join(c))]
def pick(paras, start_re, cut_from=None, cut_to=None):
    for p in paras:
        if re.match(start_re, p):
            if cut_from:
                m = re.search(cut_from, p); p = p[m.start():] if m else p
            if cut_to:
                m = re.search(cut_to, p); p = p[:m.end()] if m else p
            return p
    raise SystemExit(f'not found: {start_re}')
LS = load(SIYAR); LA = load(ALAM)
people = []
def person(key, name, parts): people.append({'key': key, 'name': name, 'parts': parts})
def part(src, loc, text): return {'src': src, 'loc': loc, 'text': text}

# ---- سير أعلام النبلاء ----
P = entry(LS, r'محمد بن سيرين أبو بكر الأنصاري')
person('ابن سيرين', 'محمد بن سيرين', [
    part(S_NAME, 'ترجمة محمد بن سيرين', pick(P, r'الإمام، شيخ الإسلام، أبو بكر الأنصاري')),
    part(S_NAME, 'ترجمة محمد بن سيرين', pick(P, r'قال ابن شبرمة: دخلت على محمد بن سيرين')),
    part(S_NAME, 'ترجمة محمد بن سيرين', pick(P, r'قد جاء عن ابن سيرين في التعبير')),
    part(S_NAME, 'ترجمة محمد بن سيرين', pick(P, r'مات ابن سيرين لتسع مضين من شوال'))])
P = entry(LS, r'سعيد بن المسيب بن حزن القرشي')
person('سعيد بن المسيب', 'سعيد بن المسيب', [
    part(S_NAME, 'ترجمة سعيد بن المسيب', pick(P, r'ابن أبي وهب بن عمرو', cut_from=r'الإمام، العلم') + ' ' + pick(P, r'وسيد التابعين في زمانه')),
    part(S_NAME, 'ترجمة سعيد بن المسيب', pick(P, r'قال الواقدي: كان سعيد بن المسيب من أعبر الناس للرؤيا')),
    part(S_NAME, 'ترجمة سعيد بن المسيب', pick(P, r'وقال الهيثم بن عدي: مات في سنة أربع وتسعين') + ' ' + pick(P, r'وفيها أرخ وفاة ابن المسيب') + ' ' + pick(P, r'وما ذكر ابن سعد سواه'))])
P = entry(LS, r'أبو بكر الصديق خليفة رسول الله')
person('أبو بكر الصديق', 'أبو بكر الصديق رضي الله عنه', [
    part(S_NAME, 'ترجمة أبي بكر الصديق', pick(P, r'اسمه عبد الله -ويقال: عتيق- بن أبي قحافة')),
    part(S_NAME, 'ترجمة أبي بكر الصديق', pick(P, r'وقال محمد بن سيرين: كان أبو بكر أعبر هذه الأمة لرؤيا'))])
P = entry(LS, r'مسروق بن الأجدع')
person('مسروق', 'مسروق بن الأجدع', [
    part(S_NAME, 'ترجمة مسروق بن الأجدع', pick(P, r'الإمام، القدوة، العلم، أبو عائشة الوادعي')),
    part(S_NAME, 'ترجمة مسروق بن الأجدع', pick(P, r'قال أبو نعيم: مات سنة اثنتين وستين') + ' ' + pick(P, r'وقال يحيى بن بكير، وابن سعد، وابن نمير: مات سنة ثلاث وستين'))])
P = entry(LS, r'الحسن البصري أبو سعيد')
person('الحسن البصري', 'الحسن البصري', [
    part(S_NAME, 'ترجمة الحسن البصري', pick(P, r'هو: الحسن بن أبي الحسن يسار، أبو سعيد') + ' ' + pick(P, r'الأنصاري\.')),
    part(S_NAME, 'ترجمة الحسن البصري', pick(P, r'قال ابن علية: مات الحسن في رجب، سنة عشر ومائة'))])
P = entry(LS, r'عبد الله بن عباس البحر أبو العباس')
person('ابن عباس', 'عبد الله بن عباس رضي الله عنهما', [
    part(S_NAME, 'ترجمة عبد الله بن عباس', pick(P, r'حبر الأمة، وفقيه العصر، وإمام التفسير') + ' ' + pick(P, r'عم رسول الله -صلى الله عليه وسلم - العباس بن عبد المطلب', cut_to=r'العباس بن عبد المطلب')),
    part(S_NAME, 'ترجمة عبد الله بن عباس', pick(P, r'صحب النبي -صلى الله عليه وسلم - نحوا من ثلاثين شهرا'))])

# ---- الأعلام للزركلي ----
P = entry_at(LA, r'^# جعفر بن محمد الباقر بن علي زين العابدين')
person('جعفر الصادق', 'جعفر الصادق', [part(A_NAME, 'جعفر الصادق', p) for p in P])
P = entry_at(LA, r'^# أحمد بن عبد الرحمن بن عبد المنعم، أبو العباس شهاب الدين')
person('ابن نعمة النابلسي', 'ابن نعمة النابلسي (مؤلف «البدر المنير في علم التعبير»)', [part(A_NAME, 'ابن نعمة', P[0]), part(A_NAME, 'ابن نعمة', P[1] + ' ' + P[2])])
P = entry_at(LA, r'^# خليل بن شاهين الظاهري، غرس الدين')
person('ابن شاهين الظاهري', 'خليل بن شاهين الظاهري (مؤلف «الإشارات في علم العبارات»)', [
    part(A_NAME, 'ابن شاهين', P[0]),
    part(A_NAME, 'ابن شاهين', P[1] + P[2] + ' ' + pick(P, r'كان من المولعين بالبحث')),
    part(A_NAME, 'ابن شاهين', pick(P, r'\(زبدة كشف المماليك', cut_from=r'\(الإشارات إلى علم العبارات', cut_to=r'في تعبير الأحلام'))])
P = entry_at(LA, r'^# عبد الغني بن إسماعيل بن عبد الغني النابلسي')
person('عبد الغني النابلسي', 'عبد الغني النابلسي (مؤلف «تعطير الأنام في تعبير المنام»)', [
    part(A_NAME, 'عبد الغني النابلسي', P[0]),
    part(A_NAME, 'عبد الغني النابلسي', P[1] + P[2]),
    part(A_NAME, 'عبد الغني النابلسي', pick(P, r'وتوفي بها', cut_to=r'تعطير الأنام في تعبير المنام - ط "'))])
P = entry_at(LA, r'^# نصر بن يعقوب بن إبراهيم الدينوري')
person('نصر بن يعقوب الدينوري', 'نصر بن يعقوب الدينوري (مؤلف «التعبير القادري»)', [
    part(A_NAME, 'الدينوري', P[0]),
    part(A_NAME, 'الدينوري', pick(P, r'نصر بن يعقوب بن إبراهيم الدينوري', cut_to=r'من كبار الكتاب\.')),
    part(A_NAME, 'الدينوري', pick(P, r'نصر بن يعقوب بن إبراهيم الدينوري', cut_from=r'له تصانيف', cut_to=r'وفرغ منه في رمضان 399'))])
P = entry_at(LA, r'^# \.?إبراهيم بن يحيى بن غنام')
person('ابن غنام المقدسي', 'إبراهيم بن يحيى بن غنام (مؤلف «تعبير الرؤيا»)', [
    part(A_NAME, 'ابن غنام', P[0]),
    part(A_NAME, 'ابن غنام', pick(P, r'.?إبراهيم بن يحيى بن غنام', cut_to=r'المعلم على حروف المعجم - خ\)'))])
for pp in people:
    for x in pp['parts']: x['text'] = re.sub(r'\s+([.،؛:؟])', r'\1', re.sub(r'\s+', ' ', x['text'])).strip(' ؛')
os.makedirs('data/muabbirun', exist_ok=True)
json.dump(people, open('data/muabbirun/excerpts.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
for pp in people:
    print('==', pp['name'])
    for x in pp['parts']: print('   ', x['text'][:230])
