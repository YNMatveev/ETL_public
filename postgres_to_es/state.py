import abc
from pathlib import Path
from typing import Any, Optional

import yaml


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""


class YamlFileStorage(BaseStorage):
    """
    Класс для работы с хранилищем в yaml-файле
    """
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as config_file:
            yaml.safe_dump(state, config_file)

    def retrieve_state(self) -> dict:
        if Path(self.file_path).is_file():
            with open(self.file_path, 'r', encoding='utf-8') as config_file:
                current_state = yaml.safe_load(config_file)
            return current_state or {}
        return {}


class State:
    """
    Класс для хранения состояния при работе с данными.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.current_state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        self.current_state.update({key: value})
        self.storage.save_state(self.current_state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        return self.current_state.get(key)
