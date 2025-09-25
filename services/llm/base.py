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
        raise NotImplementedError("generate method must be implemented")

    @abstractmethod
    async def generate_parse(
        self,
        user_input: str,
        *,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        schema: Any = None,
        web_search: bool = False
    ) -> str:
        raise NotImplementedError("generate_parse method must be implemented")
