# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import re

def create_post_image(theme, month, day, output_path="output/post_image.jpg"):
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
        # Этот шаг гарантированно убирает "квадратики"
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
        # 1. Открываем фон
        background_path = "assets/fon.jpg"
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"Фоновое изображение не найдено: {background_path}")
        img = Image.open(background_path)

        if img.mode != "RGB":
            img = img.convert("RGB")

        draw = ImageDraw.Draw(img)
        
        # 2. Загружаем шрифты
        font_path = "fonts/GOST_A.TTF"
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Шрифт не найден: {font_path}")

        # Размеры шрифтов (уже оптимизированные для компактности)
        font_month = ImageFont.truetype(font_path, 68)
        font_date = ImageFont.truetype(font_path, 150)
        font_theme = ImageFont.truetype(font_path, 70)
        
        img_width, img_height = img.size
        line_height = 10
        start_y = 550  # Стартовая позиция (уже сдвинута вниз)

        def get_center_x(text, font):
            text_width = draw.textlength(text, font=font)
            return (img_width - text_width) // 2

        # ========== ВАЖНО: ОЧИСТКА ТЕМЫ ПЕРЕД ИСПОЛЬЗОВАНИЕМ ==========
        # Логируем исходную тему для отладки
        print(f"[DEBUG] Тема ДО очистки: {repr(theme)}")
        
        # Очищаем тему от эмодзи и специальных символов
        theme_cleaned = remove_emoji_and_special(theme)
        
        # Логируем результат очистки
        print(f"[DEBUG] Тема ПОСЛЕ очистки: {repr(theme_cleaned)}")
        
        # Выводим коды Unicode каждого символа для точной диагностики
        print("[DEBUG] Символы в очищенной теме:")
        for i, char in enumerate(theme_cleaned):
            print(f"  Символ {i}: U+{ord(char):04X} - {repr(char)}")
        
        # Используем очищенную тему для дальнейшей обработки
        theme = theme_cleaned
        # =============================================================

        # 3. Рисуем месяц (черный)
        month_x = get_center_x(month, font_month)
        draw.text((month_x, start_y), month, font=font_month, fill="black")
        current_y = start_y + font_month.size + line_height

        # 4. Черта под месяцем
        line_y = current_y
        month_width = draw.textlength(month, font=font_month)
        draw.line([(month_x, line_y), (month_x + month_width, line_y)], fill="black", width=3)
        current_y = line_y + line_height * 2

        # 5. Дата
        day_x = get_center_x(day, font_date)
        draw.text((day_x, current_y), day, font=font_date, fill="red")
        current_y = current_y + font_date.size + line_height

        # 6. Черта под датой
        line_y = current_y
        day_width = draw.textlength(day, font=font_date)
        draw.line([(day_x, line_y), (day_x + day_width, line_y)], fill="black", width=3)
        current_y = line_y + line_height * 2

        # 7. Тема поста (теперь гарантированно без эмодзи)
        # Улучшенный перенос строк с учетом ширины
        theme_lines = []
        max_line_width = img_width * 0.8
        
        words = theme.split()
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
        
        # Если после очистки тема стала пустой, используем заглушку
        if not theme_lines or all(not line.strip() for line in theme_lines):
            theme_lines = ["Народный календарь"]
            print("[DEBUG] Тема оказалась пустой после очистки, использована заглушка")
        
        theme_line_spacing = 8
        
        for theme_line in theme_lines:
            theme_x = get_center_x(theme_line, font_theme)
            draw.text((theme_x, current_y), theme_line, font=font_theme, fill="black")
            current_y += font_theme.size + theme_line_spacing

        # 8. Сохраняем изображение
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "JPEG", quality=95)
        print(f"✅ Изображение создано: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании изображения: {e}")
        import traceback
        traceback.print_exc()
        return None
