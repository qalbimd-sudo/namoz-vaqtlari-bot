import aiohttp
import logging
from datetime import datetime
import pytz
from config import (
    NAMOZ_API_URL, ALADHAN_API_URL,
    REGION, CITY, COUNTRY, METHOD, TIMEZONE
)

logger = logging.getLogger(__name__)

# Namoz vaqtlari nomlari (o'zbekcha)
PRAYER_NAMES = {
      "Fajr":    "Bomdod (Fajr)",
      "Sunrise": "Quyosh chiqishi",
      "Dhuhr":   "Peshin (Zuhr)",
      "Asr":     "Asr",
      "Maghrib": "Shom (Maghrib)",
      "Isha":    "Xufton (Isha)",
}


async def fetch_from_namoztime(day: int, month: int) -> dict | None:
      """zero8d/namozvaqtlariapi (islom.uz asosida) dan namoz vaqtlarini olish."""
      payload = {"region": REGION, "month": month, "day": day}
      try:
                async with aiohttp.ClientSession() as session:
                              async with session.post(
                                                NAMOZ_API_URL,
                                                json=payload,
                                                timeout=aiohttp.ClientTimeout(total=10)
                              ) as resp:
                                                if resp.status == 200:
                                                                      data = await resp.json(content_type=None)
                                                                      if data:
                                                                                                return data
      except Exception as e:
                logger.warning(f"NamozTime API xatosi: {e}")
            return None


async def fetch_from_aladhan(day: int, month: int, year: int) -> dict | None:
      """Aladhan API dan namoz vaqtlarini olish (zaxira manba)."""
    try:
              async with aiohttp.ClientSession() as session:
                            url = f"http://api.aladhan.com/v1/timingsByCity/{day}-{month}-{year}"
                            params = {
                                "city": CITY,
                                "country": COUNTRY,
                                "method": METHOD,
                            }
                            async with session.get(
                                              url,
                                              params=params,
                                              timeout=aiohttp.ClientTimeout(total=10)
                            ) as resp:
                                              if resp.status == 200:
                                                                    data = await resp.json()
                                                                    if data.get("code") == 200:
                                                                                              timings = data["data"]["timings"]
                                                                                              return {
                                                                                                  "Fajr":    timings.get("Fajr", "N/A"),
                                                                                                  "Sunrise": timings.get("Sunrise", "N/A"),
                                                                                                  "Dhuhr":   timings.get("Dhuhr", "N/A"),
                                                                                                  "Asr":     timings.get("Asr", "N/A"),
                                                                                                  "Maghrib": timings.get("Maghrib", "N/A"),
                                                                                                  "Isha":    timings.get("Isha", "N/A"),
                                                                                              }
    except Exception as e:
        logger.warning(f"Aladhan API xatosi: {e}")
    return None


def parse_namoztime_response(data: dict) -> dict | None:
      """NamozTime API javobini standart formatga o'tkazish."""
    try:
              mapping = {
                            "Fajr":    data.get("Bomdod") or data.get("bomdod") or data.get("Fajr"),
                            "Sunrise": data.get("Quyosh") or data.get("quyosh") or data.get("Sunrise"),
                            "Dhuhr":   data.get("Peshin") or data.get("peshin") or data.get("Dhuhr"),
                            "Asr":     data.get("Asr") or data.get("asr"),
                            "Maghrib": data.get("Shom") or data.get("shom") or data.get("Maghrib"),
                            "Isha":    data.get("Hufton") or data.get("hufton") or data.get("Isha"),
              }
              if any(mapping.values()):
                            return mapping
    except Exception as e:
        logger.warning(f"NamozTime javobini tahlil qilishda xato: {e}")
    return None


async def get_prayer_times() -> dict | None:
      """
          Bugungi namoz vaqtlarini olish.
              Avval NamozTime API (islom.uz), ishlamasa Aladhan API ishlatiladi.
                  """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    day, month, year = now.day, now.month, now.year

    # 1. NamozTime API (islom.uz asosida)
    raw = await fetch_from_namoztime(day, month)
    if raw:
              parsed = parse_namoztime_response(raw)
              if parsed:
                            logger.info("NamozTime API dan vaqtlar olindi.")
                            return parsed

          # 2. Zaxira: Aladhan API
          logger.info("Aladhan API ga o'tilmoqda (zaxira)...")
    aladhan_data = await fetch_from_aladhan(day, month, year)
    if aladhan_data:
              logger.info("Aladhan API dan vaqtlar olindi.")
              return aladhan_data

    logger.error("Barcha API lar ishlamadi!")
    return None


def format_prayer_message(times: dict) -> str:
      """Namoz vaqtlarini chiroyli Telegram xabar formatiga o'tkazish."""
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    date_str = today.strftime("%d.%m.%Y")
    weekdays = [
              "Dushanba", "Seshanba", "Chorshanba",
              "Payshanba", "Juma", "Shanba", "Yakshanba"
    ]
    weekday = weekdays[today.weekday()]

    lines = [
              f"*Namoz Vaqtlari — {REGION}*",
              f"*{date_str} | {weekday}*",
              "",
              "```",
    ]

    icons = {
              "Fajr":    "Bomdod   ",
              "Sunrise": "Quyosh   ",
              "Dhuhr":   "Peshin   ",
              "Asr":     "Asr      ",
              "Maghrib": "Shom     ",
              "Isha":    "Xufton   ",
    }

    for key, label in icons.items():
              value = times.get(key, "---")
              if value and value != "---":
                            value = str(value).strip()[:5]
                        lines.append(f"  {label}  {value}")

    lines.append("```")
    lines.append("")
    lines.append("_Alloh ibodat va namozlaringizni qabul qilsin!_")
    return "\n".join(lines)
