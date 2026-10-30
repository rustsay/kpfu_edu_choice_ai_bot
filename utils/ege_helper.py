"""
Модуль для работы с ЕГЭ и подсказок абитуриентам
"""
from typing import List, Dict, Set, Tuple
from config import INSTITUTE_EXAMS, EXAM_NAMES, MIN_EGE_SCORES
from utils.logger import logger

class EGEChecker:
    """Класс для проверки и подсказок по ЕГЭ"""
    
    @staticmethod
    def get_required_exams_for_institutes(institute_codes: List[str]) -> Dict[str, Dict]:
        """Получить требуемые ЕГЭ для списка институтов"""
        result = {}
        for code in institute_codes:
            if code in INSTITUTE_EXAMS:
                result[code] = INSTITUTE_EXAMS[code]
        return result
    
    @staticmethod
    def check_exams_compatibility(user_exams: List[str], institute_code: str) -> Tuple[bool, List[str], str]:
        """
        Проверить совместимость сданных ЕГЭ с требованиями института
        Возвращает: (совместимо, недостающие предметы, сообщение)
        """
        if institute_code not in INSTITUTE_EXAMS:
            return False, [], "Институт не найден в базе данных"
        
        exam_info = INSTITUTE_EXAMS[institute_code]
        required = exam_info.get("required", [])
        optional = exam_info.get("optional", [])
        
        user_exams_lower = [exam.lower().strip() for exam in user_exams]
        
        # Проверяем обязательные предметы
        missing_required = []
        for req in required:
            # Проверяем точное совпадение или вхождение
            found = False
            for user_exam in user_exams_lower:
                if req.lower() in user_exam or user_exam in req.lower():
                    found = True
                    break
            if not found:
                missing_required.append(req)
        
        # Если не хватает обязательных - не подходит
        if missing_required:
            msg = f"Не хватает обязательных ЕГЭ: {', '.join([EXAM_NAMES.get(e, e) for e in missing_required])}"
            return False, missing_required, msg
        
        # Проверяем, что русский язык есть (обязателен для всех)
        has_russian = any("русский" in exam.lower() for exam in user_exams_lower)
        if not has_russian:
            return False, ["русский"], "Русский язык обязателен для всех направлений"
        
        # Если все обязательные есть - совместимо
        return True, [], "Все обязательные ЕГЭ сданы"
    
    @staticmethod
    def get_missing_exams(user_exams: List[str], institute_code: str) -> List[str]:
        """Получить список недостающих ЕГЭ для института"""
        if institute_code not in INSTITUTE_EXAMS:
            return []
        
        exam_info = INSTITUTE_EXAMS[institute_code]
        required = exam_info.get("required", [])
        user_exams_lower = [exam.lower().strip() for exam in user_exams]
        
        missing = []
        for req in required:
            found = False
            for user_exam in user_exams_lower:
                if req.lower() in user_exam or user_exam in req.lower():
                    found = True
                    break
            if not found:
                missing.append(req)
        
        return missing
    
    @staticmethod
    def check_minimum_scores(user_exams: Dict[str, int]) -> Tuple[bool, List[str]]:
        """
        Проверить, соответствуют ли баллы минимальным требованиям
        user_exams: словарь {название_предмета: балл}
        Возвращает: (все_баллы_достаточны, список_предметов_с_недостаточными_баллами)
        """
        insufficient = []
        for exam_name, score in user_exams.items():
            exam_key = exam_name.lower().strip()
            # Ищем минимальный балл для предмета
            min_score = None
            for key, min_val in MIN_EGE_SCORES.items():
                if key in exam_key or exam_key in key:
                    min_score = min_val
                    break
            
            if min_score and score < min_score:
                insufficient.append(f"{EXAM_NAMES.get(exam_key, exam_name)}: {score} < {min_score}")
        
        return len(insufficient) == 0, insufficient
    
    @staticmethod
    def format_exams_for_user(exams: List[str]) -> str:
        """Форматировать список ЕГЭ для отображения пользователю"""
        formatted = []
        for exam in exams:
            # Получаем полное название или используем исходное
            full_name = EXAM_NAMES.get(exam, exam.capitalize())
            formatted.append(f"• {full_name}")
        return "\n".join(formatted)
    
    @staticmethod
    def get_recommended_exams_for_direction(institute_codes: List[str]) -> Dict[str, List[str]]:
        """Получить рекомендуемые ЕГЭ для выбранных направлений"""
        all_required = set()
        all_optional = set()
        
        for code in institute_codes:
            if code in INSTITUTE_EXAMS:
                exam_info = INSTITUTE_EXAMS[code]
                all_required.update(exam_info.get("required", []))
                all_optional.update(exam_info.get("optional", []))
        
        # Убираем дубликаты (если предмет есть и в required, и в optional)
        all_optional = all_optional - all_required
        
        return {
            "required": sorted(list(all_required)),
            "optional": sorted(list(all_optional)),
            "all": sorted(list(all_required | all_optional))
        }
    
    @staticmethod
    def generate_ege_advice(institute_codes: List[str], user_exams: List[str] = None, user_scores: Dict[str, int] = None) -> str:
        """Сгенерировать совет по ЕГЭ для абитуриента"""
        if not institute_codes:
            return "Для начала выберите интересующее направление."
        
        advice_parts = []
        
        # Получаем требуемые ЕГЭ для выбранных институтов
        exam_info = EGEChecker.get_recommended_exams_for_direction(institute_codes)
        required = exam_info["required"]
        optional = exam_info["optional"]
        
        if user_exams:
            # Если пользователь уже сдал ЕГЭ, проверяем совместимость
            compatibility_results = []
            missing_by_institute = {}
            
            for code in institute_codes:
                is_compatible, missing, msg = EGEChecker.check_exams_compatibility(user_exams, code)
                if not is_compatible:
                    missing_by_institute[code] = missing
                compatibility_results.append((code, is_compatible, missing))
            
            # Проверяем минимальные баллы, если они указаны
            if user_scores:
                scores_ok, insufficient = EGEChecker.check_minimum_scores(user_scores)
                if not scores_ok:
                    advice_parts.append("⚠️ ВНИМАНИЕ: Некоторые ваши баллы ниже минимальных требований:")
                    for item in insufficient:
                        advice_parts.append(f"  • {item}")
                    advice_parts.append("\nМинимальные баллы для поступления в КФУ (2025-2026):")
                    for exam in required:
                        if exam in MIN_EGE_SCORES:
                            advice_parts.append(f"  • {EXAM_NAMES.get(exam, exam)}: {MIN_EGE_SCORES[exam]} баллов")
                    advice_parts.append("")
            
            # Проверяем совместимость
            compatible_institutes = [code for code, is_ok, _ in compatibility_results if is_ok]
            if compatible_institutes:
                advice_parts.append("✅ Ваши ЕГЭ подходят для поступления в следующие институты:")
                for code in compatible_institutes:
                    if code in INSTITUTE_EXAMS:
                        desc = INSTITUTE_EXAMS[code].get("description", "")
                        advice_parts.append(f"  • {code}: {desc}")
                
                if len(compatible_institutes) < len(institute_codes):
                    advice_parts.append("\n⚠️ Для некоторых институтов не хватает ЕГЭ:")
                    for code, is_ok, missing in compatibility_results:
                        if not is_ok and missing:
                            exam_names = [EXAM_NAMES.get(m, m) for m in missing]
                            advice_parts.append(f"  • {code}: требуется {', '.join(exam_names)}")
            else:
                advice_parts.append("❌ Ваши ЕГЭ не подходят для выбранных направлений.")
                advice_parts.append("\n📋 Необходимые ЕГЭ:")
                advice_parts.append(EGEChecker.format_exams_for_user(required))
                if optional:
                    advice_parts.append("\nДополнительно могут потребоваться:")
                    advice_parts.append(EGEChecker.format_exams_for_user(optional))
        else:
            # Если ЕГЭ еще не сданы, даем рекомендации
            advice_parts.append("📚 Для поступления на выбранные направления необходимо сдать следующие ЕГЭ:")
            advice_parts.append("\n🔴 ОБЯЗАТЕЛЬНЫЕ:")
            advice_parts.append(EGEChecker.format_exams_for_user(required))
            
            if optional:
                advice_parts.append("\n🟡 ДОПОЛНИТЕЛЬНЫЕ (могут потребоваться для некоторых программ):")
                advice_parts.append(EGEChecker.format_exams_for_user(optional))
            
            advice_parts.append("\n💡 Важная информация:")
            advice_parts.append("• Русский язык обязателен для ВСЕХ направлений")
            if "профиль" in required:
                advice_parts.append("• Математика (профильный уровень) обязательна для технических направлений")
            advice_parts.append("• Обычно требуется 3 ЕГЭ")
            advice_parts.append("\n📊 Минимальные баллы для поступления в КФУ (2026-2027):")
            for exam in required:
                if exam in MIN_EGE_SCORES:
                    advice_parts.append(f"  • {EXAM_NAMES.get(exam, exam)}: минимум {MIN_EGE_SCORES[exam]} баллов")
            advice_parts.append("\n⚠️ Обратите внимание: проходные баллы могут быть значительно выше минимальных!")
        
        return "\n".join(advice_parts)
