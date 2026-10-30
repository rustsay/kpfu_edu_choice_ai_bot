"""
Сервис для подбора образовательных программ
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from services.llm_service import LLMService
from utils.data_loader import data_loader, mag_data_loader
from utils.institute_validator import institute_validator
from utils.logger import logger

class ProgramMatcher:
    """Класс для подбора образовательных программ"""
    
    def __init__(self):
        self.llm = LLMService()
        self._current_programs: List[Dict] = []
    
    def find_best_program(self, user_data: dict, institute_codes: List[str]) -> str:
        """Найти наиболее подходящую программу"""
        try:
            education_level = user_data.get("education_level")
            loader = mag_data_loader if education_level == "Магистратура" else data_loader

            programs = loader.get_programs_by_institutes(institute_codes)
            
            if user_data.get('budget_only'):
                programs = loader.filter_programs_by_budget(programs, budget_only=True)
            
            is_foreign = user_data.get('is_foreign', False)
            programs = loader.filter_programs_by_foreign(programs, is_foreign=is_foreign)
            
            # Для Набережных Челнов: фильтр по выбранной форме обучения
            preferred_form = user_data.get('preferred_form')
            if preferred_form:
                programs = [p for p in programs if (p.get('form') or '').strip() == preferred_form]
            
            if not programs:
                return "К сожалению, не найдено подходящих программ по вашим критериям."
            
            self._current_programs = programs
            
            prompt = self._build_matching_prompt(user_data, programs, institute_codes)
            
            result = self.llm.generate_response(prompt)
            
            program_number, justification = self._parse_llm_response(result)
            
            if program_number is None or program_number < 1 or program_number > len(programs):
                logger.warning(f"Не удалось определить номер программы. LLM ответ: {result}")
                return "Не удалось точно определить подходящую программу. Попробуйте уточнить ваши предпочтения."
            
            selected_program = programs[program_number - 1]
            
            result = self._format_result(selected_program, institute_codes, justification)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка при подборе программы: {e}", exc_info=True)
            return "Извините, произошла ошибка при подборе программы. Попробуйте позже."
    
    def _parse_llm_response(self, response: str) -> Tuple[Optional[int], str]:
        """Извлечь номер программы и обоснование из ответа LLM"""
        lines = response.strip().split('\n')
        
        program_number = None
        justification_lines = []
        justification_started = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if not justification_started:
                match = re.search(r'^\[?(\d+)\]?(?:\.|\)|:|-)', line)
                if match:
                    program_number = int(match.group(1))
                    justification_started = True
                    remainder = line[match.end():].strip()
                    if remainder:
                        justification_lines.append(remainder)
                    continue
                
                match = re.search(r'номер\s*[:\-]?\s*(\d+)', line, re.IGNORECASE)
                if match:
                    program_number = int(match.group(1))
                    justification_started = True
                    continue
            else:
                justification_lines.append(line)
        
        justification = ' '.join(justification_lines).strip()
        
        if not justification and program_number is not None:
            justification = "Программа выбрана на основе анализа ваших интересов и данных."
        
        return program_number, justification
    
    def _format_result(self, program: Dict, institute_codes: List[str], justification: str) -> str:
        """Форматировать результат с данными из JSON и обоснованием от LLM"""
        institute_code = program.get("institute", "")
        institute_name = data_loader.get_institute_name(institute_code)
        
        budget = program.get("budget_places", 0)
        contract = program.get("contract_places", 0)
        
        places_info = f"Бюджетных мест: {budget}, контрактных мест: {contract}"
        
        result = f"""{institute_name}

Образовательная программа:
- Название: {program.get('name', '')}
- Профиль: {program.get('profile', '')}
- Код: {program.get('code', '')}
- Уровень: {program.get('level', '')}
- Срок обучения: {program.get('duration', '')}
- Форма обучения: {program.get('form', '')}
- {places_info}
- Описание: {program.get('specifics', '')}

Обоснование выбора: {justification}"""
        
        return result
    
    def find_alternative_programs(self, user_data: dict, previous_recommendation: str) -> str:
        """Найти альтернативные программы"""
        try:
            institute_codes = user_data.get('institutes', [])
            education_level = user_data.get("education_level")
            loader = mag_data_loader if education_level == "Магистратура" else data_loader

            all_programs = loader.get_all_programs()
            # Для Набережных Челнов ограничиваем альтернативы выбранными институтами
            if user_data.get('preferred_form') and institute_codes:
                all_programs = [p for p in all_programs if p.get('institute') in institute_codes]
            if user_data.get('budget_only'):
                all_programs = loader.filter_programs_by_budget(all_programs, budget_only=True)
            
            is_foreign = user_data.get('is_foreign', False)
            all_programs = loader.filter_programs_by_foreign(all_programs, is_foreign=is_foreign)
            
            preferred_form = user_data.get('preferred_form')
            if preferred_form:
                all_programs = [p for p in all_programs if (p.get('form') or '').strip() == preferred_form]
            
            if len(all_programs) < 3:
                return "Недостаточно программ для поиска альтернатив."
            
            programs_text = self._format_programs_with_numbers(all_programs)
            
            prompt = f"""
