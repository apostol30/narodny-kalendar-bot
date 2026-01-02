import os
import logging
from datetime import datetime
from telegram.ext import Application, CommandHandler, ContextTypes
from post_generator import create_daily_post

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar")

# Финальное расписание — 15 постов в день
POST_SCHEDULE = {
    8: "holiday",
    9: "primeta",
    10: "saint",
    11: "ussr",
    12: "quote_morning",
    13: "primeta",
    14: "saint",
    15: "ussr",
    16: "lunar",
    17: "primeta",
    18: "quote_evening",
    19: "quiz",
    20: "evening_prayer",
    21: "proverb",
    22: "saint_tomorrow"
}

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
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
            logger.error(f"❌ Ошибка: {e}")

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Народный календарь\n\n"
        "Публикация: каждый час с 8:00 до 22:00 по МСК.\n"
        "• Праздники, приметы, святые\n"
        "• Герои, цитаты, викторины\n"
        "• Молитвы, пословицы, луна\n\n"
        "/test — отправить пробный пост\n"
        "/status — проверить статус"
    )

async def test_post(update, context: ContextTypes.DEFAULT_TYPE):
    image_path, caption = create_daily_post(post_type="holiday")
    with open(image_path, 'rb') as photo:
        await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
    os.remove(image_path)
    await update.message.reply_text("✅ Пробный пост (праздник) отправлен!")

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает. Расписание активно.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))
    app.add_handler(CommandHandler("status", status))
    app.job_queue.run_repeating(send_scheduled_post, interval=3600, first=10)
    logger.info("✅ Бот запущен. Полный цикл: 8:00–22:00.")
    app.run_polling()

if __name__ == "__main__":
    main()
