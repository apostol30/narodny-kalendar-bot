from PIL import Image, ImageDraw, ImageFont
import os

def create_daily_post():
    date_str = "31 декабря"
    caption = (
        "🕯️ Сегодня — 31 декабря. Модестов день\n\n"
        "В народе этот вечер называли «порогом года».\n"
        "Говорили: «Как Модестов вечер пройдёт — так и весь год пойдёт».\n\n"
        "👉 Подписывайтесь на «Народный календарь» на RuTube:\n"
        "https://rutube.ru/channel/23605491"
    )
    img = Image.new('RGB', (1080, 1350), color=(235, 230, 220))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("CormorantGaramond-Bold.ttf", 80)
    except:
        from PIL import ImageFont
        font = ImageFont.load_default()
    draw.text((540, 600), date_str, fill=(50, 40, 30), font=font, anchor="mm")
    image_path = "post.jpg"
    img.save(image_path)
    return image_path, caption