Ты консультант приёмной комиссии Казанского Федерального Университета. Абитуриент предварительно определился с итоговой программой для обучения в КФУ, 
тебе нужно подобрать ещё 2 альтернативные программы обучения в КФУ, которые также могут подойти этому абитуриенту.

Подбери ещё 2 образовательные программы из списка ниже, которые также могут подойти этому абитуриенту на основе его ответов на вопросы и интересов.
ВЫБЕРИ ИМЕННО ТЕ ПРОГРАММЫ, КОТОРЫЕ ЕСТЬ В СПИСКЕ НИЖЕ!

Входные данные:
Резюме абитуриента:
{self._format_user_resume(user_data)}

Выбранная ранее программа:
{previous_recommendation}

КРИТИЧЕСКИ ВАЖНО! ВЫБОР ПРОГРАММ:
1. Проанализируй ВСЕ пронумерованные программы ниже
2. Выбери 2 НАИБОЛЕЕ ПОДХОДЯЩИЕ программы (отличные от выбранной ранее)
3. В ответе укажи 2 номера программ и обоснование для каждой
4. НЕ описывай программы полностью - данные о программах будут добавлены автоматически из базы данных

Формат ответа (СТРОГО соблюдай):
[НОМЕР ПРОГРАММЫ 1]: [Обоснование почему эта программа подойдёт]

[НОМЕР ПРОГРАММЫ 2]: [Обоснование почему эта программа подойдёт]

Пример ответа:
5: Эта программа подходит абитуриенту, так как она ориентирована на практическое применение математики в экономике.
12: Данная программа позволит студенту развить навыки программирования и работы с данными.

Все доступные программы (пронумерованный список):
{programs_text}
"""
            result = self.llm.generate_response(prompt)
            
            program_numbers = self._parse_multiple_programs(result)
            
            if not program_numbers or len(program_numbers) < 2:
                logger.warning(f"Не удалось определить номера альтернативных программ. LLM ответ: {result}")
                return "Не удалось подобрать альтернативные программы. Попробуйте позже."
            
            alt_programs = []
            for num in program_numbers[:2]:
                if 1 <= num <= len(all_programs):
                    alt_programs.append(all_programs[num - 1])
            
            response_parts = []
            for i, prog in enumerate(alt_programs):
                institute_code = prog.get("institute", "")
                institute_name = loader.get_institute_name(institute_code)
                budget = prog.get("budget_places", 0)
                contract = prog.get("contract_places", 0)
                
                justification = ""
                if i < len(program_numbers) - 1:
                    lines = result.split('\n')
                    for line in lines:
                        if f"{program_numbers[i]}" in line:
                            justification = line.split(':', 1)[1].strip() if ':' in line else ""
                            break
                
                response_parts.append(f"""Институт: {institute_name}
Образовательная программа:
- Название: {prog.get('name', '')}
- Профиль: {prog.get('profile', '')}
- Код: {prog.get('code', '')}
- Уровень: {prog.get('level', '')}
- Срок обучения: {prog.get('duration', '')}
- Форма обучения: {prog.get('form', '')}
- Бюджетных мест: {budget}, контрактных мест: {contract}
- Описание: {prog.get('specifics', '')}

Обоснование выбора: {justification if justification else 'Программа выбрана как альтернативная.'}""")
            
            return "\n\n---\n\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Ошибка при подборе альтернативных программ: {e}", exc_info=True)
            return "Извините, произошла ошибка. Попробуйте позже."
    
    def _parse_multiple_programs(self, response: str) -> List[int]:
        """Извлечь несколько номеров программ из ответа LLM"""
        program_numbers = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.search(r'^\[?(\d+)\]?(?:\.|\)|:|-)', line)
            if match:
                program_numbers.append(int(match.group(1)))
                continue
            
            match = re.search(r'номер\s*[:\-]?\s*(\d+)', line, re.IGNORECASE)
            if match:
                program_numbers.append(int(match.group(1)))
        
        return program_numbers
    
    def _build_matching_prompt(self, user_data: dict, programs: List[Dict], institute_codes: List[str]) -> str:
        """Построение промпта для подбора программы"""
        import json
        
        institute_names = [data_loader.get_institute_name(code) for code in institute_codes]
        
        resume = self._format_user_resume(user_data)
        
        programs_text = self._format_programs_with_numbers(programs)
        
        institute_names_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(institute_names)])
        
        prompt = f"""
