"""各叙事线程的进度台阶与账本读写。"""

from __future__ import annotations

from typing import Any

from xsagent.domain.narrative.models import NarrativeThread, ThreadStage

DEFAULT_THREAD_STAGES: dict[str, list[dict[str, Any]]] = {
    "main": [
        {
            "level": 0,
            "id": "situation",
            "label": "处境确认",
            "ceiling": "仅允许确认当前处境、日常细节与轻微违和；禁止进入卷内核心冲突高潮",
        },
        {
            "level": 1,
            "id": "adaptation",
            "label": "适应调整",
            "ceiling": "允许适应新环境、建立基本生活节奏；禁止提前引爆主线大转折",
        },
        {
            "level": 2,
            "id": "first_conflict",
            "label": "初次冲突",
            "ceiling": "允许引入第一个明确冲突或目标；禁止直接兑现卷末 payoff",
        },
        {
            "level": 3,
            "id": "escalation",
            "label": "冲突升级",
            "ceiling": "允许冲突升级与阶段性抉择；禁止终局级揭晓",
        },
        {
            "level": 4,
            "id": "payoff",
            "label": "阶段兑现",
            "ceiling": "允许推进至本卷阶段目标相关的高潮与收束",
        },
    ],
    "romance": [
        {
            "level": 0,
            "id": "unaware",
            "label": "无交集",
            "ceiling": "禁止男女主任何形式的直接交流；仅允许同班同框、远观或他人侧面提及",
        },
        {
            "level": 1,
            "id": "distant_awareness",
            "label": "远观印象",
            "ceiling": "允许远观、侧面印象；禁止搭话、对视交流、独处",
        },
        {
            "level": 2,
            "id": "indirect_link",
            "label": "间接关联",
            "ceiling": "允许课堂点名、第三人转述等间接关联；禁止主动搭讪、私下邀约",
        },
        {
            "level": 3,
            "id": "cold_exchange",
            "label": "冷淡交锋",
            "ceiling": "允许简短对话、学术互怼；禁止暧昧、单独相处、情感表露",
        },
        {
            "level": 4,
            "id": "rapport",
            "label": "默契互动",
            "ceiling": "允许合作、互怼升温；禁止明确告白或确立关系",
        },
        {
            "level": 5,
            "id": "emotional_shift",
            "label": "情感转折",
            "ceiling": "允许破冰、暧昧暗示与情感推进",
        },
    ],
    "academic": [
        {
            "level": 0,
            "id": "baseline",
            "label": "学业基线",
            "ceiling": "仅允许展示当前成绩水平与学习习惯；禁止跳级取得重大竞赛成果",
        },
        {
            "level": 1,
            "id": "small_win",
            "label": "小试牛刀",
            "ceiling": "允许小测验、课堂表现提升；禁止省级以上竞赛获奖",
        },
        {
            "level": 2,
            "id": "recognition",
            "label": "崭露头角",
            "ceiling": "允许校内认可、老师关注；禁止全国级名次或保送揭晓",
        },
        {
            "level": 3,
            "id": "breakthrough",
            "label": "关键突破",
            "ceiling": "允许重要考试/竞赛阶段性胜利；禁止直接跳到高考终局结果",
        },
        {
            "level": 4,
            "id": "mastery",
            "label": "学业大成",
            "ceiling": "允许学业线阶段性封顶式成果",
        },
    ],
    "mystery": [
        {
            "level": 0,
            "id": "unease",
            "label": "轻微违和",
            "ceiling": "仅允许细节违和、未解疑问；禁止揭示谜底或规则真相",
        },
        {
            "level": 1,
            "id": "clue",
            "label": "线索浮现",
            "ceiling": "允许埋设可验证线索；禁止解释线索背后的完整真相",
        },
        {
            "level": 2,
            "id": "pattern",
            "label": "规律初现",
            "ceiling": "允许角色察觉模式但未证实；禁止第一层真相揭晓",
        },
        {
            "level": 3,
            "id": "partial_truth",
            "label": "局部真相",
            "ceiling": "允许揭开局部真相；禁止终局级世界观揭晓",
        },
        {
            "level": 4,
            "id": "revelation",
            "label": "关键揭晓",
            "ceiling": "允许本卷悬疑线关键揭晓",
        },
    ],
}


def stages_for_thread(thread: NarrativeThread) -> list[ThreadStage]:
    if thread.stages:
        return thread.stages
    defaults = DEFAULT_THREAD_STAGES.get(thread.id, DEFAULT_THREAD_STAGES["main"])
    return [ThreadStage.model_validate(item) for item in defaults]


def ceiling_for_level(thread: NarrativeThread, level: int) -> str:
    stages = stages_for_thread(thread)
    clamped = max(0, min(level, len(stages) - 1))
    return stages[clamped].ceiling


def stage_id_for_level(thread: NarrativeThread, level: int) -> str:
    stages = stages_for_thread(thread)
    clamped = max(0, min(level, len(stages) - 1))
    return stages[clamped].id


def parse_thread_ledgers(plot_section: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ledgers: dict[str, dict[str, Any]] = {}
    raw = plot_section.get("thread_ledgers")
    if isinstance(raw, dict):
        for thread_id, state in raw.items():
            if isinstance(state, dict):
                ledgers[str(thread_id)] = dict(state)

    legacy = plot_section.get("relationship_ledger")
    if isinstance(legacy, dict) and legacy.get("pairs"):
        pair = legacy["pairs"][0] if isinstance(legacy["pairs"], list) else {}
        if isinstance(pair, dict):
            ledgers.setdefault(
                "romance",
                {
                    "progress_level": int(pair.get("intimacy_level", 0)),
                    "current_stage": pair.get("current_stage", "unaware"),
                    "last_progress_chapter": pair.get("last_interaction_chapter"),
                    "pair": pair.get("chars", []),
                    "history": pair.get("interaction_history", []),
                },
            )
    return ledgers


def thread_state(
    ledgers: dict[str, dict[str, Any]],
    thread: NarrativeThread,
) -> dict[str, Any]:
    existing = ledgers.get(thread.id, {})
    level = int(existing.get("progress_level", 0))
    return {
        "thread_id": thread.id,
        "label": thread.label,
        "progress_level": level,
        "current_stage": existing.get("current_stage") or stage_id_for_level(thread, level),
        "last_progress_chapter": existing.get("last_progress_chapter"),
        "ceiling": ceiling_for_level(thread, level),
        "metadata": {
            key: value
            for key, value in existing.items()
            if key
            not in {
                "progress_level",
                "current_stage",
                "last_progress_chapter",
                "history",
            }
        },
    }


def default_romance_pair(characters: list[dict[str, Any]]) -> list[str] | None:
    if not characters:
        return None
    lead_ids: list[str] = []
    for char in characters:
        if not isinstance(char, dict):
            continue
        role = str(char.get("role", ""))
        char_id = char.get("id")
        if not char_id:
            continue
        if "主角" in role or role.lower() in {"protagonist", "lead"}:
            lead_ids.insert(0, str(char_id))
        elif any(token in role for token in ("女主", "男主", "感情", "love")):
            lead_ids.append(str(char_id))
    if len(lead_ids) >= 2:
        return lead_ids[:2]
    if len(characters) >= 2 and lead_ids:
        other = next(
            (
                str(c.get("id"))
                for c in characters
                if isinstance(c, dict) and str(c.get("id")) not in lead_ids
            ),
            None,
        )
        if other:
            return [lead_ids[0], other]
    return None
