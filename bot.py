def escape_markdown_v2(text: str) -> str:
    """
    Правильно экранирует спецсимволы для Telegram MarkdownV2.
    Сохраняет *жирный*, _курсив_, __подчеркнутый__, `код`, ```блок кода``` и [ссылки](url).
    """
    if not text:
        return ""
    
    # Список символов, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Шаг 1: Временные метки для защищенных блоков
    markers = {}
    marker_counter = 0
    
    # Защищаем блоки кода (```код```)
    def protect_code_blocks(match):
        nonlocal marker_counter
        marker = f"__CODE_BLOCK_{marker_counter}__"
        markers[marker] = match.group(0)  # Сохраняем оригинал
        marker_counter += 1
        return marker
    
    # Защищаем inline-код (`код`)
    def protect_inline_code(match):
        nonlocal marker_counter
        marker = f"__INLINE_CODE_{marker_counter}__"
        markers[marker] = match.group(0)
        marker_counter += 1
        return marker
    
    # Защищаем ссылки [текст](url)
    def protect_links(match):
        nonlocal marker_counter
        marker = f"__LINK_{marker_counter}__"
        markers[marker] = match.group(0)
        marker_counter += 1
        return marker
    
    # Защищаем жирный текст **текст**
    def protect_bold(match):
        nonlocal marker_counter
        marker = f"__BOLD_{marker_counter}__"
        markers[marker] = match.group(0)
        marker_counter += 1
        return marker
    
    # Защищаем курсив *текст* или _текст_
    def protect_italic(match):
        nonlocal marker_counter
        marker = f"__ITALIC_{marker_counter}__"
        markers[marker] = match.group(0)
        marker_counter += 1
        return marker
    
    # Защищаем подчеркивание __текст__
    def protect_underline(match):
        nonlocal marker_counter
        marker = f"__UNDERLINE_{marker_counter}__"
        markers[marker] = match.group(0)
        marker_counter += 1
        return marker
    
    # Шаг 2: Последовательно защищаем все элементы форматирования
    # Важно делать это в порядке от сложных к простым конструкциям
    text = re.sub(r'```.*?```', protect_code_blocks, text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', protect_inline_code, text)
    text = re.sub(r'\[.*?\]\(.*?\)', protect_links, text)
    text = re.sub(r'\*\*[^*]+\*\*', protect_bold, text)
    text = re.sub(r'__[^_]+__', protect_underline, text)
    text = re.sub(r'_[^_]+_', protect_italic, text)
    text = re.sub(r'\*[^*]+\*', protect_italic, text)
    
    # Шаг 3: Экранируем все опасные символы
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    # Шаг 4: Восстанавливаем защищенные блоки
    for marker, original in markers.items():
        text = text.replace(marker, original)
    
    return text
