"""
Клавиатуры для Telegram бота
"""
from telebot import types

# Основное меню направлений
def get_directions_menu():
    """Меню выбора направления"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add(
        types.KeyboardButton('Математические науки'),
        types.KeyboardButton('ИТ'),
        types.KeyboardButton('Инженерные и технические науки'),
        types.KeyboardButton('Языки'),
        types.KeyboardButton('Науки о Земле'),
        types.KeyboardButton('Медицина'),
        types.KeyboardButton('Культура и искусство'),
        types.KeyboardButton('Науки о человеке и обществе'),
        types.KeyboardButton('Медиа'),
        types.KeyboardButton('Экономика и бизнес'),
        types.KeyboardButton('Я не знаю')
    )
    return menu

# Да/Нет меню
def get_yes_no_menu():
    """Меню Да/Нет"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Да'),
        types.KeyboardButton('Нет')
    )
    return menu

# Меню уровня образования
def get_education_level_menu():
    """Меню уровня образования"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Бакалавриат'),
        types.KeyboardButton('Магистратура')
    )
    return menu

# Меню городов
def get_cities_menu():
    """Меню выбора города"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Казань'),
        types.KeyboardButton('Набережные Челны'),
        types.KeyboardButton('Елабуга')
    )
    return menu

# Отделения Елабужского института КФУ (кнопка -> код в JSON)
ELABUGA_DEPARTMENT_TO_CODE = {
    "Математика и естественные науки": "ЕлабИ_ОМЕН",
    "Инженерно-технологическое отделение": "ЕлабИ_ИТО",
    "Экономика и право": "ЕлабИ_ОЭЮН",
    "Психология и педагогика": "ЕлабИ_ОПП",
    "Иностранные языки": "ЕлабИ_ОИЯ",
    "Филология и история": "ЕлабИ_ОФИ",
}

def get_elabuga_departments_menu():
    """Меню выбора отделения Елабужского института КФУ"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for btn_text in ELABUGA_DEPARTMENT_TO_CODE:
        menu.add(types.KeyboardButton(btn_text))
    return menu

# --- Набережные Челны: дерево решений (форма обучения → институт) ---
# 1) Обязательный вопрос: форма обучения в Челнах
CHELNY_FORM_OPTIONS = ("Очная", "Заочная", "Очно-заочная")

def get_chelny_form_menu():
    """Меню выбора формы обучения в Набережных Челнах"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in CHELNY_FORM_OPTIONS:
        menu.add(types.KeyboardButton(opt))
    return menu

# 2) Выбор области → институт(ы) в Челнах
CHELNY_AREA_TO_INSTITUTES = {
    "Техника и технологии": ["ЧелнИ_ВТШ"],
    "Экономика, право и гуманитарные науки": ["ЧелнИ_ВШЭиП"],
    "Пока не определился": ["ЧелнИ_ВТШ", "ЧелнИ_ВШЭиП"],
}

def get_chelny_area_menu():
    """Меню выбора области для института в Набережных Челнах"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for btn_text in CHELNY_AREA_TO_INSTITUTES:
        menu.add(types.KeyboardButton(btn_text))
    return menu

# Меню для ИТ
def get_it_menu():
    """Меню для ИТ направлений"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Высокоуровневая разработка'),
        types.KeyboardButton('ИБ'),
        types.KeyboardButton('ИИ'),
        types.KeyboardButton('Низкоуровневая разработка'),
        types.KeyboardButton('Менеджмент в ИТ')
    )
    return menu

# Меню для ИИ
def get_ai_menu():
    """Меню для ИИ"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Математическая составляющая'),
        types.KeyboardButton('Инжиниринг данных'),
        types.KeyboardButton('Алгоритмы и шаблоны построения ИИ')
    )
    return menu

# Меню для математики
def get_math_menu():
    """Меню для математики"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Прикладные разработки'),
        types.KeyboardButton('Наука и исследования'),
        types.KeyboardButton('Педагогика в математике')
    )
    return menu

# Меню для языков
def get_languages_menu():
    """Меню для языков"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Изучение иностранных языков, как средства коммуникации'),
        types.KeyboardButton('Изучение языков с точки зрения их культуры и филологии')
    )
    return menu

# Меню для наук о Земле
def get_earth_sciences_menu():
    """Меню для наук о Земле"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    menu.add(
        types.KeyboardButton('Физика'),
        types.KeyboardButton('Экология и Биология'),
        types.KeyboardButton('Химия'),
        types.KeyboardButton('География и Геология')
    )
    return menu

# Меню для биологии
def get_biology_menu():
    """Меню для биологии"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Прикладные и междисциплинарные исследования в биологии'),
        types.KeyboardButton('Фундаментальное изучение биологии')
    )
    return menu

# Меню для наук о человеке
def get_human_sciences_menu():
    """Меню для наук о человеке"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Психология'),
        types.KeyboardButton('Юридические науки'),
        types.KeyboardButton('Социология'),
        types.KeyboardButton('Менеджмент'),
        types.KeyboardButton('Философия')
    )
    return menu

# Меню для бизнеса
def get_business_menu():
    """Меню для бизнеса"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Предпринимательство'),
        types.KeyboardButton('Экономика'),
        types.KeyboardButton('Сервис')
    )
    return menu

# Меню для техники
def get_technics_menu():
    """Меню для техники"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('Радиотехника и связь'),
        types.KeyboardButton('Нанотехнологии и материалы'),
        types.KeyboardButton('Электроника и приборостроение'),
        types.KeyboardButton('Робототехника и новые технологии')
    )
    return menu

# Финальное меню
def get_final_menu():
    """Финальное меню после подбора программы"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('✚ Подобрать ещё программы'),
        types.KeyboardButton('🔄 Начать заново')
    )
    return menu

# Меню для статуса ЕГЭ
def get_ege_status_menu():
    """Меню для статуса ЕГЭ"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton('✅ Уже сдал ЕГЭ'),
        types.KeyboardButton('❌ Еще не сдавал ЕГЭ')
    )
    return menu
