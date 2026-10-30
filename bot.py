"""
Главный файл Telegram бота для экспертной системы подбора направления в КФУ
Продакшн версия с улучшенной архитектурой и обработкой всех сценариев
"""
import telebot
from telebot import types
import os
import sys
from dotenv import load_dotenv
import time
# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from config import TELEGRAM_BOT_TOKEN
from handlers.user_state import state_manager
from handlers.keyboards import *
from services.question_generator import QuestionGenerator
from services.program_matcher import ProgramMatcher
from utils.ege_helper import EGEChecker
from utils.data_loader import data_loader
from utils.logger import logger

# Проверка токена
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен! Установите переменную окружения или добавьте в config.py")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Инициализация сервисов
question_generator = QuestionGenerator()
program_matcher = ProgramMatcher()

# Маппинг направлений на институты
DIRECTION_TO_INSTITUTES = {
    "ИТ": ["ИВМиИТ", "ИИРСИ", "ИТИС", "ИФ"],
    "Математические науки": ["ИВМиИТ", "ИМиМ"],
    "Медицина": ["ИФМиБ"],
    "Культура и искусство": ["ИДиПИ"],
    "Медиа": ["ИСФНиМК"],
    "Экономика и бизнес": ["ИУЭФ"],
    "Науки о человеке и обществе": {
        "Психология": ["ИПиО"],
        "Юридические науки": ["ЮФ"],
        "Социология": ["ИСФНиМК"],
        "Менеджмент": ["ИУЭФ"],
        "Философия": ["ИСФНиМК"]
    },
    "Науки о Земле": {
        "Физика": ["ИФ"],
        "Химия": ["ХИ"],
        "География и Геология": ["ИГиНГТ"],
        "Экология и Биология": {
            "Биология": ["ИФМиБ", "ИЭБиП"],
            "Экология": ["ИЭБиП"]
        }
    },
    "Инженерные и технические науки": {
        "Робототехника и новые технологии": ["ИИРСИ"],
        "default": ["ИФ"]
    },
    "Языки": {
        "Изучение иностранных языков, как средства коммуникации": ["ИМОИВ"],
        "Изучение языков с точки зрения их культуры и филологии": ["ИФМК"]
    }
}

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    try:
        state = state_manager.get_state(message.chat.id)
        state.clear()
        
        bot.send_message(
            message.chat.id,
            "👋 Добрый день! Это бот экспертной системы, который поможет Вам подобрать подходящую образовательную программу в институтах КФУ!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.send_message(
            message.chat.id,
            "🏙️ Выберите город, в котором Вы хотите учиться",
            reply_markup=get_cities_menu()
        )
        state.step = "city_selection"
        logger.info(f"Пользователь {message.chat.id} начал работу с ботом")
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}", exc_info=True)
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """Главный обработчик сообщений"""
    try:
        state = state_manager.get_state(message.chat.id)
        step = state.step
        
        # Маршрутизация по шагам
        if step == "city_selection":
            handle_city_selection(message, state)
        elif step == "foreign_student":
            handle_foreign_student(message, state)
        elif step == "education_level":
            handle_education_level(message, state)
        elif step == "about_self":
            handle_about_self(message, state)
        elif step == "profession":
            handle_profession(message, state)
        elif step == "subjects":
            handle_subjects(message, state)
        elif step == "activities":
            handle_activities(message, state)
        elif step == "budget_only":
            handle_budget_only(message, state)
        elif step == "ege_status":
            handle_ege_status(message, state)
        elif step == "ege_exams":
            handle_ege_exams(message, state)
        elif step == "ege_score":
            handle_ege_score(message, state)
        elif step == "elabuga_department_selection":
            handle_elabuga_department_selection(message, state)
        elif step == "chelny_form_selection":
            handle_chelny_form_selection(message, state)
        elif step == "chelny_area_selection":
            handle_chelny_area_selection(message, state)
        elif step == "direction_selection":
            handle_direction_selection(message, state)
        elif step.startswith("direction_sub_"):
            handle_direction_sub_selection(message, state)
        elif step == "personal_question":
            handle_personal_question(message, state)
        elif step == "final":
            handle_final(message, state)
        else:
            bot.send_message(message.chat.id, "Начните с команды /start")
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}", exc_info=True)
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте команду /start")

