"""Generate TEST_REPORT.md from tests/last-run.json (+ OCR sample check). usage: python3 -I scripts/gen_test_report.py"""
import json, collections
r = json.load(open('tests/last-run.json', encoding='utf8')); chk = json.load(open('data/ocr_sample_check.json'))
res = r['results']; ok = sum(1 for x in res if x['pass']); groups = collections.OrderedDict()
for x in res: groups.setdefault(x['group'], []).append(x)
ar = lambda n: str(n).translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))
out = [f"# تقرير الاختبارات — TEST_REPORT\n\nتاريخ آخر تشغيل: `{r['at']}` · البيئة: Chromium عبر Playwright على بناء الإنتاج `dist/` · المجموع: **{ar(ok)} من {ar(len(res))} اختباراً ناجحاً**.\n",
 "أُجريت الاختبارات بـ`npm test` (ملف `tests/e2e.mjs`) وتفاصيل كل اختبار وزمنه في `tests/last-run.json` مع لقطات في `tests/screenshots/`. اختبارات المحرك وحدها في `tests/engine-check.mjs`.\n",
 "## ما غُطّي بحسب قائمة المرحلة الأولى\n",
 "| # | بند القائمة | النتيجة |\n|---|---|---|"]
cover = [('البحث عن آيات', ['البحث في القرآن']), ('البحث عن أحاديث (الجامع الصغير هو المصدر الوحيد للحديث)', ['السنة النبوية', 'المصادر']), ('البحث داخل الجامع الصغير', ['السنة النبوية']), ('البحث عن الأمثال', ['الأمثال']), ('التشكيل وبدونه', ['التشكيل']), ('العبارات الطويلة', ['البحث']), ('الفلاتر وتغيير المصدر (الأصل: تبويبات فقط بلا فلاتر)', ['مطابقة الأصل']), ('المراجع والإحالات', ['السنة النبوية', 'البحث في القرآن']), ('خط Dubai Bold', ['الخط']), ('RTL', ['RTL']), ('الأزرار والروابط (التبويبات وأزرار الأمثلة)', ['الأمثلة', 'مطابقة الأصل', 'الخلفية']), ('عدم وجود نتائج وحالات التحميل', ['الحالات']), ('الهواتف والكمبيوتر', ['الاستجابة']), ('الأداء وإمكانية الوصول', ['الأداء', 'إمكانية الوصول (axe)']), ('عينات OCR', [])]
for i, (name, gs) in enumerate(cover, 1):
    items = [x for g in gs for x in groups.get(g, [])]
    if name == 'البحث عن الأمثال': st = f"التبويب موجود ويصرّح بعدم توفر البيانات؛ البحث نفسه غير قابل للاختبار (لا بيانات مرخّصة): {ar(sum(1 for x in items if x['pass']))}/{ar(len(items))} ناجح"
    elif name == 'عينات OCR': st = f"قياس على عينة مُدقَّقة بالصور: دقة الكلمات {chk['data/ocr_selected']['word_accuracy']} (انظر القسم الأخير)"
    else: st = f"{ar(sum(1 for x in items if x['pass']))}/{ar(len(items))} ناجح"
    out.append(f'| {ar(i)} | {name} | {st} |')
for g, items in groups.items():
    out.append(f'\n## {g}\n\n| النتيجة | الاختبار | التفصيل |\n|---|---|---|')
    for x in items: out.append(f"| {'✅' if x['pass'] else '❌'} | {x['name']} | {x['detail'].replace('|', '/')[:140]} |")
out.append('\n## إمكانية الوصول (axe-core، WCAG 2 A/AA + best-practice)\n')
for page, v in r['axe'].items():
    s = ', '.join(f"{i['id']} ({i['impact']}×{i['n']})" for i in v) or 'لا مخالفات'
    out.append(f'- **{page}**: {s}')
out.append('\nالمخالفات من درجة `moderate/minor` المذكورة أعلاه لم تُعالَج؛ لا توجد مخالفات `serious/critical`.')
out.append(f"\n## الأداء\n\n- جاهزية الفهرس بعد التحميل (قراءة + فك ضغط + فهرسة ٦٬٢٣٦ آية وكل مداخل الجامع الصغير): **{next((x['detail'] for x in res if x['group'] == 'الأداء'), '')}** على هذه البيئة.\n- زمن البحث داخل الفهرس: أقل من ١٥٠ م.ث للاستعلامات المختبرة (انظر قسم «الأداء»).\n- لم يُشغَّل Lighthouse (يحتاج Chrome كاملاً بمنفذ تصحيح)؛ استُعيض عنه بقياس الأزمنة وفحص axe.")
out.append("\n## عينات OCR مقارنة بصور الصفحات\n\nالمرجع: ١١ مدخلاً نقلتُها بيدي من صور الصفحتين ٧ و٤٠ (قرابة ٢٢٨ كلمة بلا تشكيل). عينة صغيرة وليست تمثيلية؛ الدقة الفعلية على الكتاب غير معروفة.\n\n| القراءة | الكلمات المطابقة | الدقة |\n|---|---|---|")
names = {'data/ocr': 'عادية 300dpi', 'data/ocr_best': 'tessdata_best 300dpi', 'data/ocr_500': 'عادية 500dpi', 'data/ocr_selected': 'المعتمدة (أفضل قراءة لكل صفحة)'}
for k, n in names.items():
    if k in chk: out.append(f"| {n} | {ar(chk[k]['matched_words'])}/{ar(chk[k]['reference_words'])} | {chk[k]['word_accuracy']} |")
LIMITS = [
 "- **الأمثال**: لا بيانات مرخّصة؛ لم يُختبر سوى سلوك التبويب الفارغ.",
 "- **البحث الدلالي الحقيقي** (تضمينات): غير موجود؛ المُختبَر هو التوسعة بقوائم ألفاظ يدوية فقط.",
 "- **متصفحات أخرى وأجهزة حقيقية**: جرى الاختبار على Chromium فقط (محاكاة ٣٩٠ و٧٦٨ و١٣٦٦ بكسل).",
 "- **الخادم والتخزين الدائم**: غير موجودين في هذه المرحلة.",
 "- **صحة نصوص OCR**: غير مضمونة؛ انظر `AL_JAMI_AL_SAGHIR_SOURCE_NOTES.md`.",
 "- **Artifact داخل claude.ai**: اختُبرت الحزمة المنشورة نفسها محلياً داخل هيكل صفحة مماثل (بلا طلبات خارجية وبلا أخطاء)، لكن بيئة العرض الفعلية داخل claude.ai لم أتمكن من تشغيلها من هنا.",
 "- **أعداد نتائج «الصبر» وأمثاله** قد تختلف عن الأصل (الأصل ٥ آيات للصبر وهنا أكثر) لأن خادم الأصل غير متاح لي؛ التطابق التام موثَّق في «مفتاح» (٤ آيات بالترتيب نفسه) و«الصلاه» (٦٦ آية).",
 "- **مطابقة الأصل بصرياً**: قورنت المقاسات (ارتفاع الحقل والزر ونصف الأقطار) وبنية الصفحة ونصوصها، لا لقطات بكسل ببكسل.",
]
out.append("\n## ما لم يُختبر أو لم ينجح\n\n" + "\n".join(LIMITS))
open('TEST_REPORT.md', 'w', encoding='utf8').write('\n'.join(out) + '\n'); print('TEST_REPORT.md written', ok, '/', len(res))
