#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для публикации постов из текстовых файлов с поддержкой MarkdownV2.
Форматирование: *жирный*, _курсив_, __подчеркивание__, [ссылки](url), `код`
"""

import os
import logging
import re
from datetime import datetime, time
from telegram.ext import Application, CommandHandler, ContextTypes

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
# Получаем настройки из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@narodny_kalendar").strip()
POSTS_DIR = "posts"  # Директория с файлами постов

# Часы публикации по Московскому времени (UTC+3)
POST_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

# ==================== ФУНКЦИИ ОБРАБОТКИ ТЕКСТА ====================
def escape_markdown_v2(text: str) -> str:
    """
    Корректно экранирует спецсимволы для Telegram MarkdownV2.
    Сохраняет форматирование: *жирный*, _курсив_, __подчеркнутый__,
    `код`, ```блок кода``` и [ссылки](url).
    
    Args:
        text: Исходный текст с Markdown разметкой
        
    Returns:
        Текст с экранированными спецсимволами, готовый к отправке
        с parse_mode="MarkdownV2"
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Символы, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Словарь для временного хранения защищенных блоков
    protected_blocks = {}
    block_counter = 0
    
    def create_protector(name):
        """Фабрика функций для защиты блоков форматирования"""
        nonlocal block_counter
        def protector(match):
            nonlocal block_counter
            block_id = f"__{name}_{block_counter}__"
            protected_blocks[block_id] = match.group(0)
            block_counter += 1
            return block_id
        return protector
    
    # Создаем защитники для разных типов форматирования
    protectors = {
        'CODE_BLOCK': create_protector('CODE_BLOCK'),
        'INLINE_CODE': create_protector('INLINE_CODE'),
        'LINK': create_protector('LINK'),
        'BOLD': create_protector('BOLD'),
        'UNDERLINE': create_protector('UNDERLINE'),
        'ITALIC_UNDERSCORE': create_protector('ITALIC_US'),
        'ITALIC_ASTERISK': create_protector('ITALIC_AST')
    }
    
    # Шаг 1: Защищаем блоки форматирования (в порядке от сложных к простым)
    # 1. Блоки кода (многострочные) ```
    text = re.sub(r'```[\s\S]*?```', protectors['CODE_BLOCK'], text)
    # 2. Inline-код `
    text = re.sub(r'`[^`\n]+`', protectors['INLINE_CODE'], text)
    # 3. Ссылки [текст](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', protectors['LINK'], text)
    # 4. Жирный текст **текст**
    text = re.sub(r'\*\*([^*]+)\*\*', protectors['BOLD'], text)
    # 5. Подчеркивание __текст__
    text = re.sub(r'__([^_]+)__', protectors['UNDERLINE'], text)
    # 6. Курсив через _текст_
    text = re.sub(r'_([^_\n]+)_', protectors['ITALIC_UNDERSCORE'], text)
    # 7. Курсив через *текст*
    text = re.sub(r'\*([^*\n]+)\*', protectors['ITALIC_ASTERISK'], text)
    
    # Шаг 2: Экранируем все опасные символы
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    # Шаг 3: Восстанавливаем защищенные блоки
    for block_id, original_content in protected_blocks.items():
        text = text.replace(block_id, original_content)
    
    return text

def load_post_for_hour(target_hour: int) -> str:
    """
    Загружает пост для указанного часа из файла с текущей датой.
    
    Args:
        target_hour: Час по Московскому времени
        
    Returns:
        Текст поста или пустая строка, если пост не найден
    """
    now = datetime.now()
    filename = f"{POSTS_DIR}/{now.day:02d}-{now.month:02d}.txt"
    
    # Проверяем существование файла
    if not os.path.exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        return ""
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filename}: {e}")
        return ""
    
    # Парсим файл: формат [ЧЧ:ММ] текст
    posts = {}
    current_hour = None
    current_content = []
    
    for line_num, line in enumerate(lines, 1):
        raw_line = line.rstrip('\n\r')
        
        # Если строка начинается с [ЧЧ:ММ] - это начало нового поста
        if raw_line.startswith('[') and '] ' in raw_line:
            # Сохраняем предыдущий пост
            if current_hour is not None and current_content:
                posts[current_hour] = "\n".join(current_content).strip()
            
            # Парсим время нового поста
            try:
                time_part = raw_line.split(']')[0][1:]  # Убираем [ и ]
                hour = int(time_part.split(':')[0])
                current_hour = hour
                content_part = raw_line.split('] ', 1)[1]
                current_content = [content_part] if content_part.strip() else []
            except (IndexError, ValueError) as e:
                logger.warning(f"Ошибка парсинга строки {line_num}: {raw_line}")
                current_hour = None
                current_content = []
        else:
            # Продолжение текущего поста
            if current_hour is not None:
                current_content.append(raw_line)
    
    # Сохраняем последний пост в файле
    if current_hour is not None and current_content:
        posts[current_hour] = "\n".join(current_content).strip()
    
    return posts.get(target_hour, "")

