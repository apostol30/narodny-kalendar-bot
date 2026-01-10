# image_generator.py
from PIL import Image, ImageDraw, ImageFont  # Библиотека Pillow для работы с изображениями
import os
import re  # Импорт модуля для работы с регулярными выражениями


def create_post_image(theme, month, day, output_path="output/post_image.jpg"):
    """
    Создает изображение для поста по заданному шаблону.

    Args:
        theme (str): Тема поста (например, "ДЕНЬ В ИСТОРИИ: Луи Дагер")
        month (str): Название месяца (например, "ЯНВАРЬ")
        day (str): Число дня (например, "07")
        output_path (str): Путь для сохранения готового изображения.
    """

    def remove_emoji(text):
        """
        Удаляет эмодзи и другие специальные символы из строки.
        """
        # Шаблон для поиска emoji и других нестандартных символов
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # различные символы
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
            u"\ufe0f"  # вариационный селектор-16 (часть составных эмодзи)
            u"\u3030"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)

    try:
        # 1. Открываем фон
        background_path = "assets/fon.jpg"
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"Фоновое изображение не найдено: {background_path}")
        img = Image.open(background_path)

        # Конвертируем в RGB, если нужно (например, если фон был в формате RGBA)
        if img.mode != "RGB":
            img = img.convert("RGB")

        draw = ImageDraw.Draw(img)

        # 2. Загружаем шрифты
        # Убедитесь, что файл шрифта GOST_A.TTF лежит в папке проекта или в указанном пути.
        font_path_bold = "fonts/GOST_A.TTF"  # Основной шрифт для месяца и темы
        font_path_regular = "fonts/GOST_A.TTF"  # Можно использовать тот же или другой
        font_path_date = "fonts/GOST_A.TTF"  # Шрифт для даты

        # Проверка наличия шрифта
        if not os.path.exists(font_path_bold):
            raise FileNotFoundError(
                f"Шрифт не найден: {font_path_bold}. Убедитесь, что файл лежит в указанной папке."
            )

        # Размеры шрифтов подбираются опытным путем под ваш размер фона 1600x1124
        font_month = ImageFont.truetype(font_path_bold, 90)  # Крупный для месяца
        font_date = ImageFont.truetype(font_path_date, 180)  # Очень крупный, красный для даты
        font_theme = ImageFont.truetype(font_path_regular, 90)  # Как у месяца, для темы

        # 3. Рассчитываем координаты для центрирования текста
        img_width, img_height = img.size
        line_height = 15  # Расстояние между строками

        # Координата Y для первой строки (месяц) - отступ от верха
        start_y = 500

        # Функция для расчета координаты X, чтобы текст был по центру
        def get_center_x(text, font):
            text_width = draw.textlength(text, font=font)  # Новый метод в Pillow 9.2+
            # Для совместимости со старыми версиями можно использовать:
            # bbox = draw.textbbox((0, 0), text, font=font)
            # text_width = bbox[2] - bbox[0]
            return (img_width - text_width) // 2

        # 4. Рисуем месяц (черный)
        month_x = get_center_x(month, font_month)
        draw.text((month_x, start_y), month, font=font_month, fill="black")
        current_y = start_y + font_month.size + line_height

        # 5. Рисуем черту под месяцем
        line_y = current_y
        draw.line(
            [(month_x, line_y), (month_x + draw.textlength(month, font=font_month), line_y)],
            fill="black",
            width=3,
        )
        current_y = line_y + line_height * 2

        # 6. Рисуем дату (красная, крупно)
        day_x = get_center_x(day, font_date)
        draw.text((day_x, current_y), day, font=font_date, fill="red")
        current_y = current_y + font_date.size + line_height

        # 7. Рисуем черту под датой
        line_y = current_y
        draw.line(
            [(day_x, line_y), (day_x + draw.textlength(day, font=font_date), line_y)],
            fill="black",
            width=3,
        )
        current_y = line_y + line_height * 2

        # 8. Очищаем тему поста от эмодзи перед отрисовкой
        theme = remove_emoji(theme)

        # Рисуем тему поста (черный, размер как у месяца)
        # Если тема длинная, можно разбить на две строки.
        theme_lines = []
        if len(theme) > 20:  # Условное значение, подберите под ваш дизайн
            # Простой перенос по словам
            words = theme.split()
            current_line = words[0]
            for word in words[1:]:
                if len(current_line) + len(word) + 1 <= 20:
                    current_line += " " + word
                else:
                    theme_lines.append(current_line)
                    current_line = word
            theme_lines.append(current_line)
        else:
            theme_lines = [theme]

        for theme_line in theme_lines:
            theme_x = get_center_x(theme_line, font_theme)
            draw.text((theme_x, current_y), theme_line, font=font_theme, fill="black")
            current_y += font_theme.size + 10  # Межстрочный интервал для темы

        # 9. Создаем папку для результата, если её нет
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 10. Сохраняем изображение
        img.save(output_path, "JPEG", quality=95)
        print(f"✅ Изображение создано: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Ошибка при создании изображения: {e}")
        return None
