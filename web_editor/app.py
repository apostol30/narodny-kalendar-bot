"""
Веб-интерфейс для редактирования базы данных Народного календаря
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# Конфигурация
DATA_DIR = "data"
ALLOWED_THEMES = [
    "primety", "saints", "holidays", "heroes", "actors",
    "wisdom", "lunar", "history", "herbal", "art",
    "food", "house", "craft", "advice", "prayers"
]

def load_database(theme):
    """Загружает базу данных по теме"""
    filepath = os.path.join(DATA_DIR, f"{theme}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_database(theme, data):
    """Сохраняет базу данных"""
    filepath = os.path.join(DATA_DIR, f"{theme}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """Главная страница"""
    # Получаем список файлов и статистику
    themes_data = []
    for theme in ALLOWED_THEMES:
        filepath = os.path.join(DATA_DIR, f"{theme}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                themes_data.append({
                    'name': theme,
                    'count': len(data),
                    'last_date': list(data.keys())[-1] if data else 'нет данных'
                })
    
    return render_template('index.html', themes=themes_data)

@app.route('/view/<theme>')
def view_theme(theme):
    """Просмотр базы данных темы"""
    if theme not in ALLOWED_THEMES:
        return redirect(url_for('index'))
    
    data = load_database(theme)
    
    # Преобразуем ключи "день-месяц" в читаемый вид
    items = []
    for key, value in data.items():
        day, month = map(int, key.split('-'))
        items.append({
            'key': key,
            'day': day,
            'month': month,
            'data': value
        })
    
    # Сортируем по дате
    items.sort(key=lambda x: (x['month'], x['day']))
    
    return render_template('view.html', theme=theme, items=items)

@app.route('/edit/<theme>/<key>', methods=['GET', 'POST'])
def edit_item(theme, key):
    """Редактирование записи"""
    if theme not in ALLOWED_THEMES:
        return redirect(url_for('index'))
    
    data = load_database(theme)
    
    if request.method == 'POST':
        # Получаем данные из формы
        form_data = {}
        for field in request.form:
            form_data[field] = request.form[field]
        
        # Сохраняем изменения
        data[key] = form_data
        save_database(theme, data)
        
        return redirect(url_for('view_theme', theme=theme))
    
    # Загружаем данные для редактирования
    item_data = data.get(key, {})
    
    return render_template('edit.html', theme=theme, key=key, data=item_data)

@app.route('/add/<theme>', methods=['GET', 'POST'])
def add_item(theme):
    """Добавление новой записи"""
    if theme not in ALLOWED_THEMES:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        day = request.form.get('day')
        month = request.form.get('month')
        
        if not day or not month:
            return "Ошибка: укажите день и месяц", 400
        
        key = f"{day}-{month}"
        
        data = load_database(theme)
        
        # Собираем данные из формы
        form_data = {}
        for field in request.form:
            if field not in ['day', 'month']:
                form_data[field] = request.form[field]
        
        data[key] = form_data
        save_database(theme, data)
        
        return redirect(url_for('view_theme', theme=theme))
    
    return render_template('add.html', theme=theme)

@app.route('/delete/<theme>/<key>')
def delete_item(theme, key):
    """Удаление записи"""
    if theme not in ALLOWED_THEMES:
        return redirect(url_for('index'))
    
    data = load_database(theme)
    
    if key in data:
        del data[key]
        save_database(theme, data)
    
    return redirect(url_for('view_theme', theme=theme))

@app.route('/api/search/<theme>')
def search(theme):
    """Поиск по базе данных"""
    query = request.args.get('q', '').lower()
    
    if theme not in ALLOWED_THEMES:
        return jsonify({'error': 'Invalid theme'}), 400
    
    data = load_database(theme)
    results = []
    
    for key, value in data.items():
        # Ищем в текстовых полях
        text_to_search = json.dumps(value, ensure_ascii=False).lower()
        if query in text_to_search or query in key:
            results.append({
                'key': key,
                'data': value
            })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
