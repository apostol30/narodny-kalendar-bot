from PIL import Image, ImageDraw, ImageFont
import os
import math
from datetime import datetime

# Импортируем вечные базы
from data.holidays import ORTHODOX, STATE
from data.saints import SAINTS
from data.heroes import HEROES
from data.quotes_proverbs import MORNING_QUOTES, EVENING_QUOTES, PROVERBS

# === Цвета ===
BG_COLOR = (235, 230, 220)  # нежный бежевый
TEXT_COLOR = (40, 35, 30)   # тёмно-коричневый
ACCENT = (150, 100, 80)     # тёплый акцент

def get_russian_month(m):
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return months[m - 1]

def draw_ornament(draw, theme, width, height):
    """Рисует простой орнамент по углам"""
    size = 50
    if "saint" in theme or theme == "holiday":
        # Крест
        for x, y in [(40, 40), (width - 40, height - 40)]:
            draw.line([(x, y - 20), (x, y + 20)], fill=ACCENT, width=3)
            draw.line([(x - 20, y), (x + 20, y)], fill=ACCENT, width=3)
    elif theme == "ussr":
        # Звезда (упрощённо)
        cx, cy = width - 60, 60
        points = []
        for i in range(5):
            angle = math.radians(90 + i * 72)
            px = cx + size * math.cos(angle)
            py = cy - size * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=ACCENT)
    elif "quote" in theme or theme == "proverb":
        # Перо
        x, y = 60, height - 80
        draw.line([(x, y), (x - 25, y - 50)], fill=ACCENT, width=2)
        draw.ellipse((x - 30, y - 60, x - 20, y - 40), fill=ACCENT)
    else:
        # Завиток
        x, y = width - 80, height - 80
        draw.arc((x, y, x + 60, y + 60), start=0, end=180, fill=ACCENT, width=2)

def create_post_image(theme, subtitle, width=1920, height=1080):
    """Создаёт горизонтальное изображение 1920x1080"""
    img = Image.new('RGB', (width, height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Шрифты
    try:
        font_title = ImageFont.truetype("fonts/CormorantGaramond-Bold.ttf", 110)
        font_subtitle = ImageFont.truetype("fonts/PTSerif-Regular.ttf", 70)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

    # Тема (верх)
    theme_names = {
        "holiday": "ПРАЗДНИК",
        "primeta": "НАРОДНАЯ ПРИМЕТА",
        "saint": "СВЯТОЙ ДНЯ",
        "ussr": "ГЕРОЙ ОТЕЧЕСТВА",
        "quote_morning": "ЦИТАТА ДНЯ",
        "quote_evening": "ВЕЧЕРНЯЯ ЦИТАТА",
        "quiz": "ВИКТОРИНА ДНЯ",
        "evening_prayer": "ВЕЧЕРНЯЯ МОЛИТВА",
        "proverb": "НАРОДНАЯ МУДРОСТЬ",
        "lunar": "ЛУННЫЙ КАЛЕНДАРЬ",
        "saint_tomorrow": "СВЯТОЙ ЗАВТРА"
    }
    title = theme_names.get(theme, "НАРОДНЫЙ КАЛЕНДАРЬ")
    
    bbox = draw.textbbox((0, 0), title, font=font_title)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, 280), title, fill=TEXT_COLOR, font=font_title)

    # Подзаголовок
    if len(subtitle) > 40:
        subtitle = subtitle[:37] + "..."
    bbox2 = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    x2 = (width - (bbox2[2] - bbox2[0])) // 2
    draw.text((x2, 450), subtitle, fill=TEXT_COLOR, font=font_subtitle)

    # Орнамент
    try:
        draw_ornament(draw, theme, width, height)
    except Exception as e:
        pass  # если ошибка — пропустить

    path = "post.jpg"
    img.save(path, quality=95)
    return path

def build_caption(lines, hashtags=""):
    full = "\n".join(lines)
    if len(full) > 4000:
        full = full[:3950] + "…"
    return full + "\n\n👉 Подписывайтесь на «Народный календарь» на RuTube.\n🔗 https://rutube.ru/channel/23605491\n\n" + hashtags