# ==================== ФУНКЦИИ БОТА ====================
async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """
    Функция, вызываемая по расписанию для публикации постов.
    Определяет текущий час по МСК и публикует соответствующий пост.
    """
    try:
        # Определяем текущий час по Московскому времени (UTC+3)
        utc_hour = datetime.utcnow().hour
        moscow_hour = (utc_hour + 3) % 24
        
        logger.debug(f"Текущий час: UTC={utc_hour}, МСК={moscow_hour}")
        
        # Проверяем, нужно ли публиковать в этот час
        if moscow_hour not in POST_HOURS:
            return
        
        # Загружаем пост для текущего часа
        post_text = load_post_for_hour(moscow_hour)
        
        if not post_text or not post_text.strip():
            logger.warning(f"Нет контента для публикации в {moscow_hour}:00 МСК")
            return
        
        # Проверяем длину поста (ограничение Telegram: 4096 символов)
        if len(post_text) > 4000:
            post_text = post_text[:4000] + "\n\n..."
            logger.warning(f"Пост для {moscow_hour}:00 обрезан до 4000 символов")
        
        # Экранируем текст для MarkdownV2
        safe_text = escape_markdown_v2(post_text)
        
        # Публикуем пост в канал
        await context.bot.send_message(
            chat_id=CHANNEL,
            text=safe_text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            disable_notification=False  # Уведомления включены
        )
        
        logger.info(f"✅ Пост опубликован в {moscow_hour}:00 МСК")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при публикации: {e}", exc_info=True)

async def cmd_test(update, context):
    """
    Команда /test - отправляет тестовый пост (для 8:00)
    """
    try:
        post_text = load_post_for_hour(8)
        
        if not post_text:
            post_text = (
                "*Тестовый пост*\n\n"
                "Это тестовое сообщение с __разными__ стилями:\n"
                "- *Курсив*\n"
                "- **Жирный текст**\n"
                "- __Подчеркивание__\n"
                "- `Встроенный код`\n"
                "- [Ссылка на Google](https://google.com)\n\n"
                "```python\nprint('Блок кода')\n```"
            )
        
        safe_text = escape_markdown_v2(post_text)
        
        await context.bot.send_message(
            chat_id=CHANNEL,
            text=safe_text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        
        await update.message.reply_text(
            "✅ Тестовый пост отправлен в канал!\n"
            f"Проверьте: {CHANNEL}"
        )
        
    except Exception as e:
        error_msg = f"❌ Ошибка при отправке тестового поста: {e}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)

async def cmd_start(update, context):
    """
    Команда /start - приветственное сообщение
    """
    welcome_text = (
        "🤖 *Бот Народный Календарь*\n\n"
        "Я публикую посты в канал по расписанию.\n\n"
        "*Поддерживаемое форматирование:*\n"
        "• *Курсив* или _Курсив_\n"
        "• **Жирный текст**\n"
        "• __Подчеркивание__\n"
        "• `Встроенный код`\n"
        "• ```Блок кода```\n"
        "• [Ссылки](https://example.com)\n\n"
        "*Команды:*\n"
        "/start - это сообщение\n"
        "/test - отправить тестовый пост\n\n"
        f"Канал: {CHANNEL}\n"
        f"Часы публикации (МСК): {', '.join(map(str, POST_HOURS))}"
    )
    
    await update.message.reply_text(
        escape_markdown_v2(welcome_text),
        parse_mode="MarkdownV2"
    )

async def cmd_status(update, context):
    """
    Команда /status - информация о состоянии бота
    """
    now = datetime.now()
    utc_hour = now.hour
    moscow_hour = (utc_hour + 3) % 24
    
    # Проверяем наличие файла на сегодня
    filename = f"{POSTS_DIR}/{now.day:02d}-{now.month:02d}.txt"
    file_exists = os.path.exists(filename)
    
    status_text = (
        f"📊 *Статус бота*\n\n"
        f"• *Время:* {now.strftime('%H:%M:%S')}\n"
        f"• *Дата:* {now.strftime('%d.%m.%Y')}\n"
        f"• *Час МСК:* {moscow_hour}\n"
        f"• *Файл на сегодня:* {'✅' if file_exists else '❌'} {filename}\n"
        f"• *Следующий пост:* {'Скоро' if moscow_hour in POST_HOURS else 'Не сегодня'}\n"
        f"• *Часы публикации (МСК):* {', '.join(map(str, POST_HOURS))}\n\n"
        f"_Бот работает в режиме MarkdownV2_"
    )
    
    await update.message.reply_text(
        escape_markdown_v2(status_text),
        parse_mode="MarkdownV2"
    )

# ==================== ЗАПУСК БОТА ====================
def main():
    """Основная функция запуска бота"""
    
    # Проверка обязательных переменных
    if not BOT_TOKEN:
        logger.error("❌ ОШИБКА: BOT_TOKEN не задан!")
        logger.error("Задайте переменную окружения: export BOT_TOKEN='ваш_токен'")
        return
    
    if not CHANNEL:
        logger.error("❌ ОШИБКА: CHANNEL не задан!")
        return
    
    # Создаем директорию для постов, если её нет
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
        logger.info(f"📁 Создана директория для постов: {POSTS_DIR}")
        logger.info(f"📝 Пример файла: {POSTS_DIR}/07-01.txt")
    
    # Инициализация приложения
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        logger.info("✅ Приложение инициализировано")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        return
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("status", cmd_status))
    logger.info("✅ Команды зарегистрированы")
    
    # Настройка расписания
    job_added = 0
    for hour_msk in POST_HOURS:
        # Конвертируем МСК в UTC (МСК = UTC+3)
        utc_hour = (hour_msk - 3) % 24
        app.job_queue.run_daily(
            send_scheduled_post,
            time(hour=utc_hour, minute=0, second=10),  # +10 секунд для надежности
            name=f"post_{hour_msk:02d}"
        )
        job_added += 1
    
    logger.info(f"✅ Настроено {job_added} заданий по расписанию")
    logger.info(f"📢 Бот будет публиковать в канал: {CHANNEL}")
    logger.info(f"🕐 Часы публикации (МСК): {POST_HOURS}")
    logger.info("✨ Бот запущен. Ожидание команд и срабатывания таймеров...")
    logger.info("=" * 50)
    
    # Запуск бота
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)

if __name__ == "__main__":
    main()
