import os
import logging
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar")

POST_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

def load_post_for_time(target_hour):
    now = datetime.now()
    filename = f"posts/{now.day:02d}-{now.month:02d}.txt"
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return None

    current_hour = None
    current_lines = []
    posts = {}

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('[') and '] ' in line:
                if current_hour is not None:
                    posts[current_hour] = "\n".join(current_lines).strip()
                time_str = line.split(']')[0][1:]
                hour = int(time_str.split(':')[0])
                current_hour = hour
                theme = line.split('] ', 1)[1]
                current_lines = [theme]
            else:
                if current_hour is not None:
                    current_lines.append(line)
        if current_hour is not None:
            posts[current_hour] = "\n".join(current_lines).strip()

    return posts.get(target_hour)

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    moscow_hour = (datetime.utcnow().hour + 3) % 24
    if moscow_hour not in POST_HOURS:
        return

    post_text = load_post_for_time(moscow_hour)
    if post_text:
        try:
            await context.bot.send_message(chat_id=CHANNEL, text=post_text)
            logger.info(f"✅ Пост опубликован в {moscow_hour}:00")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
    else:
        logger.warning(f"Нет поста на {moscow_hour}:00")

async def test_post(update, context):
    post_text = load_post_for_time(8)
    if post_text:
        await context.bot.send_message(chat_id=CHANNEL, text=post_text)
        await update.message.reply_text("✅ Пробный пост отправлен!")
    else:
        await update.message.reply_text("❌ Пост не найден.")

async def start(update, context):
    await update.message.reply_text("✅ Бот работает. Публикация по дням года.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_post))

    for hour_msk in POST_HOURS:
        run_time_utc = (hour_msk - 3) % 24
        # ✅ Правильно: один объект time
        app.job_queue.run_daily(
            send_scheduled_post,
            time(hour=run_time_utc, minute=0, second=5)
        )

    logger.info("✅ Бот запущен. Точная публикация по МСК.")
    app.run_polling()

if __name__ == "__main__":
    main()
