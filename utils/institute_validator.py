"""
Модуль для валидации названий институтов в ответах LLM
Исключает галлюцинации и заменяет на реальные названия из базы данных
"""
import re
from typing import List, Dict, Tuple, Optional
from utils.data_loader import data_loader
from utils.logger import logger

class InstituteValidator:
    """Класс для валидации и исправления названий институтов"""
    
    def __init__(self):
        # Кэш названий институтов будет загружен при первом использовании
        self._institute_names_cache = {}
    
    def _ensure_cache_loaded(self):
        """Убедиться, что кэш загружен"""
        if not self._institute_names_cache:
            self._load_institute_names()
    
    def _load_institute_names(self):
        """Загрузить все названия институтов из базы данных"""
        try:
            # Получаем все институты из базы через data_loader
            institutes_data = data_loader._data.get("institutes", {})
            for code, info in institutes_data.items():
                name = info.get("name", "")
                if name:
                    self._institute_names_cache[code] = name
                    # Также сохраняем варианты названий
                    self._institute_names_cache[name.lower()] = code
                    # Сохраняем короткие коды
                    self._institute_names_cache[code.lower()] = code
        except Exception as e:
            logger.error(f"Ошибка загрузки названий институтов: {e}")
    
    def get_all_institute_codes(self) -> List[str]:
        """Получить все коды институтов"""
        return list(data_loader._data.get("institutes", {}).keys())
    
    def get_institute_name(self, code: str) -> str:
        """Получить полное название института по коду"""
        return data_loader.get_institute_name(code)
    
    def find_institute_in_text(self, text: str, allowed_codes: List[str] = None) -> Optional[Tuple[str, str]]:
        """
        Найти название института в тексте
        Возвращает: (код_института, найденное_название) или None
        """
        self._ensure_cache_loaded()
        
        if allowed_codes is None:
            allowed_codes = self.get_all_institute_codes()
        
        # Получаем названия разрешенных институтов
        allowed_names = {}
        for code in allowed_codes:
            name = self.get_institute_name(code)
            if name:
                allowed_names[code] = name
                # Также добавляем варианты
                allowed_names[name.lower()] = code
                allowed_names[code.lower()] = code
        
        # Ищем в тексте
        text_lower = text.lower()
        
        # Сначала ищем по полным названиям (более точное совпадение)
        for code, name in allowed_names.items():
            if isinstance(name, str) and len(name) > 5:  # Только полные названия
                name_lower = name.lower()
                # Ищем точное вхождение или начало строки
                if name_lower in text_lower:
                    # Проверяем, что это не часть другого слова
                    pattern = r'\b' + re.escape(name_lower) + r'\b'
                    if re.search(pattern, text_lower):
                        return (code, name)
        
        # Затем ищем по кодам (ИВМиИТ, ИТИС и т.д.)
        for code in allowed_codes:
            code_lower = code.lower()
            if code_lower in text_lower:
                # Проверяем, что это отдельное слово или аббревиатура
                pattern = r'\b' + re.escape(code_lower) + r'\b'
                if re.search(pattern, text_lower):
                    return (code, self.get_institute_name(code))
        
        return None
    
    def validate_and_fix_response(self, llm_response: str, allowed_institute_codes: List[str]) -> str:
        """
        Валидировать ответ LLM и исправить названия институтов
        """
        if not llm_response or not allowed_institute_codes:
            return llm_response
        
        # Получаем правильные названия для разрешенных институтов
        correct_names = {}
        for code in allowed_institute_codes:
            name = self.get_institute_name(code)
            correct_names[code] = name
            correct_names[name.lower()] = code
        
        # Ищем название института в ответе
        found_institute = self.find_institute_in_text(llm_response, allowed_institute_codes)
        
        lines = llm_response.split('\n')
        fixed_lines = []
        institute_found = False
        
        for i, line in enumerate(lines):
            line_original = line
            line_lower = line.lower()
            
            # Проверяем, есть ли в строке название института
            # Ищем в первых 3 строках (обычно название института в начале)
            if i < 3:
                # Проверяем, есть ли правильное название
                has_correct = False
                for code, name in correct_names.items():
                    if isinstance(name, str) and len(name) > 5:
                        if name.lower() in line_lower or code.lower() in line_lower:
                            has_correct = True
                            institute_found = True
                            break
                
                # Если правильного названия нет, но строка похожа на название института
                if not has_correct and any(keyword in line_lower for keyword in ['институт', 'факультет', 'школа']):
                    # Заменяем на первое разрешенное название
                    if allowed_institute_codes:
                        default_code = allowed_institute_codes[0]
                        default_name = correct_names[default_code]
                        # Заменяем всю строку или начало строки
                        if re.match(r'^[А-Яа-я\s]+(?:институт|факультет|школа)', line, re.IGNORECASE):
                            fixed_lines.append(default_name)
                            institute_found = True
                            logger.warning(f"Заменено название института в строке '{line}' на '{default_name}'")
                            continue
            
            fixed_lines.append(line)
        
        # Если институт не найден вообще, добавляем правильное название в начало
        if not institute_found and allowed_institute_codes:
            default_code = allowed_institute_codes[0]
            default_name = correct_names[default_code]
            logger.warning(f"Институт не найден в ответе LLM. Добавлено: {default_name}")
            fixed_response = f"{default_name}\n\n" + '\n'.join(fixed_lines)
            return fixed_response
        
        fixed_response = '\n'.join(fixed_lines)
        return fixed_response
    
    def extract_institute_from_response(self, response: str, allowed_codes: List[str]) -> Optional[str]:
        """
        Извлечь код института из ответа LLM
        """
        found = self.find_institute_in_text(response, allowed_codes)
        if found:
            return found[0]  # Возвращаем код
        return None
    
    def validate_program_in_institute(self, program_name: str, institute_code: str) -> bool:
        """
        Проверить, существует ли программа в указанном институте
        """
        try:
            programs = data_loader.get_programs_by_institutes([institute_code])
            program_name_lower = program_name.lower()
            
            for program in programs:
                # Проверяем название программы
                if program_name_lower in program.get("name", "").lower():
                    return True
                if program_name_lower in program.get("profile", "").lower():
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки программы: {e}")
            return False

# Глобальный экземпляр валидатора
institute_validator = InstituteValidator()
