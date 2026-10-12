import json
import re
from collections.abc import AsyncIterator

import httpx

from xsagent.core.config import Settings
from xsagent.llm.base import LLMRequest, LLMResponseError


class OllamaProvider:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._think = settings.ollama_think
        self._strip_think_tags = settings.strip_think_tags

    def _clean_response(self, text: str) -> str:
        if not self._strip_think_tags:
            return text
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    async def generate(self, request: LLMRequest) -> str:
        payload: dict = {
            "model": self._model,
            "prompt": request.prompt,
            "stream": False,
            "think": False if request.json_mode else self._think,
        }
        if request.system:
            payload["system"] = request.system
        if request.json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "")
            if not text:
                raise LLMResponseError("Empty response from Ollama")
            return self._clean_response(text)

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        payload: dict = {
            "model": self._model,
            "prompt": request.prompt,
            "stream": True,
            "think": self._think,
        }
        if request.system:
            payload["system"] = request.system

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self._base_url}/api/generate", json=payload
            ) as resp:
                resp.raise_for_status()
                in_think = False
                buffer = ""
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        if not self._strip_think_tags:
                            yield chunk
                            continue

                        buffer += chunk
                        while buffer:
                            if not in_think:
                                start = buffer.find("<think>")
                                if start == -1:
                                    yield buffer
                                    buffer = ""
                                    break
                                if start > 0:
                                    yield buffer[:start]
                                buffer = buffer[start + len("<think>") :]
                                in_think = True
                            else:
                                end = buffer.find("</think>")
                                if end == -1:
                                    buffer = buffer[-16:]
                                    break
                                buffer = buffer[end + len("</think>") :]
                                in_think = False
