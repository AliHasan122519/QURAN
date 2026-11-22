"""Builds the page «حول التطبيق» of the «المزيد» menu (content/about.json). The first row is the app's own description (the sentence of its home page); the other rows are short notes whose every
statement is a fact of the app (how it searches, what the side menu holds, the privacy notice of PRIVACY_POLICY.md, how it updates). The counters of the page are drawn live by the app from the content manifest.
usage: python3 -I scripts/build_about.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
ROWS = [
 ['الباحث القرآني', 'منصّة بحث شرعي في القرآن الكريم والسنة النبوية الصحيحة، تبدأ من اللفظ المطابق ثم تتوسّع إلى الجذر اللغوي والألفاظ القريبة دون أي تفسير شخصي.'],
 ['كيف يبحث', 'اكتب كلمة أو عبارة في الحقل «اكتب هنا»، فتظهر النتائج المطابقة للفظ أولاً، ثم ما يقاربها من الجذر والألفاظ القريبة.\nفي «الكتب» و«أبيات الإستشهاد» يفهم التطبيق الكلمات العامية: اكتب «حنش» فيدلّك على «حية، ثعبان».\nفي «الكتب» تأتي معاني الرمز أولاً ثم ما ورد ذكره فيها، ويظهر زر «وجه الشبه» حين يذكر المؤلف سبب التأويل.'],
 ['قائمة «المزيد»', 'رؤى وتعبيرها، ورؤى الأنبياء والصالحين، والمعبِّرون، وقواعد علم التعبير، وأحاديث الرؤيا، ومقارنة المعبِّرين: قوائم كل نص فيها منقول حرفياً من مصدره، واسم المصدر تحت كل نص.'],
 ['نصوص كما هي', 'كل ما تقرؤه منقول من مصدره كما هو دون إضافة من عندنا؛ وأخطاء الطباعة الواضحة وحدها تُصحَّح. وهي نصوص العلماء والكتب، لا فتوى شخصية.'],
 ['الخصوصية', 'لا يجمع التطبيق أي بيانات شخصية، ولا يطلب حساباً، ولا يستخدم أدوات تتبّع أو إعلانات.\nالبحث يتم داخل جهازك، وما تكتبه لا يغادره.\nتفضيل الوضع الفاتح أو الداكن يُحفَظ على جهازك فقط.'],
 ['التحديث', 'عند فتح التطبيق يفحص تلقائياً وجود محتوى جديد فيُطبَّق دون إعادة تثبيت، وإذا توفرت نسخة جديدة من التطبيق تظهر لك نافذة «تحديث الآن».'],
]
def main():
    rows = [[t, x, '', '', ''] for t, x in ROWS]
    CL.publish('about', 'حول التطبيق', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'about', 'menu': 'حول التطبيق', 'placeholder': 'اكتب هنا', 'hint': 'ما هو الباحث القرآني وما يحويه.'})
    return rows
if __name__ == '__main__': print(len(main()), 'rows')