def handle_city_selection(message, state):
    """Обработка выбора города"""
    if message.text not in ["Казань", "Набережные Челны", "Елабуга"]:
        bot.send_message(
            message.chat.id, 
            "❌ Пожалуйста, выберите город из предложенных вариантов.",
            reply_markup=get_cities_menu()
        )
        return
    
    state.update(city=message.text)
    bot.send_message(
        message.chat.id,
        "🌍 Вы иностранный абитуриент?",
        reply_markup=get_yes_no_menu()
    )
    state.step = "foreign_student"

def handle_foreign_student(message, state):
    """Обработка вопроса об иностранном статусе"""
    is_foreign = message.text.lower() == "да"
    state.update(is_foreign=is_foreign)
    
    bot.send_message(
        message.chat.id,
        "📚 Выберите уровень образования",
        reply_markup=get_education_level_menu()
    )
    state.step = "education_level"

def handle_education_level(message, state):
    """Обработка выбора уровня образования"""
    if message.text not in ["Бакалавриат", "Специалитет", "Магистратура"]:
        bot.send_message(
            message.chat.id, 
            "❌ Пожалуйста, выберите уровень из предложенных.",
            reply_markup=get_education_level_menu()
        )
        return
    
    state.update(education_level=message.text)
    
    # Бакалавриат и магистратура используют единый опрос о профиле и интересах
    if message.text in ("Бакалавриат", "Магистратура") or "бакалавр" in message.text.lower():
        bot.send_message(
            message.chat.id,
            "1️⃣ Кратко расскажите о себе. Чем Вы интересуетесь, какие у вас хобби и увлечения?",
            reply_markup=types.ReplyKeyboardRemove()
        )
        state.step = "about_self"
    else:
        bot.send_message(
            message.chat.id,
            "Для выбранного уровня обучения функционал находится в разработке. Пожалуйста, выберите бакалавриат или магистратуру.",
            reply_markup=get_education_level_menu()
        )

def handle_about_self(message, state):
    """Обработка ответа о себе"""
    state.update(about=message.text)
    bot.send_message(
        message.chat.id,
        "2️⃣ Представляете ли кем хотите работать в будущем?"
    )
    state.step = "profession"

def handle_profession(message, state):
    """Обработка ответа о профессии"""
    state.update(profession=message.text)
    bot.send_message(
        message.chat.id,
        "3️⃣ По каким предметам была хорошая успеваемость в школе?"
    )
    state.step = "subjects"

def handle_subjects(message, state):
    """Обработка ответа о предметах"""
    state.update(subjects=message.text)
    bot.send_message(
        message.chat.id,
        "4️⃣ Какой внеучебной деятельностью занимались в школе?"
    )
    state.step = "activities"

def handle_activities(message, state):
    """Обработка ответа о внеучебной деятельности"""
    state.update(activities=message.text)
    bot.send_message(
        message.chat.id,
        "💰 Вы рассматриваете для обучения только бюджет?",
        reply_markup=get_yes_no_menu()
    )
    state.step = "budget_only"

def handle_budget_only(message, state):
    """Обработка вопроса о бюджете"""
    budget_only = message.text.lower() == "да"
    state.update(budget_only=budget_only)
    
    # Для бакалавриата продолжаем ветку с ЕГЭ, для магистратуры сразу переходим к выбору направления
    if state.get("education_level") == "Магистратура":
        bot.send_message(
            message.chat.id,
            "🎯 Какая область магистратуры Вам интересна?",
            reply_markup=get_directions_menu()
        )
        state.step = "direction_selection"
    else:
        bot.send_message(
            message.chat.id,
            "📝 Вы уже сдали ЕГЭ?",
            reply_markup=get_ege_status_menu()
        )
        state.step = "ege_status"

