# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import re

def create_post_image(theme, month, day, output_path="output/post_image.jpg"):
    def remove_emoji(text):
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002500-\U00002BEF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\U0002B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"
            u"\u3030"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)

    try:
        background_path = "assets/fon.jpg"
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"Фоновое изображение не найдено: {background_path}")
        img = Image.open(background_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        
        font_path = "fonts/GOST_A.TTF"
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Шрифт не найден: {font_path}")
        
        # Уменьшаем размеры шрифтов для большей компактности
        font_month = ImageFont.truetype(font_path, 68)   # Было 70
        font_date = ImageFont.truetype(font_path, 150)   # Было 180
        font_theme = ImageFont.truetype(font_path, 70)   # Было 90
        
        img_width, img_height = img.size
        
        # Уменьшаем расстояние между строками
        line_height = 10  # Было 15
        
        # Сдвигаем стартовую позицию ВНИЗ (большее значение = ниже)
        start_y = 550  # Было 500
        
        def get_center_x(text, font):
            text_width = draw.textlength(text, font=font)
            return (img_width - text_width) // 2

        # 1. Месяц
        month_x = get_center_x(month, font_month)
        draw.text((month_x, start_y), month, font=font_month, fill="black")
        current_y = start_y + font_month.size + line_height
        
        # 2. Черта под месяцем
        line_y = current_y
        month_width = draw.textlength(month, font=font_month)
        draw.line([(month_x, line_y), (month_x + month_width, line_y)], fill="black", width=3)
        current_y = line_y + line_height * 2
        
        # 3. Дата
        day_x = get_center_x(day, font_date)
        draw.text((day_x, current_y), day, font=font_date, fill="red")
        current_y = current_y + font_date.size + line_height
        
        # 4. Черта под датой
        line_y = current_y
        day_width = draw.textlength(day, font=font_date)
        draw.line([(day_x, line_y), (day_x + day_width, line_y)], fill="black", width=3)
        current_y = line_y + line_height * 2
        
        # 5. Тема поста (очистка от эмодзи)
        theme = remove_emoji(theme)
        
        # Улучшенный перенос строк: используем ширину изображения вместо фиксированного количества символов
        theme_lines = []
        max_line_width = img_width * 0.8  # Максимальная ширина строки - 80% от ширины изображения
        
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
        
        # Уменьшаем межстрочный интервал для темы
        theme_line_spacing = 8  # Было 10
        
        for theme_line in theme_lines:
            theme_x = get_center_x(theme_line, font_theme)
            draw.text((theme_x, current_y), theme_line, font=font_theme, fill="black")
            current_y += font_theme.size + theme_line_spacing
        
        # Сохранение изображения
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "JPEG", quality=95)
        print(f"✅ Изображение создано: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании изображения: {e}")
        return None
