"""本章硬约束：由 Mandate 派生，优先级高于自由文本 constraints。"""

from __future__ import annotations

from typing import Any

from xsagent.domain.narrative.models import ChapterMandate

# 休眠线程触发的敏感词（命中则弱化 beats）
_ROMANCE_WORDS = (
    "搭话",
    "搭讪",
    "表白",
    "告白",
    "暧昧",
    "约会",
    "牵手",
    "亲吻",
    "独处",
    "互怼",
    "主动接近",
    "情感升温",
    "感情推进",
)
_MYSTERY_WORDS = ("真相", "揭晓", "幕后黑手", "谜底", "原来是")
_ACADEMIC_WORDS = ("竞赛冠军", "保送", "状元", "全国第")


def hard_constraints_from_mandate(mandate: ChapterMandate) -> dict[str, Any]:
    return {
        "primary_thread": mandate.primary_thread,
        "dormant_threads": list(mandate.dormant_threads),
        "chapter_role": mandate.chapter_role,
        "tier": mandate.tier,
        "thread_ceilings": dict(mandate.thread_ceilings),
        "romance_ceiling": mandate.romance_ceiling,
        "narrative_goal": mandate.narrative_goal,
        "milestone_targets": list(mandate.milestone_targets),
    }


def hard_constraints_prompt_text(hard: dict[str, Any]) -> str:
    if not hard:
        return "（无硬约束）"
    dormant = hard.get("dormant_threads") or []
    ceilings = hard.get("thread_ceilings") or {}
    ceiling_lines = [
        f"- {tid}: {text}" for tid, text in ceilings.items() if text
    ]
    return (
        f"章节角色：{hard.get('chapter_role', '')}\n"
        f"位阶：{hard.get('tier', '')}\n"
        f"主推进线程：{hard.get('primary_thread', '')}\n"
        f"休眠线程（禁止推进）：{', '.join(dormant) or '无'}\n"
        f"叙事目标：{hard.get('narrative_goal', '')}\n"
        f"可兑现里程碑：{', '.join(hard.get('milestone_targets') or []) or '无'}\n"
        f"各线程推进上限：\n{chr(10).join(ceiling_lines) if ceiling_lines else '- 无'}"
    )


def scrub_beats_against_hard_constraints(
    beats: list[str],
    hard: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """剔除/改写明显违反休眠线程的 beats，返回 (新beats, 冲突说明)。"""
    dormant = set(hard.get("dormant_threads") or [])
    scrubbed: list[str] = []
    conflicts: list[str] = []

    for beat in beats:
        text = str(beat)
        lowered = text
        conflict = False
        reason = ""

        if "romance" in dormant and any(w in lowered for w in _ROMANCE_WORDS):
            conflict = True
            reason = "触及休眠感情线"
            text = "可远观相关人物或侧面提及，但不推进感情互动"
        elif "mystery" in dormant and any(w in lowered for w in _MYSTERY_WORDS):
            conflict = True
            reason = "触及休眠悬疑揭晓"
            text = "仅保留轻微违和感，不揭示谜底"
        elif "academic" in dormant and any(w in lowered for w in _ACADEMIC_WORDS):
            conflict = True
            reason = "触及休眠学业高潮"
            text = "可展示日常学习状态，不兑现重大学业成果"

        if conflict:
            conflicts.append(f"{beat} → {reason}")
        scrubbed.append(text)

    # 去重保序
    seen: set[str] = set()
    unique: list[str] = []
    for item in scrubbed:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique, conflicts
