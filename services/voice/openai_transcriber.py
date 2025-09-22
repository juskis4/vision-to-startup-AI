from io import BytesIO
from typing import Optional
from openai import AsyncOpenAI
from .base import Transcriber


class OpenAITranscriber(Transcriber):
    def __init__(self, api_key: str, default_model: str):
        if not api_key:
            raise ValueError("OpenAI API key not provided for transcriber")
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None
    ) -> str:
        if not audio_bytes:
            return ""

        bio = BytesIO(audio_bytes)
        bio.name = "audio.ogg"

        resp = await self.client.audio.transcriptions.create(
            model=self.default_model,
            file=bio,
            language=language,
        )

        return resp.text
