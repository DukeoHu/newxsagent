"""写作风格规则：格式化与 prompt 注入。"""

from __future__ import annotations

from typing import Any

_PRIORITY_ORDER = {"must": 0, "should": 1, "prefer": 2}
_CATEGORY_LABELS = {
    "perspective": "视角",
    "tone": "基调",
    "pacing": "节奏",
    "dialogue": "对话",
    "diction": "用词",
    "technique": "技法",
    "taboo": "禁忌",
}
_PRIORITY_LABELS = {
    "must": "必须",
    "should": "应当",
    "prefer": "偏好",
}


def style_rules_prompt_text(rules: list[Any] | None, *, max_chars: int = 1200) -> str:
    """将 style_rules 列表格式化为写作 prompt 文本。"""
    if not rules:
        return "（无结构化风格规则）"

    items: list[dict[str, Any]] = [r for r in rules if isinstance(r, dict)]
    if not items:
        return "（无结构化风格规则）"

    items.sort(key=lambda r: _PRIORITY_ORDER.get(str(r.get("priority", "should")), 9))
    lines: list[str] = []
    for index, rule in enumerate(items, start=1):
        category = str(rule.get("category", "tone"))
        priority = str(rule.get("priority", "should"))
        cat_label = _CATEGORY_LABELS.get(category, category)
        pri_label = _PRIORITY_LABELS.get(priority, priority)
        title = str(rule.get("title", "")).strip() or f"规则{index}"
        description = str(rule.get("description", "")).strip()
        body = f"{title}：{description}" if description and description != title else title
        lines.append(f"{index}. [{pri_label}/{cat_label}] {body}")

    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 10] + "\n…（已截断）"