def handle_ege_status(message, state):
    """Обработка статуса ЕГЭ"""
    if "уже сдал" in message.text.lower() or "✅" in message.text:
        bot.send_message(
            message.chat.id,
            "📋 Какие экзамены ЕГЭ вы сдавали? Укажите через запятую (например: русский, математика профиль, информатика)",
            reply_markup=types.ReplyKeyboardRemove()
        )
        state.step = "ege_exams"
    elif "еще не" in message.text.lower() or "❌" in message.text:
        state.update(exams=[], exams_score=None)
        # Переходим к выбору направления или отделения (Елабуга)
        bot.send_message(
            message.chat.id,
            "📚 Хорошо, мы поможем вам определиться с необходимыми ЕГЭ после выбора направления!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        if state.get("city") == "Елабуга":
            bot.send_message(
                message.chat.id,
                "🏛️ Выберите отделение Елабужского института КФУ",
                reply_markup=get_elabuga_departments_menu()
            )
            state.step = "elabuga_department_selection"
        elif state.get("city") == "Набережные Челны":
            bot.send_message(
                message.chat.id,
                "📅 Выберите желаемую форму обучения в Набережных Челнах",
                reply_markup=get_chelny_form_menu()
            )
            state.step = "chelny_form_selection"
        else:
            bot.send_message(
                message.chat.id,
                "🎯 Какая область Вам интересна?",
                reply_markup=get_directions_menu()
            )
            state.step = "direction_selection"

def handle_ege_exams(message, state):
    """Обработка списка ЕГЭ"""
    exams = [exam.strip() for exam in message.text.split(",") if exam.strip()]
    if not exams:
        bot.send_message(message.chat.id, "Пожалуйста, укажите хотя бы один экзамен.")
        return
    
    # Нормализуем названия экзаменов
    normalized_exams = []
    for exam in exams:
        exam_lower = exam.lower()
        # Маппинг различных вариантов названий
        if "математик" in exam_lower and "профил" in exam_lower:
            normalized_exams.append("профиль")
        elif "математик" in exam_lower:
            normalized_exams.append("профиль")  # По умолчанию профиль для технических
        elif "русск" in exam_lower:
            normalized_exams.append("русский")
        elif "информатик" in exam_lower or "информатик" in exam_lower:
            normalized_exams.append("информатика")
        elif "физик" in exam_lower:
            normalized_exams.append("физика")
        elif "хими" in exam_lower:
            normalized_exams.append("химия")
        elif "биолог" in exam_lower:
            normalized_exams.append("биология")
        elif "географи" in exam_lower:
            normalized_exams.append("география")
        elif "литератур" in exam_lower:
            normalized_exams.append("литература")
        elif "истори" in exam_lower:
            normalized_exams.append("история")
        elif "обществ" in exam_lower or "общество" in exam_lower:
            normalized_exams.append("обществознание")
        elif "иностранн" in exam_lower or "английск" in exam_lower or "немецк" in exam_lower or "французск" in exam_lower:
            normalized_exams.append("иностранный")
        else:
            normalized_exams.append(exam_lower)
    
    state.update(exams=normalized_exams, exams_raw=exams)
    
    bot.send_message(
        message.chat.id,
        "📊 Укажите баллы по каждому экзамену через запятую в том же порядке\n"
        "Например: 85, 90, 78\n"
        "Или укажите суммарный балл за все экзамены (число от 0 до 300)"
    )
    state.step = "ege_score"

def handle_ege_score(message, state):
    """Обработка баллов ЕГЭ"""
    try:
        scores_text = message.text.strip()
        exams = state.get("exams", [])
        
        # Пытаемся распарсить как отдельные баллы
        if "," in scores_text:
            scores_list = [int(s.strip()) for s in scores_text.split(",")]
            if len(scores_list) == len(exams):
                # Создаем словарь баллов по предметам
                scores_dict = {exam: score for exam, score in zip(exams, scores_list)}
                state.update(exams_scores_dict=scores_dict, exams_score=sum(scores_list))
            else:
                bot.send_message(
                    message.chat.id,
                    f"Количество баллов ({len(scores_list)}) не совпадает с количеством экзаменов ({len(exams)}).\n"
                    "Попробуйте еще раз или укажите суммарный балл."
                )
                return
        else:
            # Суммарный балл
            total_score = int(scores_text)
            if total_score < 0 or total_score > 300:
                bot.send_message(message.chat.id, "Пожалуйста, введите корректный балл (0-300).")
                return
            state.update(exams_score=total_score)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число или числа через запятую.")
        return
    
    if state.get("city") == "Елабуга":
        bot.send_message(
            message.chat.id,
            "🏛️ Выберите отделение Елабужского института КФУ",
            reply_markup=get_elabuga_departments_menu()
        )
        state.step = "elabuga_department_selection"
    elif state.get("city") == "Набережные Челны":
        bot.send_message(
            message.chat.id,
            "📅 Выберите желаемую форму обучения в Набережных Челнах",
            reply_markup=get_chelny_form_menu()
        )
        state.step = "chelny_form_selection"
    else:
        bot.send_message(
            message.chat.id,
            "🎯 Какая область Вам интересна?",
            reply_markup=get_directions_menu()
        )
        state.step = "direction_selection"

def handle_chelny_form_selection(message, state):
    """Обработка выбора формы обучения в Набережных Челнах"""
    if message.text not in CHELNY_FORM_OPTIONS:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, выберите форму обучения из предложенных вариантов.",
            reply_markup=get_chelny_form_menu()
        )
        return
    state.update(chelny_form=message.text)
    bot.send_message(
        message.chat.id,
        "🏛️ Какое направление Вам ближе? (выберите институт по профилю)",
        reply_markup=get_chelny_area_menu()
    )
    state.step = "chelny_area_selection"

