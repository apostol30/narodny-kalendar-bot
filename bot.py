import os
import logging
import asyncio
from datetime import datetime, time
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

# Типы постов по часам (9:00, 10:00, ...)
POST_SCHEDULE = {
    9: "primeta",      # Народная примета
    10: "saint",       # Святой + молитва
    11: "ussr",        # Личность СССР
    12: "lunar",       # Лунный календарь
    13: "primeta",     # Ещё одна примета
    14: "saint",       # Молитва дня
    15: "ussr",        # Советская история
    16: "lunar",       # Совет по луне
    17: "primeta",     # Вечерняя примета
    18: "saint",       # Вечерняя молитва
    19: "ussr",
    20: "lunar",
    21: "primeta",
    22: "saint"        # Завершение дня
}

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет пост по расписанию"""
    now = datetime.now()
    hour = now.hour

    if hour in POST_SCHEDULE:
        post_type = POST_SCHEDULE[hour]
        try:
            image_path, caption = create_daily_post(post_type=post_type)
            bot = context.bot
            with open(image_path, 'rb') as photo:
                await bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
            os.remove(image_path)
            logger.info(f"✅ Пост '{post_type}' опубликован в {hour}:00")
        except Exception as e:
            logger.error(f"❌ Ошибка при публикации в {hour}:00: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Народный календарь\n\n"
        "Автоматическая публикация: каждый час с 9:00 до 22:00 по МСК.\n"
        "Команды:\n"
        "/test — отправить сейчас\n"
        "/status — статус"
    )

async def test_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пробный пост (берём первый тип из расписания)
    image_path, caption = create_daily_post(post_type="primeta")
    with open(image_path, 'rb') as photo:
        await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
    os.remove(image_path)
    await update.message.reply_text("✅ Пробный пост отправлен в канал!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает. Публикация по расписанию включена.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))
    app.add_handler(CommandHandler("status", status))

    # Настраиваем ежечасную публикацию
    job_queue = app.job_queue
    # Запуск каждые 60 минут, но публикуем только в нужные часы
    job_queue.run_repeating(send_scheduled_post, interval=3600, first=0)

    logger.info("✅ Бот запущен. Автопубликация активна.")
    app.run_polling()

if __name__ == "__main__":
    main()
