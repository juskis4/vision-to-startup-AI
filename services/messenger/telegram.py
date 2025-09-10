from .base import Messenger
from typing import Any, Optional
from telegram import Bot
from telegram.constants import ParseMode


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