def handle_chelny_area_selection(message, state):
    """Обработка выбора области/института в Набережных Челнах"""
    if message.text not in CHELNY_AREA_TO_INSTITUTES:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, выберите вариант из предложенных.",
            reply_markup=get_chelny_area_menu()
        )
        return
    institutes = CHELNY_AREA_TO_INSTITUTES[message.text]
    state.update(institutes=institutes, interest_area=message.text, preferred_form=state.get("chelny_form"))
    proceed_to_questions(message, state)

def handle_elabuga_department_selection(message, state):
    """Обработка выбора отделения Елабужского института КФУ"""
    department_btn = message.text
    if department_btn not in ELABUGA_DEPARTMENT_TO_CODE:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, выберите отделение из предложенных вариантов.",
            reply_markup=get_elabuga_departments_menu()
        )
        return
    institute_code = ELABUGA_DEPARTMENT_TO_CODE[department_btn]
    state.update(institutes=[institute_code], interest_area=department_btn)
    proceed_to_questions(message, state)

def handle_direction_selection(message, state):
    """Обработка выбора направления"""
    direction = message.text
    
    if direction == "Я не знаю":
        # Генерируем вопросы для неопределившихся
        user_data = {
            "about": state.get("about", ""),
            "profession": state.get("profession", ""),
            "subjects": state.get("subjects", ""),
            "activities": state.get("activities", "")
        }
        questions = question_generator.generate_questions_for_undecided(user_data)
        state.update(questions=questions, question_index=0)
        bot.send_message(message.chat.id, questions[0], reply_markup=types.ReplyKeyboardRemove())
        state.step = "personal_question"
        return
    
    # Определяем институты для направления
    institutes = get_institutes_for_direction(direction, state)
    
    if not institutes:
        bot.send_message(message.chat.id, "Направление не найдено. Выберите из предложенных.")
        return
    
    state.update(direction=direction, institutes=institutes, interest_area=direction)
    
    # Для магистратуры не даём советов по ЕГЭ
    if state.get("education_level") != "Магистратура":
        # Если ЕГЭ не сданы, показываем рекомендации
        if not state.get("exams"):
            advice = EGEChecker.generate_ege_advice(
                institutes, 
                user_exams=None,
                user_scores=None
            )
            bot.send_message(message.chat.id, advice, reply_markup=types.ReplyKeyboardRemove())
        else:
            # Если ЕГЭ сданы, проверяем совместимость и показываем результат
            user_exams = state.get("exams", [])
            user_scores = state.get("exams_scores_dict", {})
            advice = EGEChecker.generate_ege_advice(
                institutes,
                user_exams=user_exams,
                user_scores=user_scores if user_scores else None
            )
            bot.send_message(message.chat.id, advice, reply_markup=types.ReplyKeyboardRemove())
    
    # Проверяем, нужно ли уточнение
    if direction in DIRECTION_TO_INSTITUTES and isinstance(DIRECTION_TO_INSTITUTES[direction], dict):
        # Нужно уточнение
        handle_direction_submenu(message, state, direction)
    else:
        # Переходим к генерации вопросов
        proceed_to_questions(message, state)

