from .base import Messenger
from typing import Any, Optional
from telegram import Bot
from telegram.constants import ParseMode
import asyncio


class TelegramMessenger(Messenger):

    def __init__(self, token: str):
        self.bot = Bot(token=token)

    async def send_message(self, chat_id: str, text: str, reply_markup: Optional[Any] = None) -> None:
        print(f"Sending message to chat_id {chat_id}: {text}")
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

    def receive_message(self, payload: dict) -> str:
        if "message" in payload:
            return payload["message"]["text"]

        if "callback_query" in payload:
            return payload["callback_query"]["data"]

        return ""

    async def download_voice(self, payload: dict) -> bytes:
        max_retries = 3
        retry_delay = 1  # seconds
        download_timeout = 30  # seconds

        voice = payload.get("message", {}).get("voice", {})
        file_id = voice.get("file_id")

        if not file_id:
            raise ValueError("No voice file_id found in payload")

        for attempt in range(max_retries):
            try:
                file = await self.bot.get_file(file_id)
                file_bytes = await file.download_as_bytearray(
                    read_timeout=download_timeout
                )

                return bytes(file_bytes)

            except TimeoutError:
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Download timed out after {max_retries} attempts")
                await asyncio.sleep(retry_delay)

            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Failed to download voice message: {str(e)}")
                await asyncio.sleep(retry_delay)
