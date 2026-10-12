from xsagent.domain.explore.models import ExploreOption

DEFAULT_EXPLORE_PROMPT = "给我 3 个可采纳的剧情推进方案"

EXPLORE_OPTION_TITLE = "方案 {no}：推进主冲突"
EXPLORE_OPTION_SUMMARY = "围绕 `{prompt}` 提供的第 {no} 个推进方案，强调可直接落盘到蓝图。"
EXPLORE_OPTION_BEAT_OPEN = "在 {chapter_id} 开头承接上一章结果并提出新目标"
EXPLORE_OPTION_BEAT_MIDDLE = "中段引入冲突升级与人物抉择"
EXPLORE_OPTION_BEAT_CLOSE = "末段制造钩子，连接下一章"
EXPLORE_OPTION_CONSTRAINTS = ["不破坏已锁定设定", "保持人物动机一致"]

EXPLORE_SYSTEM = """你是小说情节探索编辑。为同一章给出互相区隔的推进方案，供作者采纳到蓝图。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

EXPLORE_TEMPLATE = """<TASK>
为 {chapter_id} 生成 {count} 个可落盘的情节方案。方案必须彼此不同：冲突切口、信息揭示或人物选择至少有一项明显差异。
遵守硬约束与休眠线程，不得写出 forbidden_reveals。
</TASK>

<USER_PROMPT>
{prompt}
</USER_PROMPT>

<CONSTRAINTS_HARD>
{hard_constraints}
</CONSTRAINTS_HARD>

<CHAPTER_MANDATE>
{chapter_mandate}
</CHAPTER_MANDATE>

<BIBLE_SUMMARY>
{bible_summary}
</BIBLE_SUMMARY>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "options": [
    {{
      "title": "方案标题",
      "summary": "两句以内说明差异点",
      "beats": ["开端", "中段", "章末钩子"],
      "constraints": ["约束"],
      "risk_level": "low|medium|high"
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- options 长度必须为 {count}
- 禁止 markdown 代码块
</OUTPUT_STRICT_RULES>"""

JUDGE_SYSTEM = """你是稳健性评审，不参与写作。对比候选方案，选出最不容易破坏约束、最能推进本章目标的一个。
仅输出合法 JSON，不要 markdown 代码块。"""

JUDGE_TEMPLATE = """<TASK>
从候选方案中选出最优的一个执行。若多个方案收敛，选约束更紧、风险更低者。
</TASK>

<CHAPTER_MANDATE>
{chapter_mandate}
</CHAPTER_MANDATE>

<CONSTRAINTS_HARD>
{hard_constraints}
</CONSTRAINTS_HARD>

<CANDIDATES>
{candidates}
</CANDIDATES>

<OUTPUT_JSON_SCHEMA>
{{
  "winner_option_id": "opt_...",
  "reason": "一句话理由"
}}
</OUTPUT_JSON_SCHEMA>"""


def fallback_options(chapter_id: str, prompt: str, count: int) -> list[ExploreOption]:
    risk_levels: list[str] = ["low", "medium", "high"]
    options: list[ExploreOption] = []
    for i in range(count):
        no = i + 1
        options.append(
            ExploreOption(
                option_id=f"opt_{no}",
                chapter_id=chapter_id,
                title=EXPLORE_OPTION_TITLE.format(no=no),
                summary=EXPLORE_OPTION_SUMMARY.format(prompt=prompt, no=no),
                beats=[
                    EXPLORE_OPTION_BEAT_OPEN.format(chapter_id=chapter_id),
                    EXPLORE_OPTION_BEAT_MIDDLE,
                    EXPLORE_OPTION_BEAT_CLOSE,
                ],
                constraints=list(EXPLORE_OPTION_CONSTRAINTS),
                risk_level=risk_levels[min(i, 2)],  # type: ignore[arg-type]
            )
        )
    return options
