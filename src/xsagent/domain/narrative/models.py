from typing import Any, Literal

from pydantic import BaseModel, Field

ChapterRole = Literal["setup", "breather", "bridge", "escalation", "payoff"]
PriorityCurve = Literal["high_early", "low_early_high_mid", "steady"]


class ThreadStage(BaseModel):
    level: int = 0
    id: str
    label: str = ""
    ceiling: str = ""


class ThreadMilestone(BaseModel):
    id: str
    summary: str
    earliest_chapter: int = 1


class NarrativeThread(BaseModel):
    id: str
    label: str = ""
    priority_curve: PriorityCurve = "steady"
    milestones: list[ThreadMilestone] = Field(default_factory=list)
    stages: list[ThreadStage] = Field(default_factory=list)


class ThreadLedgerState(BaseModel):
    progress_level: int = 0
    current_stage: str = ""
    last_progress_chapter: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


class RelationshipPairState(BaseModel):
    chars: list[str] = Field(default_factory=list)
    intimacy_level: int = 0
    current_stage: str = "unaware"
    last_interaction_chapter: str | None = None
    interaction_history: list[dict[str, Any]] = Field(default_factory=list)


class RelationshipLedger(BaseModel):
    pairs: list[RelationshipPairState] = Field(default_factory=list)


class ChapterMandate(BaseModel):
    chapter_id: str = ""
    chapter_no: int = 0
    tier: str = "opening"
    chapter_role: ChapterRole = "setup"
    primary_thread: str = "main"
    dormant_threads: list[str] = Field(default_factory=list)
    thread_ceilings: dict[str, str] = Field(default_factory=dict)
    romance_ceiling: str = ""
    narrative_goal: str = ""
    milestone_targets: list[str] = Field(default_factory=list)
    thread_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
    relationship_state: dict[str, Any] = Field(default_factory=dict)

    def to_prompt_text(self) -> str:
        ceiling_lines = [
            f"- {thread_id}: {text}"
            for thread_id, text in self.thread_ceilings.items()
            if text
        ]
        state_lines = [
            f"- {thread_id}: level={state.get('progress_level', 0)}, "
            f"stage={state.get('current_stage', '')}"
            for thread_id, state in self.thread_states.items()
        ]
        return (
            f"章节角色：{self.chapter_role}\n"
            f"主推进线程：{self.primary_thread}\n"
            f"休眠线程（本章禁止推进）：{', '.join(self.dormant_threads) or '无'}\n"
            f"本章叙事目标：{self.narrative_goal}\n"
            f"可兑现里程碑：{', '.join(self.milestone_targets) or '无'}\n"
            f"各线程推进上限：\n{chr(10).join(ceiling_lines) if ceiling_lines else '- 无'}\n"
            f"各线程当前进度：\n{chr(10).join(state_lines) if state_lines else '- 无'}"
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
