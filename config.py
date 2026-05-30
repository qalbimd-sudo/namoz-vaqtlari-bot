import os
from dotenv import load_dotenv

load_dotenv()

# Bot token - .env faylidan yoki to'g'ridan-to'g'ri
BOT_TOKEN = os.getenv("BOT_TOKEN", "8852833040:AAF9nWyMKNQdBqqjjBrayRuSRqw_BwF0iWU")

# Namoz vaqtlari API sozlamalari
NAMOZ_API_URL = "https://namoztime.herokuapp.com/api/kundalik/"
ALADHAN_API_URL = "http://api.aladhan.com/v1/timingsByCity"

# Mintaqa sozlamalari
REGION = "Toshkent"
CITY = "Tashkent"
COUNTRY = "Uzbekistan"
METHOD = 3  # Aladhan: Muslim World League metodi

TIMEZONE = "Asia/Tashkent"
