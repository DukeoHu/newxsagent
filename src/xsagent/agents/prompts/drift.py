DRIFT_SYSTEM = """你是小说一致性审查员。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

DRIFT_TEMPLATE = """<TASK>
对比 Bible 与最新章节，找出不一致并输出 findings JSON。
检查维度：时间线、人物状态、世界观规则、伏笔。
</TASK>

<BIBLE_SUMMARY>
{bible_summary}
</BIBLE_SUMMARY>

<CHAPTER_ID>
{chapter_id}
</CHAPTER_ID>

<CHAPTER_CONTENT>
{content}
</CHAPTER_CONTENT>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "findings": [
    {{
      "id": "finding_1",
      "type": "timeline|character|world|foreshadowing",
      "severity": "low|medium|high",
      "description": "...",
      "suggested_patch": {{"updates": [], "risk_level": "...", "explanation": "..."}}
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""
