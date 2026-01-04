# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os
import json
from datetime import datetime
import random

# Размер горизонтальной карточки
CARD_WIDTH = 1200
CARD_HEIGHT = 630

# Цветовая палитра (упрощённая)
COLORS = {
    "bg_light": (245, 240, 235),
    "text_dark": (40, 35, 30),
    "text_light": (100, 90, 80),
    "accent_gold": (180, 150, 100),
    "accent_green": (120, 150, 110),
    "accent_blue": (100, 130, 150),
    "accent_red": (170, 100, 90),
}

# Путь к папке с данными
DATA_DIR = "data"

def load_data_for_day(theme, day, month):
    """Загружает данные для конкретного дня и темы из JSON-файлов"""
    try:
        theme_files = {
            "primeta": "primety.json", "saint": "saints.json", "holiday": "holidays.json",
            "hero": "heroes.json", "actor": "actors.json", "wisdom": "wisdom.json",
            "lunar": "lunar.json", "history": "history.json", "herbal": "herbal.json",
            "art": "art.json", "food": "food.json", "house": "house.json",
            "craft": "craft.json", "advice": "advice.json", "prayer": "prayers.json",
        }
        
        filename = theme_files.get(theme)
        if not filename:
            return get_default_data(theme)
        
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            return get_default_data(theme)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{day}-{month}"
        return data.get(key, get_default_data(theme))
            
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return get_default_data(theme)

def get_default_data(theme):
    """Возвращает данные по умолчанию для темы"""
    defaults = {
        "primeta": {"text": "Сегодня особый день. Природа подсказывает: наблюдайте за знаками вокруг."},
        "saint": {
            "name": "Святой угодник",
            "description": "Почитаемый святой, молитвенник и заступник.",
            "prayer": "Господи, помилуй нас по молитвам святых Твоих."
        },
        "holiday": {
            "title": "День в календаре",
            "description": "Этот день имеет особое значение в традициях нашего народа.",
            "orthodox": "Церковь чтит память святых этого дня.",
            "state": "День, отмеченный в истории нашего Отечества."
        },
        "hero": {
            "name": "Герой Отечества",
            "bio": "Пример мужества, верности и любви к Родине.",
            "deed": "Подвиг, который остаётся в памяти поколений.",
            "full_story": "Их жизнь - пример для подражания. Они шли на подвиг не ради славы, а ради Родины, ради нас с вами."
        },
        "actor": {
            "name": "Советский актёр",
            "years": "XXXX-XXXX",
            "bio": "Талантливый артист, чьё творчество стало частью нашей культуры.",
            "roles": "Замечательные роли в кино и театре.",
        },
    }
    return defaults.get(theme, {"text": "Сегодня день для размышлений о традициях и мудрости."})

def get_color_by_theme(theme):
    """Возвращает цвет акцента по теме поста"""
    colors = {
        "primeta": COLORS["accent_green"], "saint": COLORS["accent_gold"],
        "holiday": COLORS["accent_red"], "hero": COLORS["accent_red"],
        "lunar": COLORS["accent_blue"], "wisdom": COLORS["accent_gold"],
        "history": COLORS["accent_blue"], "herbal": COLORS["accent_green"],
        "art": COLORS["accent_gold"], "food": COLORS["accent_red"],
        "house": COLORS["accent_green"], "craft": COLORS["accent_blue"],
        "actor": COLORS["accent_gold"], "advice": COLORS["accent_green"],
        "prayer": COLORS["accent_gold"],
    }
    return colors.get(theme, COLORS["accent_gold"])

