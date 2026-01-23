#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для публикации постов с автоматической генерацией изображений и форматированием Markdown2
"""

import os
import logging
import re
import markdown2
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar").strip()
POSTS_DIR = "posts"
ASSETS_DIR = "assets"
FONTS_DIR = "fonts"
GENERATED_DIR = "generated_images"

# Файлы
BACKGROUND_FILE = os.path.join(ASSETS_DIR, "fon.jpg")
FONT_FILE = os.path.join(FONTS_DIR, "GOST_A.TTF")

# Часы публикации по Московскому времени (UTC+3)
POST_HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

# Русские названия месяцев
MONTHS_RU = [
    "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ",
    "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"
]

# Настройки markdown2
MARKDOWN_EXTRAS = [
    'fenced-code-blocks', 'tables', 'break-on-newline',
    'cuddled-lists', 'markdown-in-html', 'spoiler',
    'strike', 'target-blank-links', 'header-ids', 'pyshell'
]

# ==================== ФУНКЦИИ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ ====================
def create_post_image(theme: str, month: str, day: str, output_path: str) -> str:
    import re

    def remove_emoji(text: str) -> str:
        if not text:
            return ""
        emoji_pattern = re.compile(
            r"["
            r"\U0001F600-\U0001F64F"
            r"\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF"
            r"\U0001F1E0-\U0001F1FF"
            r"\U00002702-\U000027B0"
            r"\U000024C2-\U001F251"
            r"\U0001f926-\U0001f937"
            r"\U00010000-\U0010ffff"
            r"\u2640-\u2642"
            r"\u2600-\u2B55"
            r"\u200d"
            r"\u23cf"
            r"\u23e9"
            r"\u231a"
            r"\ufe0f"
            r"\u3030"
            r"\u00A9\u00AE\u2122"
            r"]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text).strip()

    try:
        if not os.path.exists(BACKGROUND_FILE):
            logger.error(f"Фоновое изображение не найдено: {BACKGROUND_FILE}")
            return None
        
        if not os.path.exists(FONT_FILE):
            logger.error(f"Шрифт не найден: {FONT_FILE}")
            return None
        
        img = Image.open(BACKGROUND_FILE)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size
        
        font_month = ImageFont.truetype(FONT_FILE, 90)
        font_date = ImageFont.truetype(FONT_FILE, 150)
        font_theme = ImageFont.truetype(FONT_FILE, 90)
        
        start_y = 220
        line_height = 20
        line_thickness = 3
        
        def get_center_x(text, font):
            try:
                text_width = draw.textlength(text, font=font)
            except AttributeError:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
            return (img_width - text_width) // 2
        
        theme_cleaned = remove_emoji(theme)
        if not theme_cleaned:
            theme_cleaned = "Народный календарь"
        
        month_x = get_center_x(month, font_month)
        month_y = start_y
        draw.text((month_x, month_y), month, font=font_month, fill="black")
        
        month_width = draw.textlength(month, font=font_month)
        line1_y = month_y + font_month.size + line_height
        draw.line(
            [(month_x, line1_y), (month_x + month_width, line1_y)],
            fill="black",
            width=line_thickness
        )
        
        date_y = line1_y + line_height * 2
        day_x = get_center_x(day, font_date)
        draw.text((day_x, date_y), day, font=font_date, fill="red")
        
        date_width = draw.textlength(day, font=font_date)
        line2_y = date_y + font_date.size + line_height
        draw.line(
            [(day_x, line2_y), (day_x + date_width, line2_y)],
            fill="black",
            width=line_thickness
        )
        
        theme_y = line2_y + line_height * 2
        theme_lines = []
        max_line_width = img_width * 0.6
        
        words = theme_cleaned.split()
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if draw.textlength(test_line, font=font_theme) <= max_line_width:
                current_line = test_line
            else:
                if current_line:
                    theme_lines.append(current_line)
                current_line = word
        
        if current_line:
            theme_lines.append(current_line)
        
        if not theme_lines or all(not line.strip() for line in theme_lines):
            theme_lines = ["Народный календарь"]
        
        theme_line_spacing = 8
        
        for i, line in enumerate(theme_lines):
            theme_x = get_center_x(line, font_theme)
            current_theme_y = theme_y + i * (font_theme.size + theme_line_spacing)
            draw.text((theme_x, current_theme_y), line, font=font_theme, fill="black")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "JPEG", quality=95)
        logger.info(f"✅ Изображение создано: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании изображения: {e}", exc_info=True)
        return None

def extract_theme_from_post(post_text: str) -> str:
    if not post_text:
        return "Народный календарь"
    
    lines = post_text.strip().split('\n')
    first_line = lines[0] if lines else ""
    
    first_line = re.sub(r'\[\d{1,2}:\d{2}\]', '', first_line).strip()
    
    if not first_line and len(lines) > 1:
        first_line = lines[1].strip()
    
    if len(first_line) > 100:
        first_line = first_line[:97] + "..."
    
    return first_line if first_line else "Народный календарь"

# ==================== ФУНКЦИИ ФОРМАТИРОВАНИЯ ТЕКСТА ====================
def convert_markdown_to_html(text: str) -> str:
    if not text:
        return ""
    try:
        html = markdown2.markdown(text, extras=MARKDOWN_EXTRAS, safe_mode=False)
        return html
    except Exception as e:
        logger.error(f"Ошибка конвертации Markdown в HTML: {e}")
        return text

def escape_html_for_telegram(html_text: str) -> str:
    if not html_text:
        return ""
    html_text = re.sub(r'<h1>(.*?)</h1>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h2>(.*?)</h2>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h3>(.*?)</h3>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h[4-6]>(.*?)</h[4-6]>', r'<b>\1</b>\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<del>(.*?)</del>', r'<s>\1</s>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<strike>(.*?)</strike>', r'<s>\1</s>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<ul>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</ul>', '\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<li>(.*?)</li>', r'• \1\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<ol>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</ol>', '\n', html_text, flags=re.IGNORECASE)
    
    def replace_ol(match):
        items = match.group(1)
        lines = [line.strip() for line in items.split('</li><li>') if line.strip()]
        numbered = '\n'.join([f'{i+1}. {line}' for i, line in enumerate(lines)])
        return numbered + '\n'
    
    html_text = re.sub(r'<ol>(.*?)</ol>', replace_ol, html_text, flags=re.IGNORECASE | re.DOTALL)
    html_text = re.sub(r'<p>(.*?)</p>', r'\1\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<div[^>]*>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</div>', '\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    
    protected_tags = re.findall(r'<(b|i|u|s|code|pre|a)[^>]*>.*?</\1>', html_text, flags=re.IGNORECASE | re.DOTALL)
    for i, tag in enumerate(protected_tags):
        html_text = html_text.replace(tag, f'__PROTECTED_TAG_{i}__')
    html_text = re.sub(r'<[^>]+>', '', html_text)
    for i, tag in enumerate(protected_tags):
        html_text = html_text.replace(f'__PROTECTED_TAG_{i}__', tag)
    
    html_text = html_text.replace('&', '&amp;')
    html_text = html_text.replace('<', '&lt;')
    html_text = html_text.replace('>', '&gt;')
    
    replacements = {
        '&lt;b&gt;': '<b>', '&lt;/b&gt;': '</b>',
        '&lt;i&gt;': '<i>', '&lt;/i&gt;': '</i>',
        '&lt;u&gt;': '<u>', '&lt;/u&gt;': '</u>',
        '&lt;s&gt;': '<s>', '&lt;/s&gt;': '</s>',
        '&lt;code&gt;': '<code>', '&lt;/code&gt;': '</code>',
        '&lt;pre&gt;': '<pre>', '&lt;/pre&gt;': '</pre>',
        '&lt;a href=': '<a href=', '&lt;/a&gt;': '</a>'
    }
    for old, new in replacements.items():
        html_text = html_text.replace(old, new)
    
    def replace_table(match):
        table_html = match.group(0)
        table_text = re.sub(r'<[^>]+>', ' ', table_html)
        table_text = re.sub(r'\s+', ' ', table_text).strip()
        return f'\n📊 Таблица: {table_text[:100]}...\n'
    
    html_text = re.sub(r'<table[^>]*>.*?</table>', replace_table, html_text, flags=re.IGNORECASE | re.DOTALL)
    html_text = re.sub(r'\n{3,}', '\n\n', html_text)
    return html_text.strip()

def format_text_for_telegram(text: str, parse_mode: str = "HTML") -> str:
    if not text:
        return ""
    if parse_mode == "HTML":
        try:
            html_text = convert_markdown_to_html(text)
            telegram_text = escape_html_for_telegram(html_text)
            return telegram_text
        except Exception as e:
            logger.error(f"Ошибка форматирования текста: {e}")
            escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return escape_html_for_telegram(escaped)
    elif parse_mode == "MarkdownV2":
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, '\\' + char)
        return text
    else:
        return text

# ==================== ФУНКЦИИ РАБОТЫ С ТЕКСТОМ ====================
def load_post_for_hour(target_hour: int) -> str:
    now = datetime.now()
    filename = f"{POSTS_DIR}/{now.day:02d}-{now.month:02d}.txt"
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return ""
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filename}: {e}")
        return ""
    posts = {}
    current_hour = None
    current_content = []
    for line in lines:
        raw_line = line.rstrip('\n\r')
        if raw_line.startswith('[') and '] ' in raw_line:
            if current_hour is not None and current_content:
                posts[current_hour] = "\n".join(current_content).strip()
            try:
                time_part = raw_line.split(']')[0][1:]
                hour = int(time_part.split(':')[0])
                current_hour = hour
                content_part = raw_line.split('] ', 1)[1]
                current_content = [content_part] if content_part.strip() else []
            except (IndexError, ValueError):
                current_hour = None
                current_content = []
        else:
            if current_hour is not None:
                current_content.append(raw_line)
    if current_hour is not None and current_content:
        posts[current_hour] = "\n".join(current_content).strip()
    return posts.get(target_hour, "")

# ==================== ФУНКЦИИ БОТА ====================
async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    try:
        utc_hour = datetime.utcnow().hour
        moscow_hour = (utc_hour + 3) % 24
        if moscow_hour not in POST_HOURS:
            return
        post_text = load_post_for_hour(moscow_hour)
        if not post_text or not post_text.strip():
            logger.warning(f"Нет контента для публикации в {moscow_hour}:00 МСК")
            return
        now = datetime.now()
        month_ru = MONTHS_RU[now.month - 1]
        day = now.strftime("%d")
        theme = extract_theme_from_post(post_text)
        if len(post_text) > 4000:
            post_text = post_text[:4000] + "\n\n..."
            logger.warning(f"Пост для {moscow_hour}:00 обрезан до 4000 символов")
        formatted_text = format_text_for_telegram(post_text, parse_mode="HTML")
        image_filename = f"post_{now.day:02d}_{now.month:02d}_{moscow_hour:02d}.jpg"
        image_path = os.path.join(GENERATED_DIR, image_filename)
        created_image = create_post_image(theme, month_ru, day, image_path)
        if created_image and os.path.exists(created_image):
            try:
                with open(created_image, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=CHANNEL,
                        photo=photo,
                        caption=formatted_text,
                        parse_mode="HTML",
                        disable_notification=False
                    )
                logger.info(f"✅ Пост с изображением опубликован в {moscow_hour}:00 МСК")
                return
            except Exception as e:
                logger.error(f"⚠️ Не удалось отправить изображение: {e}")
        await context.bot.send_message(
            chat_id=CHANNEL,
            text=formatted_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            disable_notification=False
        )
        logger.info(f"✅ Текстовый пост опубликован в {moscow_hour}:00 МСК")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при публикации: {e}", exc_info=True)

async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        now = datetime.now()
        month_ru = MONTHS_RU[now.month - 1]
        day = now.strftime("%d")
        theme = "Тестовый пост для проверки генерации изображений"
        image_filename = f"test_{int(datetime.now().timestamp())}.jpg"
        image_path = os.path.join(GENERATED_DIR, image_filename)
        created_image = create_post_image(theme, month_ru, day, image_path)
        test_text = """# 📅 Тестовый пост с изображением

