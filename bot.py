#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для публикации постов с автоматической генерацией изображений.
Поддерживает форматирование через Markdown2 (заголовки, списки, таблицы, код и т.д.)
Генерация изображений: фон + текст (месяц, дата, тема)
"""

import os
import logging
import re
import markdown2
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont  # Для генерации изображений

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
POSTS_DIR = "posts"                # Папка с текстовыми постами
ASSETS_DIR = "assets"              # Папка с фоном
FONTS_DIR = "fonts"                # Папка со шрифтами
GENERATED_DIR = "generated_images" # Папка для сгенерированных изображений

# Файлы
BACKGROUND_FILE = os.path.join(ASSETS_DIR, "fon.jpg")   # Фон 1600x1124
FONT_FILE = os.path.join(FONTS_DIR, "GOST_A.TTF")       # Основной шрифт

# Часы публикации по Московскому времени (UTC+3)
POST_HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

# Русские названия месяцев
MONTHS_RU = [
    "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ",
    "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"
]

# Настройки markdown2
MARKDOWN_EXTRAS = [
    'fenced-code-blocks',  # Блоки кода с обратными апострофами
    'tables',              # Таблицы
    'break-on-newline',    # Перенос строк на одинарных переводах
    'cuddled-lists',       # Более компактные списки
    'markdown-in-html',    # Разрешить markdown внутри HTML
    'spoiler',             # Скрытый текст
    'strike',              # Зачеркнутый текст
    'target-blank-links',  # Открывать ссылки в новой вкладке
    'header-ids',          # Добавлять ID к заголовкам
    'pyshell',             # Подсветка кода Python
]

# ==================== ФУНКЦИИ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ ====================
def create_post_image(theme: str, month: str, day: str, output_path: str) -> str:
    """
    Создает изображение для поста по шаблону.
    
    Args:
        theme: Тема поста (например, "ДЕНЬ В ИСТОРИИ: Луи Дагер")
        month: Название месяца (например, "ЯНВАРЬ")
        day: Число дня (например, "07")
        output_path: Путь для сохранения готового изображения
        
    Returns:
        Путь к созданному изображению или None в случае ошибки
    """
    
    def remove_emoji_and_special(text):
        """
        Удаляет эмодзи и специальные символы, оставляя только кириллицу, латиницу, цифры и основные знаки препинания.
        """
        if not text:
            return ""
        
        # Расширенный шаблон для эмодзи и специальных символов
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # эмотиконы
            u"\U0001F300-\U0001F5FF"  # символы и пиктограммы
            u"\U0001F680-\U0001F6FF"  # транспорт и карта
            u"\U0001F1E0-\U0001F1FF"  # флаги (iOS)
            u"\U00002500-\U00002BEF"  # различные символы
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"  # символ соединения (для составных эмодзи)
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # вариационный селектор-16
            u"\u3030"
            u"\u00A9\u00AE\u2122"  # знаки авторского права, товарные знаки
            "]+",
            flags=re.UNICODE,
        )
        
        # Удаляем эмодзи по шаблону
        text = emoji_pattern.sub(r'', text)
        
        # Дополнительно: удаляем оставшиеся непечатные и специальные символы,
        # оставляя только кириллицу, латиницу, цифры, пробелы и основные знаки препинания
        allowed_chars_pattern = re.compile(
            r'[^'
            r'a-zA-Zа-яА-ЯёЁ'  # латиница и кириллица
            r'0-9'             # цифры
            r'\s'              # пробелы
            r'.,:;!?\-–—()\[\]{}«»"\''
            r']+'
        )
        text = allowed_chars_pattern.sub(r'', text)
        
        return text.strip()
    
    try:
        # Проверяем наличие необходимых файлов
        if not os.path.exists(BACKGROUND_FILE):
            logger.error(f"Фоновое изображение не найдено: {BACKGROUND_FILE}")
            return None
        
        if not os.path.exists(FONT_FILE):
            logger.error(f"Шрифт не найден: {FONT_FILE}")
            return None
        
        # 1. Открываем фоновое изображение
        img = Image.open(BACKGROUND_FILE)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size
        
        # 2. Загружаем шрифты с разными размерами (оптимизированные для компактности)
        font_month = ImageFont.truetype(FONT_FILE, 90)      # Месяц
        font_date = ImageFont.truetype(FONT_FILE, 150)      # Дата (крупно)
        font_theme = ImageFont.truetype(FONT_FILE, 90)      # Тема
        
        # 3. Координаты и параметры (оптимизированные для более компактного и нижнего расположения)
        start_y = 220                    # Начальная позиция по Y (сдвинута вниз)
        line_height = 20                 # Расстояние между элементами
        line_thickness = 3               # Толщина черт
        
        # Функция для расчета центральной позиции по X
        def get_center_x(text, font):
            # Используем textlength для новых версий Pillow
            try:
                text_width = draw.textlength(text, font=font)
            except AttributeError:
                # Для старых версий Pillow
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
            return (img_width - text_width) // 2
        
        # ========== ВАЖНО: ОЧИСТКА ТЕМЫ ПЕРЕД ИСПОЛЬЗОВАНИЕМ ==========
        # Логируем исходную тему для отладки
        logger.debug(f"[ГЕНЕРАТОР] Тема ДО очистки: {repr(theme)}")
        
        # Очищаем тему от эмодзи и специальных символов
        theme_cleaned = remove_emoji_and_special(theme)
        
        # Логируем результат очистки
        logger.debug(f"[ГЕНЕРАТОР] Тема ПОСЛЕ очистки: {repr(theme_cleaned)}")
        
        # Используем очищенную тему для дальнейшей обработки
        theme = theme_cleaned
        # =============================================================
        
        # 4. Рисуем месяц (черный)
        month_x = get_center_x(month, font_month)
        month_y = start_y
        draw.text((month_x, month_y), month, font=font_month, fill="black")
        
        # 5. Черта под месяцем
        month_width = draw.textlength(month, font=font_month)
        line1_y = month_y + font_month.size + line_height
        draw.line(
            [(month_x, line1_y), (month_x + month_width, line1_y)],
            fill="black",
            width=line_thickness
        )
        
        # 6. Рисуем дату (красная, крупно)
        date_y = line1_y + line_height * 2
        day_x = get_center_x(day, font_date)
        draw.text((day_x, date_y), day, font=font_date, fill="red")
        
        # 7. Черта под датой
        date_width = draw.textlength(day, font=font_date)
        line2_y = date_y + font_date.size + line_height
        draw.line(
            [(day_x, line2_y), (day_x + date_width, line2_y)],
            fill="black",
            width=line_thickness
        )
        
        # 8. Рисуем тему поста (черный)
        theme_y = line2_y + line_height * 2
        
        # Улучшенный перенос строк: используем ширину изображения вместо фиксированного количества символов
        theme_lines = []
        max_line_width = img_width * 0.6  # Максимальная ширина строки - 80% от ширины изображения
        
        words = theme.split()
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            # Проверяем ширину строки с новым словом
            if draw.textlength(test_line, font=font_theme) <= max_line_width:
                current_line = test_line
            else:
                if current_line:  # Сохраняем текущую строку, если она не пустая
                    theme_lines.append(current_line)
                current_line = word  # Начинаем новую строку с текущего слова
        
        if current_line:  # Добавляем последнюю строку
            theme_lines.append(current_line)
        
        # Если после очистки тема стала пустой, используем заглушку
        if not theme_lines or all(not line.strip() for line in theme_lines):
            theme_lines = ["Народный календарь"]
            logger.debug("[ГЕНЕРАТОР] Тема оказалась пустой после очистки, использована заглушка")
        
        # Рисуем каждую строку темы (с уменьшенным межстрочным интервалом)
        theme_line_spacing = 8
        
        for i, line in enumerate(theme_lines):
            theme_x = get_center_x(line, font_theme)
            current_theme_y = theme_y + i * (font_theme.size + theme_line_spacing)
            draw.text((theme_x, current_theme_y), line, font=font_theme, fill="black")
        
        # 9. Создаем папку для результата, если её нет
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 10. Сохраняем изображение
        img.save(output_path, "JPEG", quality=95)
        logger.info(f"✅ Изображение создано: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании изображения: {e}", exc_info=True)
        return None

def extract_theme_from_post(post_text: str) -> str:
    """
    Извлекает тему поста из текста.
    
    Args:
        post_text: Полный текст поста
        
    Returns:
        Тема поста или заглушка, если тему извлечь не удалось
    """
    if not post_text:
        return "Народный календарь"
    
    # Берем первую строку текста (после времени, если есть)
    lines = post_text.strip().split('\n')
    first_line = lines[0] if lines else ""
    
    # Убираем временную метку вида [ЧЧ:ММ]
    first_line = re.sub(r'\[\d{1,2}:\d{2}\]', '', first_line).strip()
    
    # Если строка осталась пустой, берем следующую
    if not first_line and len(lines) > 1:
        first_line = lines[1].strip()
    
    # Ограничиваем длину темы
    if len(first_line) > 100:
        first_line = first_line[:97] + "..."
    
    return first_line if first_line else "Народный календарь"

# ==================== ФУНКЦИИ ФОРМАТИРОВАНИЯ ТЕКСТА ====================
def convert_markdown_to_html(text: str) -> str:
    """
    Конвертирует Markdown текст в HTML с поддержкой расширений.
    
    Args:
        text: Исходный текст в формате Markdown
        
    Returns:
        Текст в формате HTML
    """
    if not text:
        return ""
    
    try:
        # Конвертируем Markdown в HTML
        html = markdown2.markdown(
            text,
            extras=MARKDOWN_EXTRAS,
            safe_mode=False
        )
        return html
    except Exception as e:
        logger.error(f"Ошибка конвертации Markdown в HTML: {e}")
        return text

def escape_html_for_telegram(html_text: str) -> str:
    """
    Экранирует HTML-теги для Telegram.
    Telegram поддерживает ограниченный набор HTML-тегов.
    
    Args:
        html_text: HTML текст после конвертации из Markdown
        
    Returns:
        Текст, безопасный для отправки в Telegram
    """
    if not html_text:
        return ""
    
    # Telegram поддерживает только: <b>, <i>, <u>, <s>, <code>, <pre>, <a>
    # Заменяем другие теги на эквивалентное форматирование
    
    # Сначала заменяем заголовки на жирный текст с переносом строк
    html_text = re.sub(r'<h1>(.*?)</h1>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h2>(.*?)</h2>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h3>(.*?)</h3>', r'<b>\1</b>\n\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<h[4-6]>(.*?)</h[4-6]>', r'<b>\1</b>\n', html_text, flags=re.IGNORECASE)
    
    # Заменяем <strong> на <b> и <em> на <i>
    html_text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', html_text, flags=re.IGNORECASE)
    
    # Заменяем <del>, <strike> на <s>
    html_text = re.sub(r'<del>(.*?)</del>', r'<s>\1</s>', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<strike>(.*?)</strike>', r'<s>\1</s>', html_text, flags=re.IGNORECASE)
    
    # Обрабатываем списки
    # Заменяем <ul> и <li> на символы
    html_text = re.sub(r'<ul>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</ul>', '\n', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'<li>(.*?)</li>', r'• \1\n', html_text, flags=re.IGNORECASE)
    
    # Обрабатываем нумерованные списки
    html_text = re.sub(r'<ol>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</ol>', '\n', html_text, flags=re.IGNORECASE)
    
    def replace_ol(match):
        items = match.group(1)
        # Простая замена - нумеруем все пункты подряд
        lines = [line.strip() for line in items.split('</li><li>') if line.strip()]
        numbered = '\n'.join([f'{i+1}. {line}' for i, line in enumerate(lines)])
        return numbered + '\n'
    
    html_text = re.sub(r'<ol>(.*?)</ol>', replace_ol, html_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Заменяем абзацы на переносы строк
    html_text = re.sub(r'<p>(.*?)</p>', r'\1\n', html_text, flags=re.IGNORECASE)
    
    # Удаляем <div> теги, оставляя содержимое
    html_text = re.sub(r'<div[^>]*>', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'</div>', '\n', html_text, flags=re.IGNORECASE)
    
    # Заменяем <br> на перенос строки
    html_text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    
    # Удаляем все остальные HTML-теги, кроме разрешенных Telegram
    # Сначала защитим разрешенные теги
    protected_tags = re.findall(r'<(b|i|u|s|code|pre|a)[^>]*>.*?</\1>', html_text, flags=re.IGNORECASE | re.DOTALL)
    for i, tag in enumerate(protected_tags):
        html_text = html_text.replace(tag, f'__PROTECTED_TAG_{i}__')
    
    # Удаляем все оставшиеся HTML-теги
    html_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Восстанавливаем защищенные теги
    for i, tag in enumerate(protected_tags):
        html_text = html_text.replace(f'__PROTECTED_TAG_{i}__', tag)
    
    # Экранируем специальные символы HTML
    html_text = html_text.replace('&', '&amp;')
    html_text = html_text.replace('<', '&lt;')
    html_text = html_text.replace('>', '&gt;')
    
    # Восстанавливаем разрешенные теги
    html_text = html_text.replace('&lt;b&gt;', '<b>')
    html_text = html_text.replace('&lt;/b&gt;', '</b>')
    html_text = html_text.replace('&lt;i&gt;', '<i>')
    html_text = html_text.replace('&lt;/i&gt;', '</i>')
    html_text = html_text.replace('&lt;u&gt;', '<u>')
    html_text = html_text.replace('&lt;/u&gt;', '</u>')
    html_text = html_text.replace('&lt;s&gt;', '<s>')
    html_text = html_text.replace('&lt;/s&gt;', '</s>')
    html_text = html_text.replace('&lt;code&gt;', '<code>')
    html_text = html_text.replace('&lt;/code&gt;', '</code>')
    html_text = html_text.replace('&lt;pre&gt;', '<pre>')
    html_text = html_text.replace('&lt;/pre&gt;', '</pre>')
    html_text = html_text.replace('&lt;a href=', '<a href=')
    html_text = html_text.replace('&lt;/a&gt;', '</a>')
    
    # Обрабатываем таблицы (простая замена на текстовый формат)
    def replace_table(match):
        table_html = match.group(0)
        # Удаляем все HTML-теги из таблицы
        table_text = re.sub(r'<[^>]+>', ' ', table_html)
        table_text = re.sub(r'\s+', ' ', table_text).strip()
        return f'\n📊 Таблица: {table_text[:100]}...\n'
    
    html_text = re.sub(r'<table[^>]*>.*?</table>', replace_table, html_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Убираем лишние переносы строк
    html_text = re.sub(r'\n{3,}', '\n\n', html_text)
    
    return html_text.strip()

def format_text_for_telegram(text: str, parse_mode: str = "HTML") -> str:
    """
    Форматирует текст для Telegram с поддержкой Markdown и HTML.
    
    Args:
        text: Исходный текст
        parse_mode: Режим форматирования ("HTML" или "MarkdownV2")
        
    Returns:
        Отформатированный текст
    """
    if not text:
        return ""
    
    if parse_mode == "HTML":
        try:
            # Сначала конвертируем Markdown в HTML
            html_text = convert_markdown_to_html(text)
            
            # Затем экранируем для Telegram
            telegram_text = escape_html_for_telegram(html_text)
            
            return telegram_text
        except Exception as e:
            logger.error(f"Ошибка форматирования текста: {e}")
            # Возвращаем оригинальный текст в случае ошибки
            return escape_html_for_telegram(text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    
    elif parse_mode == "MarkdownV2":
        # Экранирование для MarkdownV2 (оставлено для совместимости)
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, '\\' + char)
        return text
    
    else:
        # Простой текст без форматирования
        return text

# ==================== ФУНКЦИИ РАБОТЫ С ТЕКСТОМ ====================
def load_post_for_hour(target_hour: int) -> str:
    """
    Загружает пост для указанного часа из файла с текущей датой.
    
    Args:
        target_hour: Час для загрузки (по МСК)
        
    Returns:
        Текст поста или пустая строка
    """
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
    
    for line_num, line in enumerate(lines, 1):
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
    """
    Функция, вызываемая по расписанию для публикации постов с изображениями.
    """
    try:
        # Определяем текущий час по МСК
        utc_hour = datetime.utcnow().hour
        moscow_hour = (utc_hour + 3) % 24
        
        if moscow_hour not in POST_HOURS:
            return
        
        # Загружаем пост для текущего часа
        post_text = load_post_for_hour(moscow_hour)
        
        if not post_text or not post_text.strip():
            logger.warning(f"Нет контента для публикации в {moscow_hour}:00 МСК")
            return
        
        # Получаем текущую дату
        now = datetime.now()
        month_ru = MONTHS_RU[now.month - 1]
        day = now.strftime("%d")
        
        # Извлекаем тему поста
        theme = extract_theme_from_post(post_text)
        
        # Проверяем длину поста (ограничение Telegram)
        if len(post_text) > 4000:
            post_text = post_text[:4000] + "\n\n..."
            logger.warning(f"Пост для {moscow_hour}:00 обрезан до 4000 символов")
        
        # Форматируем текст с использованием markdown2
        formatted_text = format_text_for_telegram(post_text, parse_mode="HTML")
        
        # Создаем уникальное имя файла для изображения
        image_filename = f"post_{now.day:02d}_{now.month:02d}_{moscow_hour:02d}.jpg"
        image_path = os.path.join(GENERATED_DIR, image_filename)
        
        # 1. Создаем и отправляем изображение
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
                # Продолжаем с отправкой текста
        
        # 2. Если изображение не создалось, отправляем только текст
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

async def cmd_test(update, context):
    """
    Команда /test - отправляет тестовый пост с изображением
    """
    try:
        now = datetime.now()
        month_ru = MONTHS_RU[now.month - 1]
        day = now.strftime("%d")
        theme = "Тестовый пост для проверки генерации изображений"
        
        # Создаем тестовое изображение
        image_filename = f"test_{int(datetime.now().timestamp())}.jpg"
        image_path = os.path.join(GENERATED_DIR, image_filename)
        
        created_image = create_post_image(theme, month_ru, day, image_path)
        
        # Тестовый текст с Markdown форматированием
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
