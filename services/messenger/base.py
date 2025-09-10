from abc import ABC, abstractmethod
from typing import Any


class Messenger(ABC):
    @abstractmethod
    def send_message(self, chat_id: str, text: str, reply_markup: Any = None) -> None:
        pass

    @abstractmethod
    def receive_message(self, payload: dict[str, Any]) -> str:
        pass
