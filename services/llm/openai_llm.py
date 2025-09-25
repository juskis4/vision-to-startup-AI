from typing import Any, Optional

from openai import AsyncOpenAI
from .base import LLM


class OpenAILLM(LLM):
    def __init__(self, api_key: str):

        if not api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = AsyncOpenAI(api_key=api_key, timeout=360)

    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:

        messages = []

        if options is None:
            raise ValueError(
                "LLM options missing")

        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.responses.create(
            model=options["model"],
            input=messages,
            max_output_tokens=options["max_tokens"],
        )

        return response.choices[0].message.content or ""

    async def generate_parse(
        self,
        user_input: str,
        *,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        schema: Any = None,
        web_search: bool = False
    ) -> str:

        messages = []

        if options is None:
            raise ValueError("LLM options missing")

        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_input})

        request_params = {
            "model": options["model"],
            "max_output_tokens": options["max_tokens"],
            "input": messages,
            "text_format": schema,
        }

        if web_search:
            request_params["tools"] = [{"type": "web_search"}]

        response = await self.client.responses.parse(**request_params)

        return response.output_parsed
