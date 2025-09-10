from abc import ABC, abstractmethod
from typing import Any, Optional


class LLM(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_parse(
        self,
        user_input: str,
        *,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        schema: Any = None
    ) -> str:
        raise NotImplementedError