Ты консультант приёмной комиссии Казанского Федерального Университета. Твоя задача - на основе информации о пользователе, 
его ответах на вопросы, а также выбранного ранее экспертной системой института подобрать ОДНУ наиболее подходящую образовательную 
программу из списка программ этого института.

Для этого проанализируй информацию о пользователе и описание учебных программ института / институтов, которые выбрала экспертная система, 
и подбери наиболее подходящую программу, где этому студенту будет интересно учиться!

Входные данные:
{resume}

КРИТИЧЕСКИ ВАЖНО! ВЫБОР ПРОГРАММЫ:
1. Проанализируй ВСЕ пронумерованные программы ниже
2. Выбери ОДНУ наиболее подходящую программу
3. В ответе укажи ТОЛЬКО номер выбранной программы и обоснование выбора
4. НЕ описывай программу полностью - данные о программе будут добавлены автоматически из базы данных

Формат ответа (СТРОГО соблюдай):
[НОМЕР ПРОГРАММЫ]: [Обоснование почему эта программа подойдёт абитуриенту]

Пример ответа:
3: Эта программа идеально подходит абитуриенту, так как она ориентирована на изучение современных технологий программирования, что соответствует его интересам в IT-сфере.

Образовательные программы (пронумерованный список):
{programs_text}
"""
        return prompt
    
    def _format_programs_with_numbers(self, programs: List[Dict]) -> str:
        """Форматирование списка программ с номерами"""
        lines = []
        for i, program in enumerate(programs, 1):
            name = program.get('name', '')
            profile = program.get('profile', '')
            code = program.get('code', '')
            duration = program.get('duration', '')
            budget = program.get('budget_places', 0)
            contract = program.get('contract_places', 0)
            specifics = program.get('specifics', '')
            
            lines.append(f"{i}. {name}")
            if profile:
                lines.append(f"   Профиль: {profile}")
            lines.append(f"   Код: {code}, Срок: {duration}, Места: {budget}б/{contract}к")
            if specifics:
                lines.append(f"   Описание: {specifics}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_user_resume(self, user_data: dict) -> str:
        """Форматирование резюме пользователя"""
        parts = []
        parts.append("Краткое резюме абитуриента:")
        
        if user_data.get('about'):
            parts.append(f"Кратко об абитуриенте и его интересах: {user_data['about']}")
        if user_data.get('profession'):
            parts.append(f"Видение будущей профессии: {user_data['profession']}")
        if user_data.get('subjects'):
            parts.append(f"Предметы с хорошей успеваемостью в школе: {user_data['subjects']}")
        if user_data.get('activities'):
            parts.append(f"Внеучебная деятельность в школе: {user_data['activities']}")
        
        if user_data.get('interest_area'):
            parts.append(f"\nЧто интересно студенту в области: {user_data['interest_area']}. ВАЖНО: Обрати внимание на эту область, на её основе и выбери программу")
        
        if user_data.get('personal_questions'):
            parts.append("\nДополнительные вопросы и ответы, уточняющие образовательную программу пользователя:")
            for i, (q, a) in enumerate(user_data['personal_questions'], 1):
                parts.append(f"{i}. {q} - {a}")
        
        parts.append(f"\nИнностранный абитуриент: {'Да' if user_data.get('is_foreign') else 'Нет'}")
        if user_data.get('is_foreign'):
            parts.append("(Если это иностранный абитуриент, то ищи программы для приёма иностранных граждан)")
        if user_data.get('preferred_form'):
            parts.append(f"Предпочтительная форма обучения: {user_data['preferred_form']} (учитывай только программы с этой формой)")
        
        if user_data.get('exams'):
            parts.append(f"\nДанные о результатах ЕГЭ - также учти их!")
            parts.append(f"Сдаваемые предметы ЕГЭ: {', '.join(user_data['exams'])}")
            if user_data.get('exams_score'):
                parts.append(f"Балл ЕГЭ: {user_data['exams_score']}. На основе этого балла по данным из твоих знаний оцени шанс поступления")
        else:
            parts.append("\n⚠️ Абитуриент еще не сдал ЕГЭ. Учти это при подборе программы.")
        
        return "\n".join(parts)
    
    def _format_programs(self, programs: List[Dict]) -> str:
        """Форматирование списка программ"""
        import json
        return json.dumps(programs, ensure_ascii=False, indent=2)
