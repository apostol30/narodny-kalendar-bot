from PIL import Image, ImageDraw, ImageFont
import os
import math

# Цвета в пастельной палитре
BG_COLOR = (235, 230, 220)        # бежевый фон
TEXT_COLOR = (40, 35, 30)         # тёмно-коричневый текст
ACCENT_COLOR = (180, 100, 80)     # тёплый акцент (огонь, звезда)
MOON_COLOR = (200, 210, 220)      # мягкий лунный свет
GREEN_ACCENT = (120, 150, 110)    # для природы

def draw_lampada(draw, cx, cy, size=100):
    """Рисует стилизованную лампаду"""
    # Основание
    draw.ellipse((cx - size//2, cy - size//3, cx + size//2, cy + size//3), fill=TEXT_COLOR, outline=None)
    # Пламя
    flame_points = [
        (cx, cy - size//2),
        (cx - size//4, cy - size//4),
        (cx + size//4, cy - size//4)
    ]
    draw.polygon(flame_points, fill=ACCENT_COLOR)

def draw_bread(draw, cx, cy, size=80):
    """Рисует кусочек хлеба"""
    draw.ellipse((cx - size//2, cy - size//3, cx + size//2, cy + size//3), fill=(190, 160, 130))
    # Текстура
    for i in range(-2, 3):
        draw.line([(cx - size//2 + 10, cy + i*5), (cx + size//2 - 10, cy + i*5)], fill=(150, 120, 90), width=1)

def draw_rooster(draw, cx, cy, size=100):
    """Стилизованный петух (упрощённый силуэт)"""
    # Тело
    draw.ellipse((cx - size//2, cy - size//3, cx + size//2, cy + size//3), fill=ACCENT_COLOR)
    # Гребешок
    draw.polygon([(cx - 10, cy - size//2), (cx, cy - size//2 - 20), (cx + 10, cy - size//2)], fill=ACCENT_COLOR)

def draw_moon(draw, cx, cy, size=120):
    """Полная луна"""
    draw.ellipse((cx - size//2, cy - size//2, cx + size//2, cy + size//2), fill=MOON_SIZE_COLOR if 'MOON_SIZE_COLOR' in globals() else MOON_COLOR)
    # Лёгкая текстура
    for _ in range(20):
        x = cx + (os.urandom(1)[0] % size) - size//2
        y = cy + (os.urandom(1)[0] % size) - size//2
        r = 1 + (os.urandom(1)[0] % 2)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(160, 170, 180))

def create_primitive_saint_image(date_text):
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("CormorantGaramond-Bold.ttf", 140)
        font_icon = ImageFont.truetype("CormorantGaramond-Bold.ttf", 60)
    except:
        font_title = ImageFont.load_default()
        font_icon = ImageFont.load_default()

    # Дата
    bbox = draw.textbbox((0, 0), date_text, font=font_title)
    x = (1080 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 400), date_text, fill=TEXT_COLOR, font=font_title)

    # Лампада
    draw_lampada(draw, 540, 850, size=120)

    # Надпись "Святой"
    draw.text((540, 1000), "Святой дня", fill=TEXT_COLOR, font=font_icon, anchor="mm")

    return img

def create_primitive_primeta_image(date_text):
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("CormorantGaramond-Bold.ttf", 140)
    except:
        font_title = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), date_text, font=font_title)
    x = (1080 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 400), date_text, fill=TEXT_COLOR, font=font_title)

    # Петух на крыше (условно — сверху)
    draw_rooster(draw, 540, 800, size=100)
    # Хлеб
    draw_bread(draw, 540, 950, size=90)

    return img

def create_primitive_ussr_image(date_text):
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("CormorantGaramond-Bold.ttf", 140)
        font_label = ImageFont.truetype("PTSerif-Regular.ttf", 50)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), date_text, font=font_title)
    x = (1080 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 400), date_text, fill=TEXT_COLOR, font=font_title)

    # Красная звезда (упрощённо — пятиугольник)
    star_points = []
    cx, cy, r = 540, 850, 60
    for i in range(5):
        angle = math.radians(90 + i * 72)
        star_points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    draw.polygon(star_points, fill=(180, 50, 50))

    draw.text((540, 1000), "Герой СССР", fill=TEXT_COLOR, font=font_label, anchor="mm")
    return img

def create_primitive_lunar_image(date_text):
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("CormorantGaramond-Bold.ttf", 140)
    except:
        font_title = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), date_text, font=font_title)
    x = (1080 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 400), date_text, fill=TEXT_COLOR, font=font_title)

    draw_moon(draw, 540, 850, size=160)
    return img

def create_daily_post(post_type="saint"):
    # === ТЕКСТ В РАЗГОВОРНОМ СТИЛЕ (от лица мужчины) ===
    captions = {
        "saint": (
            "Брат, сегодня — особый день.\n\n"
            "В народе чтят память святого Модеста — заступника скота и хранителя очага.\n\n"
            "Старики говорили: кто в Модестов день не ссорится — тот год в ладу проживёт.\n"
            "А кто оставит на окне кусочек хлеба — к удаче в новом году.\n\n"
            "👉 Подписывайтесь на «Народный календарь» на RuTube —\n"
            "там каждый день: молитвы, приметы, история и советы от предков.\n"
            "🔗 https://rutube.ru/channel/23605491"
        ),
        "primeta": (
            "Слушай, народ!\n\n"
            "Сегодня в канун Нового года смотри на дым из трубы:\n"
            "• Если прямо вверх — к ясному году,\n"
            "• Если стелется — к ненастью весной.\n\n"
            "А кто первым в дом войдёт — таким и год пойдёт.\n"
            "Пусть будет добрый человек — с хлебом и солью!\n\n"
            "👉 «Народный календарь» на RuTube — мудрость предков каждый день.\n"
            "🔗 https://rutube.ru/channel/23605491"
        ),
        "ussr": (
            "Помним. Гордимся.\n\n"
            "Сегодня — день рождения Зои Космодемьянской, первой женщины —\n"
            "Героя Советского Союза в ВОВ.\n\n"
            "Всего 18 лет — а уже в тылу врага. Перед казнью сказала:\n"
            "«Вы повесите меня сейчас, но я не одна. Нас двести миллионов!»\n\n"
            "👉 Подписывайтесь на «Народный календарь» на RuTube.\n"
            "🔗 https://rutube.ru/channel/23605491"
        ),
        "lunar": (
            "Друзья, сегодня — последний день лунного цикла.\n\n"
            "Убывающая Луна. Время отпускать, прощать, завершать.\n"
            "Не начинайте новых дел — лучше убраться в доме и душе.\n\n"
            "А кто верит — читает молитву на ночь:\n"
            "«Господи, благослови исходящий год…»\n\n"
            "👉 «Народный календарь» на RuTube.\n"
            "🔗 https://rutube.ru/channel/23605491"
        )
    }

    # === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ ===
    date_text = "31 декабря"
    if post_type == "saint":
        img = create_primitive_saint_image(date_text)
    elif post_type == "primeta":
        img = create_primitive_primeta_image(date_text)
    elif post_type == "ussr":
        img = create_primitive_ussr_image(date_text)
    elif post_type == "lunar":
        img = create_primitive_lunar_image(date_text)
    else:
        img = create_primitive_saint_image(date_text)

    image_path = "post.jpg"
    img.save(image_path, quality=95)
    return image_path, captions.get(post_type, captions["saint"])
