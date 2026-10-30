"""
Сервис для генерации персональных вопросов
"""
from services.llm_service import LLMService
from utils.logger import logger

class QuestionGenerator:
    """Класс для генерации вопросов для абитуриентов"""
    
    def __init__(self):
        self.llm = LLMService()
    
    def generate_questions(self, user_data: dict, programs: list) -> list:
        """Генерация 4 вопросов для уточнения программы"""
        try:
            prompt = self._build_prompt(user_data, programs)
            response = self.llm.generate_response(prompt)
            questions = self._parse_questions(response)
            return questions
        except Exception as e:
            logger.error(f"Ошибка генерации вопросов: {e}", exc_info=True)
            return self._get_default_questions()
    
    def generate_questions_for_undecided(self, user_data: dict) -> list:
        """Генерация вопросов для неопределившихся абитуриентов"""
        try:
            prompt = f"""
Сгенерируй 3 вопроса, чтобы определить, какая образовательная программа подойдёт студенту в Казанском Федеральном Университете. 
Проблема в том, что студент не знает, что ему интересно, поэтому на основе информации о нём составь вопросы, 
о том, что может быть интересно студенту, но не спрашивай напрямую.

Информация о студенте:
{self._format_user_data(user_data)}

Вопросы выдать в СТРОГО форматированном виде - разделить все вопросы символом |
"""
            response = self.llm.generate_response(prompt)
            questions = self._parse_questions(response)
            return questions if len(questions) >= 3 else self._get_default_questions()
        except Exception as e:
            logger.error(f"Ошибка генерации вопросов для неопределившихся: {e}", exc_info=True)
            return self._get_default_questions()
    
    def _build_prompt(self, user_data: dict, programs: list) -> str:
        """Построение промпта для генерации вопросов"""
        user_answers = user_data.get('answers', [])
        interest_area = user_data.get('interest_area', '')
        institutes = user_data.get('institutes', [])
        
        prompt = f"""
Ты специалист приёмной комиссии КФУ. Предварительно абитуриент выбрал некоторый спектр образовательных программ, 
составь 4 вопроса, чтобы определить, какая из этих образовательных программ подойдёт студенту по выбранному направлению 
в Казанском Федеральном университете.

Ты получишь на вход информацию о абитуриенте - его ответы на вопросы о личности. Также ты получишь на вход примерный спектр 
образовательных программ, которые могут подойти абитуриенту. Ты должен задать ИМЕННО ТАКИЕ ВОПРОСЫ, чтобы определить какая 
из приведённых программ подойдёт студенту!! Т.е вопросы по содержанию программ. Ты можешь включать в один вопрос сразу несколько, 
если это необходимо.

Вопросы выдать в СТРОГО форматированном виде - разделить все вопросы символом |

Входные данные:
Ответы абитуриента:
{chr(10).join(user_answers)}

Интересное для обучения направление: {interest_area}

Перечень институтов в КФУ, где студент может учиться: {', '.join(institutes)}

Образовательные программы:
{self._format_programs(programs)}
"""
        return prompt
    
    def _format_user_data(self, user_data: dict) -> str:
        """Форматирование данных пользователя"""
        parts = []
        if user_data.get('about'):
            parts.append(f"О себе: {user_data['about']}")
        if user_data.get('profession'):
            parts.append(f"Видение профессии: {user_data['profession']}")
        if user_data.get('subjects'):
            parts.append(f"Успеваемость: {user_data['subjects']}")
        if user_data.get('activities'):
            parts.append(f"Внеучебная деятельность: {user_data['activities']}")
        return "\n".join(parts)
    
    def _format_programs(self, programs: list) -> str:
        """Форматирование списка программ"""
        import json
        return json.dumps(programs, ensure_ascii=False, indent=2)
    
    def _parse_questions(self, response: str) -> list:
        """Парсинг вопросов из ответа LLM"""
        # Разделяем по символу |
        questions = [q.strip() for q in response.split("|") if q.strip()]
        # Очищаем от лишних символов
        questions = [q.replace("*", "").strip() for q in questions]
        return questions[:4]  # Берем максимум 4 вопроса
    
    def _get_default_questions(self) -> list:
        """Получить вопросы по умолчанию"""
        return [
            "Какие аспекты выбранного направления вас больше всего интересуют?",
            "Какой формат работы вы предпочитаете: исследовательский, практический или смешанный?",
            "Планируете ли вы продолжить обучение в магистратуре?",
            "Какие карьерные перспективы для вас наиболее привлекательны?"
        ]
