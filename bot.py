import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from post_generator import create_daily_post

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar")

# Расписание типов постов по часам (МСК)
POST_SCHEDULE = {
    9: "primeta", 10: "saint", 11: "ussr", 12: "lunar",
    13: "primeta", 14: "saint", 15: "ussr", 16: "lunar",
    17: "primeta", 18: "saint", 19: "ussr", 20: "lunar",
    21: "primeta", 22: "saint"
}

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Публикует пост, если сейчас нужный час по МСК"""
    moscow_hour = (datetime.utcnow().hour + 3) % 24  # UTC+3 = МСК
    if moscow_hour in POST_SCHEDULE:
        post_type = POST_SCHEDULE[moscow_hour]
        try:
            image_path, caption = create_daily_post(post_type=post_type)
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
            os.remove(image_path)
            logger.info(f"✅ Пост '{post_type}' опубликован в {moscow_hour}:00 МСК")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации в {moscow_hour}:00: {e}")

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Народный календарь\n\n"
        "Автопубликация: каждый час с 9:00 до 22:00 по МСК.\n"
        "/test — отправить сейчас\n"
        "/status — проверить статус"
    )

async def test_post(update, context: ContextTypes.DEFAULT_TYPE):
    image_path, caption = create_daily_post(post_type="primeta")
    with open(image_path, 'rb') as photo:
        await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
    os.remove(image_path)
    await update.message.reply_text("✅ Пробный пост отправлен!")

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает. Ждёт расписания.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))
    app.add_handler(CommandHandler("status", status))

    # Запуск задачи каждые 60 минут (проверка по МСК)
    app.job_queue.run_repeating(send_scheduled_post, interval=3600, first=10)

    logger.info("✅ Бот запущен. Автопубликация активна.")
    app.run_polling()

if __name__ == "__main__":
    main()
