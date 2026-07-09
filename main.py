import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

# بيانات البوت والقناة
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "@hayat_klha_kbd"

# صورة الأذكار
PHOTO_URL = "https://i.ibb.co/5WC8s9jW/AZKAR.jpg"

# قراءة بيانات Google من Secret
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(
    creds_dict,
    scopes=scopes,
)

client = gspread.authorize(credentials)

# افتح ملف Google Sheets
sheet = client.open("بيانات القناة").worksheet("الورقة1")

# اقرأ جميع الصفوف
rows = sheet.get_all_values()

# تجاهل صف العناوين
for i, row in enumerate(rows[1:], start=2):

    if len(row) < 3:
        continue

    text = row[1].strip()
    status = row[2].strip()

    if status == "Pending":

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "photo": PHOTO_URL,
                "caption": text,
            },
        )

        if response.status_code == 200:
            sheet.update_cell(i, 3, "Done")
            print("✅ تم إرسال الذكر بنجاح")
        else:
            print(response.text)

        break
else:
    print("لا توجد أذكار جديدة.")
