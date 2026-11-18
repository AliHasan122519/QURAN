# الباحث القرآني — الويب + تطبيق Android + خادم MCP

بحث عربي دقيق في القرآن الكريم والسنة النبوية (الجامع الصغير) والألفية الوردية، ومعها أي مراجع تُضاف لاحقاً.

```
content/        ← بيانات التطبيق (المصدر الوحيد) + manifest.json — انظر content/SCHEMA.md
src/            ← تطبيق الويب (React) الذي يعمل داخل Android عبر Capacitor
android/        ← مشروع Android (Capacitor) — يُبنى APK تلقائياً على GitHub Actions
mcp-server/     ← خادم MCP تضيفه إلى Claude لتعديل المحتوى وإضافة المراجع
scripts/        ← سكربتات بناء البيانات (OCR والتدقيق) والتحقق
.github/workflows/  ← بناء APK، وفحص المحتوى
```

## كيف يصل أي تعديل إلى كل النسخ؟
1. تطلب من Claude (عبر الـMCP) إضافة مرجع أو تصحيح نص ← يكتب الخادم **commit واحداً** في `content/` (الملف + `manifest.json` بإصدار أعلى وبصمة SHA-256).
2. فحص آلي على GitHub يتأكد من سلامة المحتوى.
3. كل تطبيق مثبَّت يفحص `manifest.json` عند فتحه، ينزّل ما تغيّر، يتحقق من البصمة، يحفظه في ذاكرة الجهاز ويعيد الفهرسة فوراً. يعمل بعدها بلا إنترنت من آخر نسخة نزّلها.
4. التغيير في **كود** التطبيق (لا المحتوى) يبني GitHub Actions منه APK جديداً وينشره في «Releases» (وسم `apk-latest`)، وتظهر في التطبيقات القديمة شريطة «يتوفر إصدار جديد».

## الإعداد (مرة واحدة)
**١) المستودع.** أنشئ مستودعاً **عاماً (Public)** على GitHub وارفع هذا المشروع إليه (فرع `main`). ضروري أن يكون عاماً ليُنزّل التطبيق المحتوى بلا مفاتيح.

**٢) صلاحيات Actions.** في المستودع: Settings ← Actions ← General ← *Workflow permissions* ← **Read and write permissions** ثم Save. بعد أول push يُبنى الـAPK ويظهر في **Releases ← apk-latest** (حوالي ٥–١٠ دقائق). ثبّته على الهاتف (يلزم السماح بالتثبيت من مصدر خارجي).

**٣) مفتاح توقيع خاص (موصى به).** النسخ تُثبَّت فوق بعضها فقط إذا وُقّعت بالمفتاح نفسه. المستودع يحوي مفتاحاً تطويرياً مفتوحاً للتجربة؛ استبدله بمفتاحك قبل نشر التطبيق لغيرك:
```bash
keytool -genkeypair -keystore my.jks -alias release -keyalg RSA -keysize 2048 -validity 36500
base64 -w0 my.jks   # الصق الناتج في سر المستودع KEYSTORE_BASE64
```
وأضف الأسرار `KEYSTORE_PASSWORD` و`KEY_ALIAS` و`KEY_PASSWORD` (Settings ← Secrets and variables ← Actions). (تغيير المفتاح لاحقاً يستلزم إلغاء تثبيت النسخة القديمة مرة واحدة.)

**٤) خادم MCP على Cloudflare (مجاني).**
```bash
cd mcp-server && npm install
# عدّل GITHUB_REPO في wrangler.toml إلى "owner/name"
npx wrangler login
npx wrangler secret put GITHUB_TOKEN   # توكن fine-grained: هذا المستودع فقط، Contents: Read and write
npx wrangler secret put MCP_SECRET     # نص عشوائي طويل (٣٢ حرفاً فأكثر): openssl rand -hex 24
npx wrangler deploy                    # يطبع الرابط https://quran-search-mcp.<حسابك>.workers.dev
```

## نشر الـMCP من الجوال فقط (بلا حاسوب) — Netlify
`mcp-server/` فيه دالة Netlify جاهزة (`functions/mcp.mjs`). على الجوال ومن المتصفح فقط:
1. **توكن GitHub:** github.com ← صورتك ← Settings ← (أسفل القائمة) Developer settings ← Personal access tokens ← Fine-grained tokens ← Generate new token. المستودع: *Only select repositories* ← `QURAN`. الصلاحية: Repository permissions ← **Contents: Read and write**. انسخ التوكن.
2. **Netlify:** app.netlify.com ← Add new project ← Import an existing project ← GitHub ← اختر `QURAN`. في الإعدادات: **Base directory = `mcp-server`** وباقي الحقول كما هي ← Deploy.
3. **المتغيرات:** Project configuration ← Environment variables ← أضف: `GITHUB_TOKEN` (الصق التوكن، وفعّل *Contains secret values*) و`MCP_SECRET` (نص عشوائي من ٣٢ حرفاً فأكثر) و`GITHUB_REPO` = `AliHasan122519/QURAN` و`GITHUB_BRANCH` = `main`. ثم Deploys ← Trigger deploy ← Deploy project.
4. **الإضافة إلى Claude:** من المتصفح (وضع «موقع سطح المكتب») claude.ai ← Settings ← Connectors ← Add custom connector ← الرابط `https://<اسم-موقعك>.netlify.app/mcp/<MCP_SECRET>`.

**٥) الإضافة إلى Claude (طريق Cloudflare).** Settings ← Connectors ← *Add custom connector* ← الرابط: `https://quran-search-mcp.<حسابك>.workers.dev/mcp/<MCP_SECRET>` (الجزء الأخير هو سرّك؛ لا تشاركه).
بديل محلي (Claude Desktop / Claude Code): `GITHUB_TOKEN=… GITHUB_REPO=owner/name node mcp-server/stdio.js` كخادم stdio.

## أدوات الـMCP
`content_status` · `search_entries` · `get_entry` · `update_entry` · `add_entries` · `delete_entries` · `add_tab` · `update_tab` · `reorder_tabs` · `remove_tab` · `set_apk_notice`
مثال: «أضف تبويباً اسمه الأذكار من النص التالي…» أو «صحّح الحديث الذي نصه… إلى…».

## التطوير والاختبار
```bash
npm ci
npm run dev                         # الويب محلياً
npm run content:validate            # تحقق manifest/SHA/الأعداد
node mcp-server/test.mjs            # اختبار خادم MCP (٣٣ فحصاً) على GitHub وهمي
npm run build && npm test           # اختبارات الواجهة (Playwright)، ويلزمها NODE_PATH=$(npm root -g)
node tests/update.mjs               # اختبار سلسلة التحديث كاملة: MCP ← ملفات ← تطبيق يستلم ويتحقق ويعمل دون إنترنت
```
بناء APK محلياً (يلزم JDK 17 وAndroid SDK): `npm run build:android && cd android && ./gradlew assembleRelease`.

## حدود
- التحديث التلقائي للمحتوى لا يغيّر **كود** التطبيق؛ تغيير الواجهة يحتاج APK جديداً (يُبنى تلقائياً ويصل إشعاره).
- التطبيق يعتمد خدمة `raw.githubusercontent.com`، وقد يتأخر ظهور التعديل بضع دقائق (تخزين مؤقت لدى GitHub).
- بيانات الجامع الصغير مستخرجة آلياً من صور ومدقَّقة جزئياً (انظر `AL_JAMI_AL_SAGHIR_SOURCE_NOTES.md`).