Это тестовое сообщение для проверки работы бота с **Markdown2** форматированием.

## 🎨 Поддерживаемые возможности:

### 1. Заголовки разных уровней
# Заголовок 1 уровня
## Заголовок 2 уровня
### Заголовок 3 уровня

### 2. Форматирование текста
- *Курсив* или _курсив_
- **Жирный текст** или __жирный текст__
- ~~Зачеркнутый текст~~
- `встроенный код`
- [Ссылка на Google](https://google.com)
- <u>Подчеркнутый текст</u>

### 3. Списки
#### Маркированный список:
* Элемент 1
* Элемент 2
  * Вложенный элемент
* Элемент 3

#### Нумерованный список:
1. Первый пункт
2. Второй пункт
   1. Подпункт
   2. Еще подпункт
3. Третий пункт

### 4. Блоки кода
```python
def hello_world():
    print("Привет, мир!")
    return True
        Важно: Бот автоматически генерирует изображения для каждого поста!

📊 Статистика:
Часы публикации: 6:00 - 20:00 МСК
Форматирование: HTML через Markdown2
Изображения: автоматическая генерация
Проверьте канал: Народный календарь
"""
formatted_text = format_text_for_telegram(test_text, parse_mode="HTML")
if created_image and os.path.exists(created_image):
with open(created_image, 'rb') as photo:
await context.bot.send_photo(
chat_id=CHANNEL,
photo=photo,
caption=formatted_text,
parse_mode="HTML"
)
message = "✅ Тестовый пост с изображением отправлен в канал!"
else:
await context.bot.send_message(
chat_id=CHANNEL,
text=formatted_text,
parse_mode="HTML"
)
message = "✅ Тестовый пост отправлен (без изображения)!"
await update.message.reply_text(f"{message}\nПроверьте: {CHANNEL}")
except Exception as e:
error_msg = f"❌ Ошибка при отправке тестового поста: {e}"
logger.error(error_msg)
await update.message.reply_text(error_msg)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
welcome_text = """# 📅 Бот Народный Календарь

Я автоматически публикую посты в канал по расписанию с генерацией изображений и Markdown форматированием.

🖼️ Формат изображения:
Месяц (черный текст)
Черта разделитель
Дата (красный текст, крупно)
Черта разделитель
Тема поста (черный текст)

📝 Поддерживаемое форматирование в постах:

Курсив или курсив
Жирный текст или жирный текст
Зачеркнутый текст
<u>Подчеркнутый текст</u>
встроенный код
Заголовки (#, ##, ###)
Списки
Таблицы
Блоки кода
Цитаты
Ссылки
🎯 Команды бота:
/start - это приветственное сообщение
/test - отправить тестовый пост с изображением
/status - информация о состоянии бота

⚙️ Настройки:
Канал: Народный календарь
Часы публикации (МСК): 6:00 - 20:00 каждый час
Форматирование: HTML (через Markdown2)
Генерация изображений: Включена
"""
formatted_text = format_text_for_telegram(welcome_text, parse_mode="HTML")
await update.message.reply_text(formatted_text, parse_mode="HTML")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
now = datetime.now()
utc_hour = now.hour
moscow_hour = (utc_hour + 3) % 24
checks = {
"Фон (fon.jpg)": os.path.exists(BACKGROUND_FILE),
"Шрифт (GOST_A.TTF)": os.path.exists(FONT_FILE),
"Папка с постами": os.path.exists(POSTS_DIR),
"Папка для изображений": os.path.exists(GENERATED_DIR),
}
check_results = "\n".join([f"{'✅' if status else '❌'} {name}" for name, status in checks.items()])
filename = f"{POSTS_DIR}/{now.day:02d}-{now.month:02d}.txt"
file_exists = os.path.exists(filename)
post_files = [f for f in os.listdir(POSTS_DIR) if f.endswith('.txt')] if os.path.exists(POSTS_DIR) else []
status_text = f"""# 📊 Статус бота
📅 Текущее состояние:
Время сервера: {now.strftime('%H:%M:%S')} UTC
Время МСК: {(utc_hour + 3) % 24}:{now.strftime('%M:%S')}
Дата: {now.strftime('%d.%m.%Y')}
Час МСК для публикации: {moscow_hour}
Файл на сегодня: {'✅' if file_exists else '❌'} {filename}
Следующий пост: {'✅ Скоро' if moscow_hour in POST_HOURS else '⏸️ Не сегодня'}

📁 Проверка файлов:
{check_results}

📈 Статистика:
Файлов с постами: {len(post_files)}
Часов публикации: {len(POST_HOURS)} (с {POST_HOURS[0]}:00 до {POST_HOURS[-1]}:00 МСК)
Режим форматирования: HTML (через Markdown2)
Генерация изображений: {'✅ Включена' if os.path.exists(BACKGROUND_FILE) and os.path.exists(FONT_FILE) else '❌ Выключена'}

⚙️ Конфигурация:
Канал: {CHANNEL}
Папка с постами: {POSTS_DIR}/
Папка изображений: {GENERATED_DIR}/
"""
formatted_text = format_text_for_telegram(status_text, parse_mode="HTML")
await update.message.reply_text(formatted_text, parse_mode="HTML")

==================== ЗАПУСК БОТА ====================
def main():
if not BOT_TOKEN:
logger.error("❌ ОШИБКА: BOT_TOKEN не задан!")
logger.error("Задайте переменную окружения: export BOT_TOKEN='ваш_токен'")
return
if not CHANNEL:
logger.error("❌ ОШИБКА: CHANNEL не задан!")
return
directories = [POSTS_DIR, ASSETS_DIR, FONTS_DIR, GENERATED_DIR]
for directory in directories:
if not os.path.exists(directory):
os.makedirs(directory)
logger.info(f"📁 Создана директория: {directory}")
if not os.path.exists(BACKGROUND_FILE):
logger.warning(f"⚠️ Фоновое изображение не найдено: {BACKGROUND_FILE}")
logger.warning("Поместите файл fon.jpg (1600x1124) в папку assets/")
if not os.path.exists(FONT_FILE):
logger.warning(f"⚠️ Шрифт не найден: {FONT_FILE}")
logger.warning("Поместите файл GOST_A.TTF в папку fonts/")
try:
app = Application.builder().token(BOT_TOKEN).build()
logger.info("✅ Приложение инициализировано")
except Exception as e:
logger.error(f"❌ Ошибка инициализации бота: {e}")
return
app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("test", cmd_test))
app.add_handler(CommandHandler("status", cmd_status))
logger.info("✅ Команды зарегистрированы")
job_added = 0
for hour_msk in POST_HOURS:
utc_hour = (hour_msk - 3) % 24
app.job_queue.run_daily(
send_scheduled_post,
time(hour=utc_hour, minute=0, second=10),
name=f"post_{hour_msk:02d}"
)
job_added += 1
logger.info(f"✅ Настроено {job_added} заданий по расписанию")
logger.info(f"📢 Бот будет публиковать в канал: {CHANNEL}")
logger.info(f"⏰ Часы публикации (МСК): {POST_HOURS}")
logger.info("🎨 Режим: генерация изображений + HTML форматирование (через Markdown2)")
logger.info("=" * 50)
logger.info("🚀 Бот запущен и готов к работе!")
try:
app.run_polling(drop_pending_updates=True)
except KeyboardInterrupt:
logger.info("⏹️ Бот остановлен пользователем")
except Exception as e:
logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)

if name == "main":
main()
