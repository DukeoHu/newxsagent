import json
from collections.abc import AsyncIterator

import httpx

from xsagent.core.config import Settings
from xsagent.llm.base import LLMRequest, LLMResponseError


class DeepSeekProvider:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.deepseek_base_url.rstrip("/")
        self._api_key = settings.deepseek_api_key
        self._model = settings.deepseek_model
        self._reasoning_effort = settings.deepseek_reasoning_effort
        self._thinking_enabled = settings.deepseek_thinking_enabled

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise LLMResponseError("DeepSeek API key is empty")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, request: LLMRequest, stream: bool) -> dict:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "reasoning_effort": self._reasoning_effort,
            "extra_body": {"thinking": {"type": "enabled" if self._thinking_enabled else "disabled"}},
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    async def generate(self, request: LLMRequest) -> str:
        payload = self._payload(request, stream=False)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise LLMResponseError("Empty response from DeepSeek")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise LLMResponseError("Empty content from DeepSeek")
            return content

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        payload = self._payload(request, stream=True)
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield str(content)
