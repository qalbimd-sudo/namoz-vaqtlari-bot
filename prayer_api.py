import aiohttp
import logging
from datetime import datetime
import pytz
from config import (
    NAMOZ_API_URL, ALADHAN_API_URL,
    REGION, CITY, COUNTRY, METHOD, TIMEZONE
)

logger = logging.getLogger(__name__)

# Namoz vaqtlari - 5 asosiy namoz (Sunrise chiqarib tashlandi)
PRAYER_NAMES = {
        "Fajr":    "Bomdod (Fajr)",
        "Dhuhr":   "Peshin (Zuhr)",
        "Asr":     "Asr",
        "Maghrib": "Shom (Maghrib)",
        "Isha":    "Xufton (Isha)",
}

# Har bir namoz uchun emoji
PRAYER_EMOJI = {
        "Fajr":    "🌙",
        "Dhuhr":   "☀️",
        "Asr":     "🌤️",
        "Maghrib": "🌇",
        "Isha":    "🌃",
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


def parse_time_str(time_str: str) -> tuple[int, int] | None:
        """
            Vaqt satrini (masalan '05:23' yoki '05:23 (BST)') soat va daqiqaga ajratish.
                """
    try:
                if not time_str or time_str == "N/A":
                                return None
                            # Faqat "HH:MM" qismini olish
                            parts = str(time_str).strip().split()[0]
        h, m = parts.split(":")
        return int(h), int(m)
except Exception:
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
                f"  {'Bomdod':<12} {str(times.get('Fajr', '---')).strip()[:5]}",
                f"  {'Peshin':<12} {str(times.get('Dhuhr', '---')).strip()[:5]}",
                f"  {'Asr':<12} {str(times.get('Asr', '---')).strip()[:5]}",
                f"  {'Shom':<12} {str(times.get('Maghrib', '---')).strip()[:5]}",
                f"  {'Xufton':<12} {str(times.get('Isha', '---')).strip()[:5]}",
                "```",
                "",
                "_Alloh ibodat va namozlaringizni qabul qilsin!_",
    ]
    return "\n".join(lines)


def format_single_prayer_message(prayer_key: str, time_str: str) -> str:
        """
            Bitta namoz vaqti kelganda yuboriladigan qisqa xabar.
                Masalan: "Bomdod namozi vaqti kirdi - 05:23"
    """
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    date_str = today.strftime("%d.%m.%Y")

    name = PRAYER_NAMES.get(prayer_key, prayer_key)
    emoji = PRAYER_EMOJI.get(prayer_key, "🕌")
    vaqt = str(time_str).strip()[:5]

    lines = [
                f"{emoji} *{name} namozi vaqti kirdi!*",
                f"",
                f"*Vaqt:* `{vaqt}` | {date_str}",
                f"",
                f"_Namozni o'z vaqtida o'qing!_ 🤲",
    ]
    return "\n".join(lines)
