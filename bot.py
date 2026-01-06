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

# Публикация с 8:00 до 22:00 по МСК
POST_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

def load_post_for_hour(target_hour):
    """Загружает пост из файла DD-MM.txt для указанного часа"""
    now = datetime.now()
    filename = f"posts/{now.day:02d}-{now.month:02d}.txt"
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return None

    posts = {}
    current_hour = None
    current_lines = []

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('[') and '] ' in line:
                # Сохраняем предыдущий пост
                if current_hour is not None:
                    posts[current_hour] = "\n".join(current_lines).strip()
                # Извлекаем час
                time_part = line[1:line.find(']')]
                hour = int(time_part.split(':')[0])
                current_hour = hour
                # Извлекаем тему
                theme = line.split('] ', 1)[1]
                current_lines = [theme]
            else:
                if current_hour is not None:
                    current_lines.append(line)
        # Сохраняем последний пост
        if current_hour is not None:
            posts[current_hour] = "\n".join(current_lines).strip()

    return posts.get(target_hour)

async def publish_post(context: ContextTypes.DEFAULT_TYPE):
    moscow_hour = (datetime.utcnow().hour + 3) % 24
    if moscow_hour not in POST_HOURS:
        return

    post_text = load_post_for_hour(moscow_hour)
    if post_text:
        try:
            await context.bot.send_message(chat_id=CHANNEL, text=post_text)
            logger.info(f"✅ Пост опубликован в {moscow_hour}:00 МСК")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации: {e}")
    else:
        logger.warning(f"Нет поста на {moscow_hour}:00")

# === Команды ===
async def cmd_test(update, context):
    post = load_post_for_hour(8) or "Тестовый пост: файл 08:00 не найден."
    await context.bot.send_message(chat_id=CHANNEL, text=post)
    await update.message.reply_text("✅ Пробный пост отправлен в канал.")

async def cmd_start(update, context):
    await update.message.reply_text("✅ Народный календарь готов. Публикация по дням года.")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("test", cmd_test))

    # Запуск задач на точное время по МСК
    for hour_msk in POST_HOURS:
        utc_hour = (hour_msk - 3) % 24
        app.job_queue.run_daily(publish_post, time(hour=utc_hour, minute=0, second=10))

    logger.info("✅ Бот запущен. Режим: файлы по дням. Точное время по МСК.")
    app.run_polling()

if __name__ == "__main__":
    main()
