GOAL_SYSTEM = """你是独立的章节完成度验收员，不参与写作，不对已写文字产生认同。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

GOAL_TEMPLATE = """<TASK>
判断本章是否真正写完。你每次看到与写作者相同的正文与约束。
停止条件：蓝图 beats 均已在正文兑现；未推进 dormant_threads；未写出 forbidden_reveals；遵守 hard_constraints 与 chapter_mandate。
不得因为「已经写了不少」或「语气完整」而放行。若信息不足、目标互相矛盾导致不可能完成，设 impossible=true。
</TASK>

<CHAPTER_ID>
{chapter_id}
</CHAPTER_ID>

<WORD_COUNT>
实际 {word_count} 字 / 目标约 {words_per_chapter} 字
</WORD_COUNT>

<BEATS>
{beats}
</BEATS>

<DORMANT_THREADS>
{dormant_threads}
</DORMANT_THREADS>

<FORBIDDEN_REVEALS>
{forbidden_reveals}
</FORBIDDEN_REVEALS>

<CONSTRAINTS_HARD>
{hard_constraints}
</CONSTRAINTS_HARD>

<CHAPTER_MANDATE>
{chapter_mandate}
</CHAPTER_MANDATE>

<CHAPTER_CONTENT>
{content}
</CHAPTER_CONTENT>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "satisfied": true,
  "impossible": false,
  "gaps": [{{"code": "beats|word_count|dormant_threads|spoiler|hard_constraints|other", "detail": "..."}}],
  "summary": "一句话说明通过或差距"
}}
</OUTPUT_JSON_SCHEMA>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
- satisfied=true 时 gaps 必须为空数组
</OUTPUT_STRICT_RULES>"""
