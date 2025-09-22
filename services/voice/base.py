from abc import ABC, abstractmethod
from typing import Optional


class Transcriber(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None
    ) -> str:
        raise NotImplementedError("transcribe method must be implemented")