def handle_direction_submenu(message, state, direction):
    """Обработка подменю направления"""
    if direction == "ИТ":
        bot.send_message(
            message.chat.id,
            "💻 Что Вам интересно в области ИТ?",
            reply_markup=get_it_menu()
        )
        state.step = "direction_sub_it"
    elif direction == "Математические науки":
        bot.send_message(
            message.chat.id,
            "🔢 Что Вам интереснее в математике?",
            reply_markup=get_math_menu()
        )
        state.step = "direction_sub_math"
    elif direction == "Науки о Земле":
        bot.send_message(
            message.chat.id,
            "🌍 Что вам интереснее в области наук о Земле?",
            reply_markup=get_earth_sciences_menu()
        )
        state.step = "direction_sub_earth"
    elif direction == "Языки":
        bot.send_message(
            message.chat.id,
            "🗣️ Что вам интереснее в изучении языков?",
            reply_markup=get_languages_menu()
        )
        state.step = "direction_sub_lang"
    elif direction == "Науки о человеке и обществе":
        bot.send_message(
            message.chat.id,
            "👥 Что вам интереснее в области наук о человеке и обществе?",
            reply_markup=get_human_sciences_menu()
        )
        state.step = "direction_sub_human"
    elif direction == "Экономика и бизнес":
        bot.send_message(
            message.chat.id,
            "💼 Что для Вас интереснее?",
            reply_markup=get_business_menu()
        )
        state.step = "direction_sub_business"
    elif direction == "Инженерные и технические науки":
        bot.send_message(
            message.chat.id,
            "⚙️ Что Вам интереснее в инженерных и технических науках?",
            reply_markup=get_technics_menu()
        )
        state.step = "direction_sub_tech"

def handle_direction_sub_selection(message, state):
    """Обработка выбора поднаправления"""
    direction = state.get("direction")
    sub_direction = message.text
    
    # Обновляем институты на основе поднаправления
    institutes = get_institutes_for_subdirection(direction, sub_direction, state)
    state.update(institutes=institutes, interest_area=sub_direction)
    
    # Для магистратуры не даём советов по ЕГЭ
    if state.get("education_level") != "Магистратура":
        # Если ЕГЭ не сданы, показываем рекомендации
        if not state.get("exams"):
            advice = EGEChecker.generate_ege_advice(
                institutes,
                user_exams=None,
                user_scores=None
            )
            bot.send_message(message.chat.id, advice, reply_markup=types.ReplyKeyboardRemove())
        else:
            # Если ЕГЭ сданы, проверяем совместимость
            user_exams = state.get("exams", [])
            user_scores = state.get("exams_scores_dict", {})
            advice = EGEChecker.generate_ege_advice(
                institutes,
                user_exams=user_exams,
                user_scores=user_scores if user_scores else None
            )
            bot.send_message(message.chat.id, advice, reply_markup=types.ReplyKeyboardRemove())
    
    proceed_to_questions(message, state)

def proceed_to_questions(message, state):
    """Переход к генерации персональных вопросов"""
    institutes = state.get("institutes", [])
    
    if not institutes:
        bot.send_message(
            message.chat.id,
            "❌ К сожалению, не удалось определить подходящие институты. Попробуйте /start"
        )
        logger.warning(f"Не удалось определить институты для пользователя {message.chat.id}")
        return
    
    # Загружаем программы: для магистратуры используем отдельную базу
    education_level = state.get("education_level")
    from utils.data_loader import data_loader, mag_data_loader
    loader = mag_data_loader if education_level == "Магистратура" else data_loader

    programs = loader.get_programs_by_institutes(institutes)
    
    # Формируем данные для генератора вопросов
    user_data = {
        "answers": [
            state.get("about", ""),
            state.get("profession", ""),
            state.get("subjects", ""),
            state.get("activities", "")
        ],
        "interest_area": state.get("interest_area", ""),
        "institutes": institutes
    }
    
    # Генерируем вопросы
    msg = bot.send_message(message.chat.id, "✨ Генерация персональных вопросов...")
    questions = question_generator.generate_questions(user_data, programs)
    
    bot.delete_message(message.chat.id, msg.message_id)
    
    if not questions or len(questions) < 4:
        questions = question_generator._get_default_questions()
    
    state.update(questions=questions, question_index=0, personal_answers=[])
    bot.send_message(message.chat.id, questions[0], reply_markup=types.ReplyKeyboardRemove())
    state.step = "personal_question"

