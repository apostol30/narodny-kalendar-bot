import os
import logging
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена и канала из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar").strip()

# Часы публикации по Московскому времени
POST_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

def load_post_for_hour(target_hour):
    """
    Загружает пост из файла DD-MM.txt для указанного часа.
    Формат файла: [09:00] ⛪ Святой дня / молитва
    """
    now = datetime.now()
    filename = f"posts/{now.day:02d}-{now.month:02d}.txt"
    
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return None

    try:
        # Читаем файл в кодировке UTF-8 (с поддержкой BOM)
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filename}: {e}")
        return None

    posts = {}
    current_hour = None
    current_content = []

    for line in lines:
        # Убираем только символы новой строки, НЕ пробелы в начале/конце содержимого
        raw_line = line.rstrip('\n\r')

        if raw_line.startswith('[') and '] ' in raw_line:
            # Сохраняем предыдущий пост
            if current_hour is not None:
                posts[current_hour] = "\n".join(current_content)
            
            # Извлекаем час
            try:
                time_part = raw_line.split(']')[0][1:]  # "09:00"
                hour = int(time_part.split(':')[0])
                current_hour = hour
                # Извлекаем оставшуюся часть (тема + эмодзи)
                content_part = raw_line.split('] ', 1)[1]
                current_content = [content_part]
            except (IndexError, ValueError):
                # Некорректная строка — пропускаем
                current_hour = None
                current_content = []
        else:
            if current_hour is not None:
                current_content.append(raw_line)

    # Сохраняем последний пост
    if current_hour is not None:
        posts[current_hour] = "\n".join(current_content)

    return posts.get(target_hour)

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Публикует пост, если сейчас нужный час по МСК"""
    moscow_hour = (datetime.utcnow().hour + 3) % 24
    if moscow_hour not in POST_HOURS:
        return

    post_text = load_post_for_hour(moscow_hour)
    if post_text and post_text.strip():
        try:
            await context.bot.send_message(
                chat_id=CHANNEL,
                text=post_text,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Пост опубликован в {moscow_hour}:00 МСК")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки поста: {e}")
    else:
        logger.warning(f"Нет текста для публикации в {moscow_hour}:00")

# === Команды управления ===
async def cmd_test(update, context):
    """Отправляет пробный пост (8:00)"""
    post = load_post_for_hour(8)
    if not post:
        post = "❌ Файл не найден или пуст. Проверьте posts/DD-MM.txt"
    try:
        await context.bot.send_message(chat_id=CHANNEL, text=post)
        await update.message.reply_text("✅ Пробный пост отправлен в канал!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def cmd_start(update, context):
    await update.message.reply_text(
        "🌾 Народный календарь\n\n"
        "Автоматическая публикация: 8:00–22:00 по МСК.\n"
        "Команды:\n"
        "/test — отправить пост за 8:00\n"
        "/start — это сообщение"
    )

# === Запуск ===
def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в переменных окружения!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("test", cmd_test))

    # Запуск задач на точное время по МСК
    for hour_msk in POST_HOURS:
        utc_hour = (hour_msk - 3) % 24
        app.job_queue.run_daily(
            send_scheduled_post,
            time(hour=utc_hour, minute=0, second=10)
        )

    logger.info("✅ Бот запущен. Чтение файлов в UTF-8. Публикация по МСК.")
    app.run_polling()

if __name__ == "__main__":
    main()