def create_daily_post(post_type="holiday"):
    now = datetime.now()
    day, month = now.day, now.month
    date_str = f"{day} {get_russian_month(month)}"

    # === 8:00 — Праздник ===
    if post_type == "holiday":
        orth_list = ORTHODOX.get((month, day), [])
        state_list = STATE.get((month, day), [])
        all_events = orth_list + state_list
        
        if all_events:
            subtitle = " • ".join(all_events[:2])
            lines = ["Друзья, сегодня — особый день."]
            if orth_list:
                lines.append("\n⛪ В православии сегодня:")
                for o in orth_list:
                    lines.append(f"— {o}")
            if state_list:
                lines.append("\n🗓️ В государственном календаре:")
                for s in state_list:
                    lines.append(f"— {s}")
            lines.append("\nЭти праздники напоминают нам: вера и Отечество — два крыла России.")
        else:
            subtitle = date_str
            lines = [f"Друзья, сегодня в народном календаре — {date_str}."]
            lines.append("\nОсобо важных праздников нет, но деды говорили:")
            lines.append("«Кто в тихий день добро творит — тому весь год везёт».")
        
        image_path = create_post_image("holiday", subtitle)
        return image_path, build_caption(lines, "#сегодняпраздник #народныйкалендарь")

    # === 10:00 / 14:00 / 22:00 — Святой ===
    elif post_type in ["saint", "saint_tomorrow"]:
        saint_name = SAINTS.get((month, day), "Святой дня")
        if post_type == "saint_tomorrow":
            subtitle = f"Завтра: {saint_name}"
            lines = [f"Друзья, завтра Церковь чтит память {saint_name}."]
            lines.append("\nУже сегодня можно помолиться ему —")
            lines.append("чтобы он стал вашим небесным покровителем.")
            lines.append("\nСпокойной ночи. Да хранит вас Господь.")
            hashtags = "#святойдня #спокойнойночи"
        else:
            subtitle = saint_name
            lines = [f"Друзья, сегодня православная Церковь чтит память {saint_name}."]
            lines.append("\nВ народе говорили: кто в этот день помолится —")
            lines.append("тому святой поможет в добрых делах.")
            lines.append("\nПусть его заступничество будет с вами.")
            hashtags = "#святойдня #молитва"
        image_path = create_post_image("saint", subtitle)
        return image_path, build_caption(lines, hashtags)

    # === 11:00 / 15:00 / 19:00 — Герой ===
    elif post_type == "ussr":
        hero_name = HEROES.get((month, day), "Герой Отечества")
        subtitle = hero_name
        lines = [f"Знаете, сегодня — день памяти {hero_name}."]
        lines.append("\nОн отдал жизнь за Родину, но его подвиг живёт в сердцах.")
        lines.append("\nСлава героям — в нашей памяти и чести.")
        image_path = create_post_image("ussr", subtitle)
        return image_path, build_caption(lines, "#геройотечества #слава")

    # === 12:00 — Утренняя цитата ===
    elif post_type == "quote_morning":
        idx = (now.timetuple().tm_yday - 1) % len(MORNING_QUOTES)
        quote, author = MORNING_QUOTES[idx]
        subtitle = author
        lines = ["🗣 Цитата дня", "", f"«{quote}»", f"— {author}"]
        image_path = create_post_image("quote_morning", subtitle)
        return image_path, build_caption(lines, "#цитатадня #мудрость")

    # === 18:00 — Вечерняя цитата ===
    elif post_type == "quote_evening":
        idx = (now.timetuple().tm_yday - 1) % len(EVENING_QUOTES)
        quote, author = EVENING_QUOTES[idx]
        subtitle = author
        lines = ["🌙 Вечерняя цитата", "", f"«{quote}»", f"— {author}"]
        image_path = create_post_image("quote_evening", subtitle)
        return image_path, build_caption(lines, "#цитатадня #вечерняямудрость")

    # === 21:00 — Пословица ===
    elif post_type == "proverb":
        idx = (now.timetuple().tm_yday - 1) % len(PROVERBS)
        prov = PROVERBS[idx]
        subtitle = "Народная мудрость"
        lines = ["Друзья, знаете, в народе говорили:", "", f"«{prov}»", "", "Эта мудрость проверена веками.", "Пусть она ляжет в основу завтрашнего дня."]
        image_path = create_post_image("proverb", subtitle)
        return image_path, build_caption(lines, "#народнаямудрость #пословицадня")

    # === 16:00 — Луна ===
    elif post_type == "lunar":
        subtitle = "Лунный календарь"
        lines = ["Друзья, сегодня Луна в убывающей фазе.", "", "В народе советовали: не начинать новых дел,", "а лучше привести в порядок дом и душу.", "", "Луна — зеркало внутреннего мира."]
        image_path = create_post_image("lunar", subtitle)
        return image_path, build_caption(lines, "#лунныйкалендарь #луна")

    # === 20:00 — Молитва ===
    elif post_type == "evening_prayer":
        subtitle = "Вечерняя молитва"
        lines = [
            "Друзья, настало время тишины.",
            "",
            "Вечером наши деды читали:",
            "«Господи, благослови исходящий день,",
            "сохрани дом от беды, семью — от тревоги,",
            "дай покой душе и крепкий сон. Аминь.»",
            "",
            "Пусть эта молитва согреет ваш дом."
        ]
        image_path = create_post_image("evening_prayer", subtitle)
        return image_path, build_caption(lines, "#вечерняямолитва #спокойнойночи")

    # === 19:00 — Викторина (упрощённо) ===
    elif post_type == "quiz":
        questions = [
            "Кто крестил Русь? А) Владимир • Б) Ольга • В) Ярослав",
            "Кто первый полетел в космос? А) Титов • Б) Гагарин • В) Леонов"
        ]
        idx = (now.timetuple().tm_yday - 1) % len(questions)
        question = questions[idx]
        subtitle = "Проверь свои знания!"
        lines = ["🧠 Викторина дня", "", f"Друзья, отгадайте:", "", question, "", "Пишите ответ в комментарии!", "Завтра — правильный ответ."]
        image_path = create_post_image("quiz", subtitle)
        return image_path, build_caption(lines, "#викторинадня #знаниероссии")

    # === Примета (9:00, 13:00, 17:00) ===
    else:  # primeta
        subtitle = "Народная примета"
        lines = [
            "Друзья, знаете, в народе на этот день есть примета:",
            "",
            "Если утро ясное — к доброму урожаю,",
            "если ветер с востока — к морозу.",
            "",
            "Смотрите на природу — она говорит с нами."
        ]
        image_path = create_post_image("primeta", subtitle)
        return image_path, build_caption(lines, "#народнаяпримета #природа")
