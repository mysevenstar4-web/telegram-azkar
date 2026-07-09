import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

# جلب البيانات من المتغيرات البيئية (أكثر أماناً)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@hayat_klha_kbd") # يفضل إضافته لـ Secrets
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDENTIALS")

# صورة الأذكار ثنائية الأبعاد الثابتة
PHOTO_URL = "https://i.ibb.co/5WC8s9jW/AZKAR.jpg"

if not BOT_TOKEN or not GOOGLE_CREDS_JSON:
    print("❌ خطأ: لم يتم العثور على المتغيرات البيئية المطلوبة في GitHub Secrets.")
    exit(1)

# إعداد الصلاحيات والاتصال بـ Google Sheets
try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # فتح الجدول والورقة الأولى
    sheet = client.open("بيانات القناة").worksheet("الورقة1")
    rows = sheet.get_all_values()
except Exception as e:
    print(f"❌ خطأ أثناء الاتصال بـ Google Sheets API: {e}")
    exit(1)

# معالجة الأذكار
# rows[0] هو صف العناوين، الأذكار تبدأ من الصف الثاني (index 2 في Google Sheets)
for i, row in enumerate(rows[1:], start=2):
    if len(row) < 3:
        continue

    text = row[1].strip()
    status = row[2].strip()

    # التحقق من الحالة (تأكدي أن الكلمة مطابقة تماماً لما في الجدول)
    if status == "Pending":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "photo": PHOTO_URL,
                    "caption": text,
                },
                timeout=10 # منع السكربت من التعليق إذا كانت استجابة تيليجرام بطيئة
            )
            
            if response.status_code == 200:
                sheet.update_cell(i, 3, "Done")
                print(f"✅ تم إرسال الذكر بنجاح (الصف {i})")
            else:
                print(f"❌ فشل إرسال الرسالة من طرف تيليجرام: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الاتصال بشبكة تيليجرام: {e}")
            
        # التوقف بعد إرسال ذكر واحد فقط بناءً على الدورة اليومية
        break
else:
    # هذا البلوك يعمل فقط إذا انتهت الحلقة ولم تجد أي صف حالته "Pending"
    print("🔄 تم إرسال جميع الأذكار مسبقاً. جاري إعادة تعيين الجدول للبدء من جديد...")
    
    # إعادة تعيين الحالات إلى Pending (من الصف الثاني وحتى آخر صف يحتوي على بيانات)
    total_rows = len(rows)
    if total_rows > 1:
        # تحديث العمود الثالث بالكامل إلى Pending دفعة واحدة لتوفير حصة الـ API
        cell_list = sheet.range(2, 3, total_rows, 3)
        for cell in cell_list:
            cell.value = "Pending"
        sheet.update_cells(cell_list)
        print("✅ تم إعادة تعيين جميع الأذكار إلى حالة Pending بنجاح.")
    else:
        print("⚠️ الجدول فارغ ولا توجد بيانات لإعادة تعيينها.")
