"""
Модуль для загрузки данных о программах
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from config import PROGRAMS_FILE, MAG_PROGRAMS_FILE
from utils.logger import logger

class BaseDataLoader:
    """Базовый класс для загрузки и работы с данными о программах"""

    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._data = None
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных из JSON файла"""
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"Данные успешно загружены из {self._file_path}")
        except FileNotFoundError:
            logger.error(f"Файл {self._file_path} не найден")
            self._data = {"institutes": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ({self._file_path}): {e}")
            self._data = {"institutes": {}}
    
    def get_programs_by_institutes(self, institute_codes: List[str]) -> List[Dict[str, Any]]:
        """Получить программы по кодам институтов"""
        programs = []
        for code in institute_codes:
            if code in self._data.get("institutes", {}):
                inst_programs = self._data["institutes"][code].get("programs", [])
                programs.extend(inst_programs)
        return programs
    
    def get_institute_name(self, institute_code: str) -> str:
        """Получить полное название института"""
        return self._data.get("institutes", {}).get(institute_code, {}).get("name", institute_code)
    
    def get_all_programs(self) -> List[Dict[str, Any]]:
        """Получить все программы"""
        all_programs = []
        for inst_data in self._data.get("institutes", {}).values():
            all_programs.extend(inst_data.get("programs", []))
        return all_programs
    
    def filter_programs_by_budget(self, programs: List[Dict[str, Any]], budget_only: bool = False) -> List[Dict[str, Any]]:
        """Фильтрация программ по наличию бюджетных мест"""
        if budget_only:
            return [p for p in programs if p.get("budget_places", 0) > 0]
        return programs
    
    def filter_programs_by_foreign(self, programs: List[Dict[str, Any]], is_foreign: bool = False) -> List[Dict[str, Any]]:
        """Фильтрация программ для иностранных граждан"""
        def _profile_str(p: Dict[str, Any]) -> str:
            # В JSON профили могут быть null -> p.get("profile") вернёт None
            # Явно приводим к строке, чтобы избежать TypeError при использовании оператора `in`
            value = p.get("profile")
            return value if isinstance(value, str) else ""

        if is_foreign:
            return [p for p in programs if "(для приема иностранных граждан)" in _profile_str(p)]
        return [p for p in programs if "(для приема иностранных граждан)" not in _profile_str(p)]


class DataLoader(BaseDataLoader):
    """Загрузчик основной базы программ (бакалавриат / специалитет)"""

    def __init__(self):
        super().__init__(PROGRAMS_FILE)


class MagDataLoader(BaseDataLoader):
    """Загрузчик базы программ магистратуры"""

    def __init__(self):
        super().__init__(MAG_PROGRAMS_FILE)


# Глобальные экземпляры загрузчиков данных
data_loader = DataLoader()
mag_data_loader = MagDataLoader()
