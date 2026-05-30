import asyncio
import logging
from datetime import datetime, date

import pytz
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ChatMemberStatus, ChatType
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, TIMEZONE
from database import init_db, add_chat, remove_chat, get_all_chats
from prayer_api import (
    get_prayer_times, format_prayer_message,
    format_single_prayer_message, parse_time_str, PRAYER_NAMES
)

# ─── Logging sozlamalari ──────────────────────────────────────────────────────
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Bot va Dispatcher ────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# Global scheduler (main() ichida ishga tushiriladi)
scheduler: AsyncIOScheduler = None


# ─── Yordamchi: barcha chatlarga xabar yuborish ──────────────────────────────
async def send_to_all_chats(text: str):
        """Bazadagi barcha chatlarga xabar yuborish."""
        chats = get_all_chats()
        success, failed = 0, 0
        for chat_id in chats:
                    try:
                                    await bot.send_message(chat_id, text, parse_mode="Markdown")
                                    success += 1
                                    await asyncio.sleep(0.05)  # Telegram API limiti
except Exception as e:
            error_str = str(e).lower()
            logger.warning(f"{chat_id} ga xabar yuborishda xato: {e}")
            if any(x in error_str for x in [
                                "bot was kicked", "chat not found",
                                "bot is not a member", "forbidden"
            ]):
                                remove_chat(chat_id)
                                logger.info(f"Faol bo'lmagan chat o'chirildi: {chat_id}")
                            failed += 1
    logger.info(f"Yuborildi: {success} ta OK, {failed} ta xato.")


# ─── Bitta namoz vaqti uchun broadcast ───────────────────────────────────────
async def broadcast_single_prayer(prayer_key: str, time_str: str):
        """Bitta namoz vaqti kelganda barcha guruhlarga yuborish."""
        logger.info(f"Namoz xabari: {prayer_key} - {time_str}")
        text = format_single_prayer_message(prayer_key, time_str)
        await send_to_all_chats(text)


# ─── Kunlik jadval xabari (ixtiyoriy - ertalab yuboriladi) ───────────────────
async def broadcast_daily_schedule():
        """Har kuni bomdod oldidan bugungi barcha namoz vaqtlarini yuborish."""
        logger.info("Kunlik jadval yuborilmoqda...")
        times = await get_prayer_times()
        if not times:
                    logger.error("Kunlik jadval: API dan vaqtlar olinmadi.")
                    return
                text = format_prayer_message(times)
    await send_to_all_chats(text)


# ─── Namoz vaqtlari uchun joblarni yangilash ─────────────────────────────────
async def schedule_today_prayers():
        """
            Har kuni tunda (00:01) bugungi namoz vaqtlarini API dan olib,
                har bir namoz uchun APScheduler ga job qo'shadi.
                    """
    global scheduler
    logger.info("Bugungi namoz vaqtlari schedulega qo'shilmoqda...")

    times = await get_prayer_times()
    if not times:
                logger.error("schedule_today_prayers: API ishlamadi!")
                return

    tz = pytz.timezone(TIMEZONE)
    today = date.today()

    # Eski namoz joblarini o'chirish
    for job in scheduler.get_jobs():
                if job.id.startswith("prayer_"):
                                job.remove()
                                logger.debug(f"Eski job o'chirildi: {job.id}")

            # Har bir namoz uchun yangi job qo'shish
            prayers_to_schedule = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    scheduled_count = 0

    for prayer_key in prayers_to_schedule:
                time_str = times.get(prayer_key)
                if not time_str:
                                continue

                parsed = parse_time_str(time_str)
                if not parsed:
                                logger.warning(f"{prayer_key} vaqtini tahlil qilib bo'lmadi: {time_str}")
                                continue

                hour, minute = parsed

        # Joriy vaqtdan o'tib ketgan namozlarni qo'shmaslik
                now = datetime.now(tz)
        if now.hour > hour or (now.hour == hour and now.minute >= minute):
                        logger.info(f"{prayer_key} ({hour:02d}:{minute:02d}) allaqachon o'tdi, o'tkazildi.")
                        continue

        job_id = f"prayer_{prayer_key}_{today.strftime('%Y%m%d')}"

        scheduler.add_job(
                        broadcast_single_prayer,
                        trigger=CronTrigger(
                                            hour=hour,
                                            minute=minute,
                                            timezone=tz,
                        ),
                        args=[prayer_key, time_str],
                        id=job_id,
                        replace_existing=True,
                        name=f"{PRAYER_NAMES.get(prayer_key, prayer_key)} namozi",
        )
        logger.info(f"Job qo'shildi: {prayer_key} - {hour:02d}:{minute:02d}")
        scheduled_count += 1

    logger.info(f"Jami {scheduled_count} ta namoz jobi qo'shildi.")


