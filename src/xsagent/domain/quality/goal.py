from pydantic import BaseModel, Field

MIN_CHAPTER_WORDS = 30


class GoalGap(BaseModel):
    code: str
    detail: str


class GoalVerdict(BaseModel):
    satisfied: bool
    impossible: bool = False
    gaps: list[GoalGap] = Field(default_factory=list)
    summary: str = ""

    def feedback_text(self) -> str:
        if self.satisfied:
            return "（无）"
        lines: list[str] = []
        if self.summary:
            lines.append(self.summary)
        for gap in self.gaps:
            lines.append(f"- [{gap.code}] {gap.detail}")
        return "\n".join(lines) or "验收未通过，请补全本章既定目标后再结束。"


def word_count_gap(word_count: int, words_per_chapter: int) -> GoalGap | None:
    del words_per_chapter
    if word_count < MIN_CHAPTER_WORDS:
        return GoalGap(
            code="word_count",
            detail=f"正文过短（{word_count} 字），无法视为成章",
        )
    return None
