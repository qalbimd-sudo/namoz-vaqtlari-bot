# Konfiguratsiya - muhit o'zgaruvchilari
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Namoz vaqtlari API sozlamalari
NAMOZ_API_URL = "https://namoztime.herokuapp.com/api/kundalik/"
ALADHAN_API_URL = "http://api.aladhan.com/v1/timingsByCity"

# Mintaqa sozlamalari
REGION = "Toshkent"
CITY = "Tashkent"
COUNTRY = "Uzbekistan"
METHOD = 3  # Aladhan: Muslim World League metodi

# Namoz vaqtlarini yuborish vaqti (Toshkent vaqti, UTC+5)
BROADCAST_HOUR = 5    # 05:00
BROADCAST_MINUTE = 0

TIMEZONE = "Asia/Tashkent"