# ─── /start handler ───────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
        chat = message.chat
    add_chat(chat.id, chat.type, chat.title or chat.first_name)

    if chat.type == ChatType.PRIVATE:
                await message.answer(
                                "Assalomu alaykum!\n\n"
                                "Men *har bir namoz vaqti kirganda* xabar yuboran botman.\n\n"
                                "Kuniga *5 marta* (Bomdod, Peshin, Asr, Shom, Xufton) avtomatik xabar keladi.\n\n"
                                "Buyruqlar:\n"
                                "/vaqtlar - bugungi barcha namoz vaqtlari\n"
                                "/start - botni qayta ishga tushirish",
                )
else:
        await message.answer(
                        "Bot guruhga qo'shildi!\n"
                        "Har bir namoz vaqti kirganda avtomatik xabar yuboriladi.\n"
                        "Kuniga *5 marta*: Bomdod, Peshin, Asr, Shom, Xufton.\n\n"
                        "/vaqtlar - bugungi namoz vaqtlarini ko'rish",
        )
    logger.info(f"/start: {chat.id} ({chat.title or chat.first_name})")


# ─── /vaqtlar handler ─────────────────────────────────────────────────────────
@dp.message(Command("vaqtlar"))
async def cmd_vaqtlar(message: Message):
        chat = message.chat
    add_chat(chat.id, chat.type, chat.title or chat.first_name)

    wait_msg = await message.answer("Namoz vaqtlari yuklanmoqda...")
    times = await get_prayer_times()
    if times:
                text = format_prayer_message(times)
                await wait_msg.edit_text(text, parse_mode="Markdown")
else:
        await wait_msg.edit_text(
                        "Namoz vaqtlarini yuklab bo'lmadi. Keyinroq urinib ko'ring."
        )


# ─── Bot guruhga qo'shilganda / chiqarilganda ────────────────────────────────
@dp.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
        old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    chat = event.chat

    if new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
                if old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.BANNED):
                                add_chat(chat.id, chat.type, chat.title)
                                try:
                                                    await bot.send_message(
                                                                            chat.id,
                                                                            "Salom! Namoz vaqtlarini yuboruvchi botman.\n"
                                                                            "Har namoz vaqti kirganda avtomatik xabar yuboriladi (kuniga 5 ta).\n"
                                                                            "/vaqtlar - bugungi namoz vaqtlari",
                                                    )
except Exception as e:
                logger.warning(f"Guruhga salom yuborishda xato: {e}")
            logger.info(f"Bot guruhga qo'shildi: {chat.id} ({chat.title})")

elif new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.BANNED):
        remove_chat(chat.id)
        logger.info(f"Bot guruhdan chiqarildi: {chat.id} ({chat.title})")


# ─── Asosiy ishga tushirish funksiyasi ───────────────────────────────────────
async def main():
        global scheduler

    # Ma'lumotlar bazasini ishga tushirish
    init_db()

    # Scheduler sozlash (Toshkent vaqtida)
    tz = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # 1. Har kuni 00:01 da namoz vaqtlarini schedulega qo'shish
    scheduler.add_job(
                schedule_today_prayers,
                trigger=CronTrigger(hour=0, minute=1, timezone=tz),
                id="daily_reschedule",
                name="Kunlik namoz vaqtlarini yangilash",
                replace_existing=True,
    )

    # 2. Har kuni 04:00 da kunlik jadval xabarini yuborish (ixtiyoriy)
    scheduler.add_job(
                broadcast_daily_schedule,
                trigger=CronTrigger(hour=4, minute=0, timezone=tz),
                id="daily_schedule_broadcast",
                name="Kunlik jadval xabari",
                replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    # Bot ishga tushganda darhol bugungi namoz vaqtlarini schedulega qo'shish
    logger.info("Bugungi namoz vaqtlari darhol schedulega qo'shilmoqda...")
    await schedule_today_prayers()

    # Botni ishga tushirish
    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
                await dp.start_polling(bot)
finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
        asyncio.run(main())
