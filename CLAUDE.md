# تعليمات لـClaude في هذا المستودع (الباحث القرآني)

هذا المستودع هو **مصدر محتوى** تطبيق الباحث القرآني (الويب + Android). التطبيقات المثبَّتة تقرأ `content/manifest.json` عند كل فتح وتنزّل ما تغيّر، فأي تعديل على `content/` يصل إلى **كل النسخ** تلقائياً.

## تعديل المحتوى (طلبات المالك: تصحيح نص، إضافة مرجع، حذف…)
استخدم **دائماً** الأداة، ولا تحرّر ملفات `content/*.json` يدوياً (لأنها تحدّث الإصدار والبصمة SHA-256 والعدد وتتحقق وتدفع commit واحداً):
```bash
node scripts/content.mjs list                                   # الأدوات
node scripts/content.mjs content_status '{}'                    # الإصدار والتبويبات
node scripts/content.mjs search_entries '{"tab":"jami","query":"إنما الأعمال"}'      # يعطي رقم المدخل index
node scripts/content.mjs update_entry '{"tab":"jami","index":0,"fields":{"text":"…"}}'
node scripts/content.mjs add_tab '{"id":"adhkar","label":"الأذكار","entries":[{"ref":"…","text":"…","explanation":"…"}]}'
node scripts/content.mjs add_entries '{"tab":"amthal","entries":[{"ref":"…","text":"…"}]}'
```
تدفع الأداة commit إلى `main` وتشغّل فحص السلامة. بعدها تصل التعديلات إلى التطبيقات عند فتحها (قد يتأخر ظهورها بضع دقائق بسبب تخزين GitHub المؤقت). أضف إلى رسالة الـcommit سطري الإسناد المطلوبين في الجلسة (متغير البيئة `COMMIT_TRAILER` يضيفهما تلقائياً).

أنواع التبويبات وحقولها: `content/SCHEMA.md`. المرجع الجديد = `add_tab` بنوع `generic` (حقول المدخل: `ref`, `text`, `explanation`).

## قواعد صارمة
- **لا تختلق نصاً**: لا نصّ حديث ولا آية ولا بيت ولا رقماً ولا حكماً. أضف فقط ما قدّمه المالك أو ما تنقله من مصدر سمّاه، وانقله كما هو. إن لم تكن متأكداً فاسأل.
- الجامع الصغير: تُعرض الرموز والدرجات كما طُبعت في الكتاب بلا إضافة.
- لا تغيّر رقم `version` يدوياً ولا تدفع بالقوة (`--force`).
- لا تضع أسراراً (توكنات/مفاتيح) في المستودع أو في رسائل المحادثة.
- في كود التطبيق: واجهة عربية RTL، خط Dubai Bold لكل النصوص عدا الآيات (Amiri Quran). لا ذكر لأسماء الكتب والمراجع في واجهة التطبيق.

## الاختبارات (قبل دفع تغيير في الكود)
`npm ci && npm run build` ثم `NODE_PATH=$(npm root -g) node tests/e2e.mjs`، و`node mcp-server/test.mjs`، و`node tests/content_cli.mjs`، و`node scripts/validate_content.mjs`.

## بناء APK
يتم تلقائياً عبر GitHub Actions (`.github/workflows/android.yml`) عند تغيير كود التطبيق، وينشر الملف في Releases باسم `apk-latest`.
