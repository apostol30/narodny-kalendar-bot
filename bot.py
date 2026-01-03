import os
import logging
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes
from post_generator import create_daily_post

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar")
PAUSED = False

POST_TIMES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
POST_TYPES = {
    8: "holiday", 9: "primeta", 10: "saint", 11: "ussr",
    12: "quote_morning", 13: "primeta", 14: "saint", 15: "ussr",
    16: "lunar", 17: "primeta", 18: "quote_evening", 19: "quiz",
    20: "evening_prayer", 21: "proverb", 22: "saint_tomorrow"
}

async def send_post_by_hour(context: ContextTypes.DEFAULT_TYPE):
    global PAUSED
    if PAUSED:
        return
    moscow_hour = (datetime.utcnow().hour + 3) % 24
    if moscow_hour in POST_TYPES:
        post_type = POST_TYPES[moscow_hour]
        try:
            image_path, caption = create_daily_post(post_type)
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
            os.remove(image_path)
            logger.info(f"✅ Пост '{post_type}' опубликован в {moscow_hour}:00 МСК")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

async def start(update, context):
    await update.message.reply_text("🌾 Народный календарь — панель управления\n\n/test — тест\n/status — статус\n/pause — пауза")

async def test_post(update, context):
    image_path, caption = create_daily_post("holiday")
    with open(image_path, 'rb') as photo:
        await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
    os.remove(image_path)
    await update.message.reply_text("✅ Пробный пост отправлен!")

async def status(update, context):
    state = "⏸️ Остановлен" if PAUSED else "▶️ Работает"
    await update.message.reply_text(f"Статус: {state}")

async def pause(update, context):
    global PAUSED
    PAUSED = True
    await update.message.reply_text("⏸️ Публикация приостановлена на 24 ч.")
    context.job_queue.run_once(resume_publishing, 86400, chat_id=update.effective_chat.id)

async def resume_publishing(context):
    global PAUSED
    PAUSED = False
    await context.bot.send_message(chat_id=context.job.chat_id, text="▶️ Публикация возобновлена.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("pause", pause))

    for hour_msk in POST_TIMES:
        run_time_utc = (hour_msk - 3) % 24
        app.job_queue.run_daily(
            send_post_by_hour,
            time=time(hour=run_time_utc, minute=0, second=5)
        )

    logger.info("✅ Бот запущен. Вечная версия. Публикация по МСК.")
    app.run_polling()

if __name__ == "__main__":
    main()
