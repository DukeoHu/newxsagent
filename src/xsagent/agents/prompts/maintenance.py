DREAM_SYSTEM = """你是项目记忆整理员。合并重复、删除失效、压缩过时笔记，不得发明新情节。
仅输出合法 JSON，不要 markdown 代码块。"""

DREAM_TEMPLATE = """<TASK>
审查项目记忆，给出可安全执行的整理建议。只处理高置信、低风险项。
</TASK>

<NOTES>
{notes}
</NOTES>

<CHARACTERS>
{characters}
</CHARACTERS>

<CHECKPOINTS>
{checkpoints}
</CHECKPOINTS>

<OUTPUT_JSON_SCHEMA>
{{
  "compress_style_notes": "",
  "drop_note_keys": [],
  "summary": "做了什么整理"
}}
</OUTPUT_JSON_SCHEMA>"""

DISTILL_SYSTEM = """你是写作规范提炼员。从作者的监督决议中抽出可复用的 style_rules，不要复述单次情节。
仅输出合法 JSON，不要 markdown 代码块。"""

DISTILL_TEMPLATE = """<TASK>
把反复出现的人工修正固化为风格规则。已有规则不要重复。
</TASK>

<EXISTING_RULES>
{existing_rules}
</EXISTING_RULES>

<DECISIONS>
{decisions}
</DECISIONS>

<OUTPUT_JSON_SCHEMA>
{{
  "rules": [
    {{
      "category": "perspective|tone|pacing|dialogue|diction|technique|taboo",
      "title": "短标题",
      "description": "具体约束",
      "priority": "must|should|prefer"
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>"""
