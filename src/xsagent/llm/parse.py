import json
import re


def parse_llm_json(raw: str) -> dict:
    """从模型输出中提取 JSON 对象，兼容偶发 markdown 代码块。"""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    return json.loads(text)
