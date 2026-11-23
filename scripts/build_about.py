"""Builds the page «حول التطبيق» of the «المزيد» menu (content/about.json): ONE description of what the platform does, without numbers, in a single message. Every statement is a fact of the app.
usage: python3 -I scripts/build_about.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
ROWS = [
 ['الباحث القرآني', 'منصّة بحث شرعي تجمع القرآن الكريم والسنة النبوية وأمثال العرب والألفية الوردية وأبيات الاستشهاد وكتب تعبير الرؤى في مكان واحد، وتبدأ في البحث من اللفظ المطابق ثم تتوسّع إلى الجذر اللغوي والألفاظ القريبة دون أي تفسير شخصي. وتفهم الكلمة العامية فتردّها إلى الفصيحة، وتعرض كل نتيجة بنص مصدرها كما هو. وفي قائمة «المزيد»: رؤى الأنبياء والصالحين، وتعبيرات المعبّرين ومقارنتها، وقواعد علم التعبير، وأحاديث الرؤيا. ولا تجمع المنصة أي بيانات شخصية، ويجري البحث كله داخل جهازك.'],
]
def main():
    rows = [[t, x, '', '', ''] for t, x in ROWS]
    CL.publish('about', 'حول التطبيق', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'about', 'menu': 'حول التطبيق', 'placeholder': 'اكتب هنا', 'hint': 'ما هو الباحث القرآني وما يحويه.'})
    return rows
if __name__ == '__main__': print(len(main()), 'rows')
