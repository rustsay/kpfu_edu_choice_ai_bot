"""
Управление состоянием пользователей
"""
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class UserState:
    """Класс для хранения состояния пользователя"""
    chat_id: int
    step: str = "start"
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def update(self, **kwargs):
        """Обновить данные пользователя"""
        self.data.update(kwargs)
    
    def get(self, key: str, default=None):
        """Получить значение по ключу"""
        return self.data.get(key, default)
    
    def clear(self):
        """Очистить состояние"""
        self.data.clear()
        self.step = "start"

class UserStateManager:
    """Менеджер состояний пользователей"""
    
    def __init__(self):
        self._states: Dict[int, UserState] = {}
    
    def get_state(self, chat_id: int) -> UserState:
        """Получить состояние пользователя"""
        if chat_id not in self._states:
            self._states[chat_id] = UserState(chat_id=chat_id)
        return self._states[chat_id]
    
    def clear_state(self, chat_id: int):
        """Очистить состояние пользователя"""
        if chat_id in self._states:
            self._states[chat_id].clear()
    
    def remove_state(self, chat_id: int):
        """Удалить состояние пользователя"""
        if chat_id in self._states:
            del self._states[chat_id]

# Глобальный менеджер состояний
state_manager = UserStateManager()