def get_theme_title(theme):
    """Возвращает заголовок темы по ID"""
    titles = {
        "primeta": "🌾 НАРОДНАЯ ПРИМЕТА",
        "saint": "⛪ СВЯТОЙ ДНЯ",
        "holiday": "🎉 ПРАЗДНИК ДНЯ",
        "hero": "⭐ ЧТОБЫ ПОМНИЛИ",
        "lunar": "🌙 ЛУННЫЙ КАЛЕНДАРЬ",
        "wisdom": "🗣️ МУДРОСТЬ ДНЯ",
        "history": "📜 ДЕНЬ В ИСТОРИИ",
        "herbal": "🌿 ТРАВНИК ДНЯ",
        "art": "🎨 ИСКУССТВО ДНЯ",
        "food": "🍞 КУХНЯ ПРЕДКОВ",
        "house": "🏡 ДОМ И УКЛАД",
        "craft": "⚒️ РЕМЕСЛО ДНЯ",
        "actor": "🎬 СОВЕТСКИЕ АКТЁРЫ",
        "advice": "🔮 СОВЕТ ДНЯ",
        "prayer": "🕯️ ВЕЧЕРНЯЯ МОЛИТВА",
    }
    return titles.get(theme, "НАРОДНЫЙ КАЛЕНДАРЬ")

def get_current_date_text():
    """Возвращает текущую дату в формате '1 января'"""
    now = datetime.now()
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{now.day} {months[now.month-1]}"

def create_horizontal_card(theme, title_line2=None):
    """Создаёт горизонтальную карточку 1200×630 (упрощённый дизайн)"""
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=COLORS["bg_light"])
    draw = ImageDraw.Draw(img)
    
    # Загружаем шрифты с увеличенным на 10% размером
    try:
        # Было: 68, 52, 38 -> Увеличиваем на 10%: 75, 57, 42
        font_title = ImageFont.truetype("fonts/CormorantGaramond-Bold.ttf", 75)
        font_subtitle = ImageFont.truetype("fonts/CormorantGaramond-SemiBold.ttf", 57)
        font_date = ImageFont.truetype("fonts/PTSerif-Regular.ttf", 42)
    except:
        try:
            font_title = ImageFont.truetype("CormorantGaramond-Bold.ttf", 75)
            font_subtitle = ImageFont.truetype("CormorantGaramond-SemiBold.ttf", 57)
            font_date = ImageFont.truetype("PTSerif-Regular.ttf", 42)
        except:
            # Если шрифты не найдены, используем стандартные
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()
            font_date = ImageFont.load_default()
    
    accent_color = get_color_by_theme(theme)
    
    # ТОЛЬКО вертикальная полоса (упрощаем оформление)
    draw.rectangle([0, 0, 60, CARD_HEIGHT], fill=accent_color)
    
    # Первая строка: тема поста
    theme_title = get_theme_title(theme)
    draw.text((80, 60), theme_title, fill=COLORS["text_dark"], font=font_title)
    
    # Вторая строка (если есть)
    if title_line2:
        max_width = CARD_WIDTH - 150
        if draw.textlength(title_line2, font=font_subtitle) > max_width:
            while draw.textlength(title_line2 + "...", font=font_subtitle) > max_width and len(title_line2) > 10:
                title_line2 = title_line2[:-1]
            title_line2 = title_line2 + "..."
        
        draw.text((80, 145), title_line2, fill=accent_color, font=font_subtitle)
    
    # Дата в правом нижнем углу
    date_text = get_current_date_text()
    date_width = draw.textlength(date_text, font=font_date)
    draw.text((CARD_WIDTH - date_width - 50, CARD_HEIGHT - 60), 
              date_text, fill=COLORS["text_light"], font=font_date)
    
    return img

