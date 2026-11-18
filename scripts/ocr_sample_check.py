"""Compare OCR readings with a hand-checked sample. The reference text below was transcribed by me from the page IMAGES of the supplied PDF
(page 40: entries printed as 549-558; page 7: first entry). It is a SMALL sample; it measures word accuracy only after removing tashkeel.
usage: python3 -I scripts/ocr_sample_check.py"""
import re, difflib, json
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‎‏]')
def toks(s):
    s = DIAC.sub('', s); s = re.sub('[إأآٱ]', 'ا', s).replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي').replace('ة', 'ه')
    return re.findall('[ء-ي]+', s)
GT = {
 40: """إذا جامع أحدكم أهله فليصدقها ثم إذا قضى حاجته قبل أن تقضى حاجتها فلا يعجلها حتى تقضى حاجتها عب ع عن أنس
إذا جامع أحدكم امرأته فلا تنح حتى تقضي حاجتها كما يحب أن يقضي حاجته عد عن طلق ض
إذا جامع أحدكم زوجته أو جاريته فلا ينظر إلى فرجها فإن ذلك يورث العمى بقي بن مخلد عد عن ابن عباس قال ابن الصلاح جيد الإسناد
إذا جامع أحدكم فلا ينظر إلى الفرج فإنه يورث العمى ولا يكثر الكلام فإنه يورث الخرس الأزدي في الضعفاء والخليلي في مشيخته فر عن أبي هريرة ض
إذا جعلت إصبعيك في أذنيك سمعت خرير الكوثر قط عن عائشة ض
إذا جلستم فاخلعوا نعالكم تستريح أقدامكم البزار عن أنس ض
إذا جلست في صلاتك فلا تتركن الصلاة علي فإنها زكاة الصلاة قط عن بريدة ض
إذا جمرتم الميت فأوتروا حب ك عن جابر
إذا جهل على أحدكم وهو صائم فليقل أعوذ بالله منك إني صائم ابن السني عن أبي هريرة صح
إذا حاك في نفسك شيء فدعه حم حب ك عن أبي أمامة""",
 7: """إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى الله ورسوله فهجرته إلى الله ورسوله ومن كانت هجرته إلى دنيا يصيبها أو امرأة ينكحها فهجرته إلى ما هاجر إليه ق 4 عن عمر بن الخطاب حل قط في غرائب مالك عن أبي سعيد ابن عساكر في أماليه عن أنس الرشيد العطار في جزء من تخريجه عن أبي هريرة""",
}
def score(page, folder):
    gt = toks(GT[page]); ocr = toks(open(f'{folder}/{page:04d}.txt', encoding='utf8').read())
    sm = difflib.SequenceMatcher(None, gt, ocr, autojunk=False); hit = sum(b.size for b in sm.get_matching_blocks())
    return hit, len(gt)
out = {}
for folder in ('data/ocr', 'data/ocr_best', 'data/ocr_500', 'data/ocr_selected'):
    try: r = {p: score(p, folder) for p in GT}
    except FileNotFoundError: continue
    h = sum(v[0] for v in r.values()); t = sum(v[1] for v in r.values()); out[folder] = {'matched_words': h, 'reference_words': t, 'word_accuracy': round(h / t, 3), 'per_page': {p: round(v[0] / v[1], 3) for p, v in r.items()}}
    print(folder, out[folder])
json.dump(out, open('data/ocr_sample_check.json', 'w'), ensure_ascii=False, indent=1)
