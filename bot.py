import os
import logging
import re
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar").strip()

# Часы публикации по МСК
POST_HOURS = [8, 9, 1, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

# === Функция экранирования для MarkdownV2 ===
def escape_markdown_v2(text: str) -> str:
    """
    Экранирует спецсимволы для Telegram MarkdownV2,
    но сохраняет *жирный*, _курсив_ и ссылки вида [текст](url).
    """
    # Шаг 1: временно сохраняем ссылки и выделения
    placeholders = []
    
    def save_placeholder(match):
        placeholders.append(match.group(0))
        return f"__PLACEHOLDER__{len(placeholders)-1}__"
    
    # Сохраняем ссылки: [текст](url)
    text = re.sub(r'\[.*?\]\(.*?\)', save_placeholder, text)
    # Сохраняем *жирный*
    text = re.sub(r'\*[^*]*\*', save_placeholder, text)
    # Сохраняем _курсив_ (опционально)
    text = re.sub(r'_[^_]*_', save_placeholder, text)

    # Шаг 2: экранируем все опасные символы
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    # Шаг 3: восстанавливаем сохранённые фрагменты
    for i, placeholder in enumerate(placeholders):
        text = text.replace(f"__PLACEHOLDER__{i}__", placeholder)
    
    return text

# === Загрузка поста из файла ===
def load_post_for_hour(target_hour):
    now = datetime.now()
    filename = f"posts/{now.day:02d}-{now.month:02d}.txt"
    
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return None

    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Ошибка чтения {filename}: {e}")
        return None

    posts = {}
    current_hour = None
    current_content = []

    for line in lines:
        raw_line = line.rstrip('\n\r')
        if raw_line.startswith('[') and '] ' in raw_line:
            if current_hour is not None:
                posts[current_hour] = "\n".join(current_content)
            try:
                time_part = raw_line.split(']')[0][1:]
                hour = int(time_part.split(':')[0])
                current_hour = hour
                content_part = raw_line.split('] ', 1)[1]
                current_content = [content_part]
            except (IndexError, ValueError):
                current_hour = None
                current_content = []
        else:
            if current_hour is not None:
                current_content.append(raw_line)

    if current_hour is not None:
        posts[current_hour] = "\n".join(current_content)

    return posts.get(target_hour)

# === Публикация поста ===
async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    moscow_hour = (datetime.utcnow().hour + 3) % 24
    if moscow_hour not in POST_HOURS:
        return

    post_text = load_post_for_hour(moscow_hour)
    if post_text and post_text.strip():
        try:
            safe_text = escape_markdown_v2(post_text)
            await context.bot.send_message(
                chat_id=CHANNEL,
                text=safe_text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )
            logger.info(f"✅ Пост опубликован в {moscow_hour}:00 МСК")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
    else:
        logger.warning(f"Нет текста для {moscow_hour}:00")

# === Команды ===
async def cmd_test(update, context):
    post = load_post_for_hour(8) or "Файл 08:00 не найден."
    try:
        safe_post = escape_markdown_v2(post)
        await context.bot.send_message(chat_id=CHANNEL, text=safe_post, parse_mode="MarkdownV2")
        await update.message.reply_text("✅ Пробный пост отправлен!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def cmd_start(update, context):
    await update.message.reply_text("✅ Народный календарь. Режим: MarkdownV2.")

# === Запуск ===
def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("test", cmd_test))

    for hour_msk in POST_HOURS:
        utc_hour = (hour_msk - 3) % 24
        app.job_queue.run_daily(send_scheduled_post, time(hour=utc_hour, minute=0, second=10))

    logger.info("✅ Бот запущен. Поддержка *жирного* и [ссылок](url) через MarkdownV2.")
    app.run_polling()

if __name__ == "__main__":
    main()