def generate_long_post_text(theme, day_data):
    """Генерирует текст поста"""
    current_date = get_current_date_text()
    
    templates = {
        "primeta": (
            f"Братья, сегодня {current_date}, и наступило время вспомнить народную примету этого дня.\n\n"
            f"*Примета:*\n{day_data.get('text', 'Природа сегодня особенная.')}\n\n"
            f"*Значение:*\nНаши предки веками наблюдали за природой, отмечая закономерности.\n\n"
        ),
        "saint": (
            f"Друзья, сегодня {current_date} Православная Церковь чтит память {day_data.get('name', 'святого угодника Божия')}.\n\n"
            f"*Житие:*\n{day_data.get('description', 'Этот святой особенно почитаем в народе.')}\n\n"
            f"*Молитва:*\n«{day_data.get('prayer', 'Господи, помилуй нас.')}»\n\n"
        ),
        "holiday": (
            f"Товарищи, сегодня {current_date} — {day_data.get('title', 'особый день в календаре')}.\n\n"
            f"*Значение:*\n{day_data.get('description', 'Этот праздник имеет глубокие исторические корни.')}\n\n"
        ),
        "hero": (
            f"Братья, сегодня {current_date} мы вспоминаем {day_data.get('name', 'героя нашего Отечества')}.\n\n"
            f"*Биография:*\n{day_data.get('bio', 'Пример мужества и служения Родине.')}\n\n"
            f"*Подвиг:*\n{day_data.get('deed', 'Подвиг, который остаётся в памяти поколений.')}\n\n"
        ),
    }
    
    base_text = templates.get(theme, 
        f"Сегодня {current_date}.\n\n"
        f"{day_data.get('text', 'Это время для размышлений о традициях и мудрости предков.')}\n\n"
    )
    
    return base_text

def generate_telegram_post(theme, day_data):
    """Создаёт текст для Telegram поста БЕЗ HTML-тегов"""
    long_text = generate_long_post_text(theme, day_data)
    
    # Хештеги без HTML
    name = day_data.get('name')
    base_tags = {
        "primeta": ["#Примета", "#НароднаяМудрость"],
        "saint": ["#Святой", "#Православие"],
        "holiday": ["#Праздник", "#Традиции"],
        "hero": ["#ЧтобыПомнили", "#Герои"],
        "actor": ["#Актеры", "#Кино"],
    }
    tags = base_tags.get(theme, ["#НародныйКалендарь", "#Традиции"])
    hashtag_text = " ".join(tags[:2])
    
    # Обычные ссылки (не HTML)
    telegram_link = "👉 Подписаться: t.me/narodny_kalendar"
    rutube_link = "📺 Смотреть: rutube.ru/channel/23605491/"
    
    # Формируем полный текст без HTML
    full_text = (
        f"{long_text}\n"
        f"{hashtag_text}\n\n"
        f"{telegram_link}\n"
        f"{rutube_link}"
    )
    
    # Ограничение Telegram
    if len(full_text) > 1024:
        full_text = full_text[:1000] + "...\n\n" + f"{hashtag_text}\n\n{telegram_link}"
    
    return full_text

def create_daily_post(post_type="primeta"):
    """Главная функция: создаёт пост с карточкой и текстом"""
    now = datetime.now()
    current_day = now.day
    current_month = now.month
    
    day_data = load_data_for_day(post_type, current_day, current_month)
    
    title_line2 = None
    if post_type == "saint":
        title_line2 = day_data.get("name", "").upper()
    elif post_type == "hero":
        title_line2 = day_data.get("name", "").upper()
    elif post_type == "actor":
        title_line2 = day_data.get("name", "").upper()
    elif post_type == "holiday":
        title_line2 = day_data.get("title", "").upper()
    
    # Создаём карточку
    card_image = create_horizontal_card(post_type, title_line2)
    
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    image_filename = f"post_{post_type}_{timestamp}.jpg"
    card_image.save(image_filename, quality=95, optimize=True)
    
    # Генерируем текст
    post_text = generate_telegram_post(post_type, day_data)
    
    return image_filename, post_text

def get_post_schedule():
    """Возвращает расписание постов на день"""
    return {
        8: "primeta", 9: "saint", 10: "holiday", 11: "hero", 12: "lunar",
        13: "wisdom", 14: "history", 15: "herbal", 16: "art", 17: "food",
        18: "house", 19: "craft", 20: "actor", 21: "advice", 22: "prayer",
    }

if __name__ == "__main__":
    print("Тестирую генератор постов...")
    try:
        image, text = create_daily_post("primeta")
        print(f"✅ Успешно создан пост!")
        print(f"📁 Файл изображения: {image}")
        print(f"📝 Длина текста: {len(text)} символов")
        print("\nТекст поста:")
        print("-" * 50)
        print(text)
        print("-" * 50)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
