import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@hayat_klha_kbd")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDENTIALS")

if not BOT_TOKEN or not GOOGLE_CREDS_JSON:
    print("❌ خطأ: لم يتم العثور على المتغيرات البيئية المطلوبة.")
    exit(1)

try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    sheet = client.open("بيانات القناة").worksheet("الورقة1")
    rows = sheet.get_all_values()
except Exception as e:
    print(f"❌ خطأ أثناء الاتصال بـ Google Sheets API: {e}")
    exit(1)

for i, row in enumerate(rows[1:], start=2):
    if len(row) < 3:
        continue

    text = row[1].strip()
    status = row[2].strip()

    if status == "Pending":
        # تم تغيير الرابط ليرسل نصوصاً فقط
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "text": text, # تم تغيير caption إلى text
                },
                timeout=10
            )
            
            if response.status_code == 200:
                sheet.update_cell(i, 3, "Done")
                print(f"✅ تم إرسال الذكر النصي بنجاح (الصف {i})")
            else:
                print(f"❌ فشل إرسال الرسالة من طرف تيليجرام: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الاتصال بشبكة تيليجرام: {e}")
            
        break
else:
    print("🔄 تم إرسال جميع الأذكار مسبقاً. جاري إعادة تعيين الجدول للبدء من جديد...")
    
    total_rows = len(rows)
    if total_rows > 1:
        cell_list = sheet.range(2, 3, total_rows, 3)
        for cell in cell_list:
            cell.value = "Pending"
        sheet.update_cells(cell_list)
        print("✅ تم إعادة تعيين جميع الأذكار إلى حالة Pending بنجاح.")
    else:
        print("⚠️ الجدول فارغ ولا توجد بيانات لإعادة تعيينها.")
