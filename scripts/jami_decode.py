"""Shared helpers for al-Jami' al-Saghir entries: symbol key (transcribed from printed pp. 5-6 and checked against the page images) and the split of an entry
into hadith text / takhrij / symbols / grade mark."""
import re
# key of symbols: transcribed from printed pp. 5-6 of the supplied PDF (checked against page images)
SYMBOLS = {
 'خد':'البخاري في الأدب','تخ':'البخاري في التاريخ','حب':'ابن حبان في صحيحه','خ':'البخاري','م':'مسلم','ق':'متفق عليه (البخاري ومسلم)',
 'د':'أبو داود','ت':'الترمذي','ن':'النسائي','ه':'ابن ماجه','4':'أبو داود والنسائي والترمذي وابن ماجه','3':'أبو داود والنسائي والترمذي',
 'حم':'أحمد في مسنده','عم':'عبد الله بن أحمد في زوائده','ك':'الحاكم (المستدرك)','طب':'الطبراني في الكبير','طس':'الطبراني في الأوسط',
 'طص':'الطبراني في الصغير','ص':'سعيد بن منصور في سننه','ش':'ابن أبي شيبة','عب':'عبد الرزاق في الجامع','ع':'أبو يعلى في مسنده',
 'قط':'الدارقطني','فر':'الديلمي في مسند الفردوس','حل':'أبو نعيم في الحلية','هب':'البيهقي في شعب الإيمان','هق':'البيهقي في السنن',
 'عد':'ابن عدي في الكامل','عق':'العقيلي في الضعفاء','خط':'الخطيب',
 'طبس':'الطبراني (رمز «طبس» مطبوع في المتن وغير وارد في مفتاح الرموز)'}
GRADES = {'صح':'صحيح','ح':'حسن','ض':'ضعيف'}
SYM_FIX = {'هـ':'ه','ه':'ه','٤':'4','٣':'3'}


paren_re = re.compile(r'\(\s*([^()]{1,24}?)\s*\)')
def decode_text(text):
    """-> (matn, takhrij, symbols, grade)"""
    text = re.sub(r'\s+', ' ', text).strip()
    matn, takhrij, syms, grade = text, '', [], ''
    for m in paren_re.finditer(text):
        toks = [SYM_FIX.get(t, t) for t in re.split(r'\s+', m.group(1).strip())]
        toks = [t for t in toks if t]
        if toks and all(t in SYMBOLS or t in ('4', '3') for t in toks) and not syms and m.start() > 5:
            syms = toks; matn = text[:m.start()].strip(); takhrij = text[m.start():].strip(); break
    gm = re.search(r'\(\s*(صح|ص ح|ضص|ض|ح)\s*\)\s*(?:والله أعلم)?\.?\s*$', text)
    if gm:
        g = gm.group(1).replace(' ', '')
        grade = {'صح': 'صح', 'ضص': 'ض', 'ض': 'ض', 'ح': 'ح'}[g]
        if not takhrij: takhrij = text[gm.start():].strip(); matn = text[:gm.start()].strip()
    return matn, takhrij, syms, grade
