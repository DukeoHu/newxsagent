ONBOARDING_QUESTION_SYSTEM = """你是资深网文策划编辑，负责通过简短问答帮助作者明确长篇小说的核心设定。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

ONBOARDING_QUESTION_TEMPLATE = """<TASK>
提出下一个最有价值的创作引导问题（一次只问一件事）。
若已收集足够信息，则标记 ready_to_generate=true 并不再提问。
</TASK>

<PROJECT>
《{project_name}》｜题材：{genre}
</PROJECT>

<TURN_STATE>
当前是第 {turn_index} 轮提问（至少 {min_turns} 轮、最多 {max_turns} 轮后应可生成设定）。
</TURN_STATE>

<TRANSCRIPT>
{transcript}
</TRANSCRIPT>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "ready_to_generate": false,
  "question_id": "q_{turn_index}",
  "question": "你的问题（ready_to_generate 为 true 时可为空）",
  "hint": "给作者的填写提示（可选）"
}}
</OUTPUT_JSON_SCHEMA>

<RULES>
- 问题应覆盖：核心灵感、主角、世界观、主线冲突、写作风格偏好、开篇方向（按需追问）
- 写作风格可追问：叙事视角、文风基调、节奏快慢、对话风格、禁用套路、特殊语言习惯等
- 不要重复已问过的问题
- 当 ready_to_generate 为 true 时，question 留空字符串
- 通常 ≥{min_turns} 轮有效回答后可标记 ready_to_generate
</RULES>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""

ONBOARDING_GENERATE_SYSTEM = """你是 Story Bible 架构师。根据创作引导对话，生成完整初始 Story Bible。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

ONBOARDING_GENERATE_TEMPLATE = """<TASK>
根据引导对话生成初始 Story Bible（所有 id 使用 snake_case）。
</TASK>

<PROJECT>
《{project_name}》｜题材：{genre}
</PROJECT>

<TRANSCRIPT>
{transcript}
</TRANSCRIPT>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "bible": {{
    "characters": {{
      "characters": [
        {{"id": "char_main", "name": "...", "role": "主角", "goal": "...", "arc": "...", "current_state": "...", "description": "..."}}
      ],
      "locked_fields": []
    }},
    "plot": {{
      "acts": [{{"id": "act_1", "title": "...", "summary": "..."}}],
      "themes": ["主题1", "主题2"],
      "foreshadowing": [
        {{
          "id": "fs_1",
          "hook": "伏笔名称",
          "plant_hint": "早期如何暗示（细节/违和感/未解疑问）",
          "plant_from_chapter": 1,
          "reveal_after_chapter": 50,
          "reveal_detail": "后期才揭晓的真相（仅供策划，不可写入早期章节）"
        }}
      ],
      "locked_fields": []
    }},
    "world": {{
      "rules": [{{"id": "rule_1", "title": "...", "description": "..."}}],
      "locations": [{{"id": "loc_1", "name": "...", "description": "..."}}],
      "locked_fields": []
    }},
    "timeline": {{
      "events": [{{"id": "evt_1", "chapter": "ch_001", "summary": "开篇事件"}}],
      "locked_fields": []
    }},
    "notes": {{
      "style_notes": "一句话概括整体文风（视角+节奏+基调）",
      "style_rules": [
        {{
          "id": "sr_1",
          "category": "perspective",
          "title": "规则短标题",
          "description": "可执行的写作约束说明",
          "priority": "must"
        }}
      ],
      "author_notes": "面向写作的公开设定摘要（不含后续卷/终局剧透）",
      "spoiler_vault": "全书结构与终局真相（仅供总纲/后期蓝图，禁止写入早期章节）",
      "locked_fields": []
    }}
  }}
}}
</OUTPUT_JSON_SCHEMA>

<RULES>
- 忠实依据引导对话提取设定；人物名、地点名、核心冲突优先沿用作者原话
- 禁止凭空编造对话中未出现的关键专有名词（如新主角名、新组织名、新地点名）
- 若对话信息不足，可做最小补全，但必须保持“可被对话支持”
- 内容具体、彼此一致，角色至少 2 人（含主角），地点与规则与题材匹配
- notes.style_rules 必须根据对话中的风格偏好生成 4–8 条可执行写作规则；category 仅允许：perspective|tone|pacing|dialogue|diction|technique|taboo；priority 仅允许：must|should|prefer
- notes.style_rules 每条须具体可落地（如“第三人称限知跟随主角”“禁用系统面板口吻”），禁止空泛口号
- notes.style_notes 用 1–2 句概括 style_rules 的整体风格，与规则一致
- 若作者未明确风格，按题材做最小合理推断，并在 style_rules 中体现
- notes.author_notes 只写当前开篇阶段可见信息：核心灵感、主角当下目标、开篇冲突、风格偏好；禁止写入后续卷/终局谜底
- notes.spoiler_vault 收纳完整分卷结构与终局真相；生成总纲时会下放到每卷 opening_knowledge / forbidden_reveals
- plot.foreshadowing 必须列出作者提到的重要伏笔，并标注 plant_from_chapter / reveal_after_chapter
</RULES>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""

# Simulator 测试用引导问题序列
SIM_ONBOARDING_QUESTIONS = [
    "你想描述的故事是什么，可以给出整体故事结构哟",
    "主角是谁？他/她此刻的处境、核心目标与最大困境是什么？",
    "故事发生在怎样的世界？有哪些关键规则或独特设定？",
    "主线冲突是什么？反派或阻碍力量如何推动剧情？",
    "你希望读者感受到什么基调？写作上有无视角、节奏、对话或禁用套路方面的偏好？",
    "开篇第一个场景你想怎么展开？",
]

SIM_ONBOARDING_HINT = "尽量具体，有助于生成更完整的 Story Bible。"
SIM_ONBOARDING_READY_HINT = "信息已足够，可以生成设定草案。"
