import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from post_generator import create_daily_post

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Народный календарь\n\n"
        "Команды:\n"
        "/test — отправить пост в канал\n"
        "/today — показать пост"
    )

async def test_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        image_path, caption = create_daily_post()
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption)
        os.remove(image_path)
        await update.message.reply_text("✅ Пост отправлен!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ {str(e)}")

async def today_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_path, caption = create_daily_post()
    with open(image_path, 'rb') as photo:
        await update.message.reply_photo(photo=photo, caption=caption)
    os.remove(image_path)

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))
    app.add_handler(CommandHandler("today", today_post))
    logger.info("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