def handle_personal_question(message, state):
    """Обработка персональных вопросов"""
    questions = state.get("questions", [])
    answers = state.get("personal_answers", [])
    index = state.get("question_index", 0)
    
    answers.append(message.text)
    index += 1
    
    if index < len(questions):
        state.update(question_index=index, personal_answers=answers)
        bot.send_message(message.chat.id, questions[index])
    else:
        # Все вопросы отвечены, переходим к подбору программы
        state.update(personal_answers=answers)
        find_program(message, state)

def find_program(message, state):
    """Подбор программы"""
    msg = bot.send_message(message.chat.id, "✨ Подбор образовательной программы...")
    
    # Формируем данные пользователя
    user_data = {
        "about": state.get("about", ""),
        "profession": state.get("profession", ""),
        "subjects": state.get("subjects", ""),
        "activities": state.get("activities", ""),
        "interest_area": state.get("interest_area", ""),
        "education_level": state.get("education_level"),
        "is_foreign": state.get("is_foreign", False),
        "budget_only": state.get("budget_only", False),
        "exams": state.get("exams", []),
        "exams_score": state.get("exams_score"),
        "personal_questions": list(zip(
            state.get("questions", []),
            state.get("personal_answers", [])
        )),
        "preferred_form": state.get("preferred_form"),  # для Набережных Челнов: Очная/Заочная/Очно-заочная
        "institutes": state.get("institutes", []),
    }
    
    institutes = state.get("institutes", [])
    result = program_matcher.find_best_program(user_data, institutes)
    
    bot.delete_message(message.chat.id, msg.message_id)
    bot.send_message(message.chat.id, result, reply_markup=get_final_menu())
    
    state.update(last_recommendation=result, user_data=user_data)
    state.step = "final"

def handle_final(message, state):
    """Обработка финального меню"""
    if "ещё программы" in message.text.lower() or "✚" in message.text:
        msg = bot.send_message(message.chat.id, "✨ Подбор альтернативных образовательных программ...")
        user_data = state.get("user_data", {})
        previous = state.get("last_recommendation", "")
        result = program_matcher.find_alternative_programs(user_data, previous)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, result, reply_markup=get_final_menu())
    elif "заново" in message.text.lower() or "🔄" in message.text:
        start_command(message)
    else:
        bot.send_message(message.chat.id, "Используйте кнопки меню.")

def get_institutes_for_direction(direction, state):
    """Получить институты для направления"""
    if direction not in DIRECTION_TO_INSTITUTES:
        return []
    
    mapping = DIRECTION_TO_INSTITUTES[direction]
    if isinstance(mapping, list):
        return mapping
    elif isinstance(mapping, dict):
        # Для сложных направлений возвращаем все возможные институты
        institutes = set()
        for value in mapping.values():
            if isinstance(value, list):
                institutes.update(value)
            elif isinstance(value, dict):
                for sub_value in value.values():
                    if isinstance(sub_value, list):
                        institutes.update(sub_value)
        return list(institutes)
    return []

def get_institutes_for_subdirection(direction, sub_direction, state):
    """Получить институты для поднаправления"""
    if direction not in DIRECTION_TO_INSTITUTES:
        return []
    
    mapping = DIRECTION_TO_INSTITUTES[direction]
    
    if isinstance(mapping, dict):
        if sub_direction in mapping:
            result = mapping[sub_direction]
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # Для вложенных структур (например, Экология и Биология)
                institutes = set()
                for value in result.values():
                    if isinstance(value, list):
                        institutes.update(value)
                return list(institutes)
        elif "default" in mapping:
            return mapping["default"]
    
    return []

while True:
    try:
        logger.info("Запуск бота...")
        bot.polling(none_stop=True, timeout=90)
    except Exception as e:
        time.sleep(5)
        continue