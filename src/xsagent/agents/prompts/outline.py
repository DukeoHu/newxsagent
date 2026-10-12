OUTLINE_MASTER_SYSTEM = """你是长篇网文总策划。根据 Story Bible 与规模信息，生成可执行的总纲与分卷弧线。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
你必须为每卷自动推断叙事线程 threads（含 stages 与 milestones），不要省略。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

OUTLINE_MASTER_TEMPLATE = """<TASK>
生成总纲与分卷弧线，确保从开篇到终局有清晰递进，并覆盖全部章节范围。
</TASK>

<PROJECT>
《{project_name}》｜题材：{genre}
计划规模：共 {total_chapters} 章，{volume_count} 卷
</PROJECT>

<BIBLE_SUMMARY>
{bible_summary}
</BIBLE_SUMMARY>

<CURRENT_MASTER>
{current_master}
</CURRENT_MASTER>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "master": {{
    "acts": [
      {{
        "id": "act_1",
        "title": "幕标题",
        "summary": "本幕核心冲突与阶段目标",
        "chapter_range": [1, 100]
      }}
    ],
    "themes": ["主题1", "主题2"],
    "ending_goal": "全书终局目标（主角最终要达成什么）"
  }},
  "volumes": [
    {{
      "volume_id": "vol_01",
      "title": "第1卷标题",
      "chapter_range": [1, 30],
      "arcs": [{{"summary": "策划用卷弧线（可含剧透，不得直接注入开篇章节 beats）"}}],
      "arc_phases": [
        {{
          "tier": "opening",
          "chapter_range": [1, 5],
          "summary": "卷初日常与人设，感情线仅远观"
        }}
      ],
      "opening_focus": "卷初前若干章叙事焦点（日常/人设/违和，不含卷末关系 payoff）",
      "stage_goal": "本卷中后段阶段目标（非全书终局，不得拆成每章固定任务）",
      "threads": [
        {{
          "id": "main",
          "label": "主线",
          "priority_curve": "high_early",
          "milestones": [{{"id": "m1", "summary": "确认核心处境", "earliest_chapter": 1}}],
          "stages": [
            {{"level": 0, "id": "situation", "label": "处境确认", "ceiling": "仅确认处境"}},
            {{"level": 1, "id": "adaptation", "label": "适应调整", "ceiling": "允许适应环境"}},
            {{"level": 2, "id": "first_conflict", "label": "初冲突", "ceiling": "允许首次冲突"}}
          ]
        }},
        {{
          "id": "romance",
          "label": "感情线",
          "priority_curve": "low_early_high_mid",
          "milestones": [
            {{"id": "r1", "summary": "远观印象", "earliest_chapter": 1}},
            {{"id": "r2", "summary": "间接关联", "earliest_chapter": 8}},
            {{"id": "r3", "summary": "首次简短对话", "earliest_chapter": 15}}
          ],
          "stages": [
            {{"level": 0, "id": "unaware", "label": "无交集", "ceiling": "禁止男女主直接交流"}},
            {{"level": 1, "id": "distant_awareness", "label": "远观印象", "ceiling": "仅远观或侧面提及"}},
            {{"level": 2, "id": "indirect_link", "label": "间接关联", "ceiling": "允许间接关联"}}
          ]
        }},
        {{
          "id": "academic",
          "label": "学业线",
          "priority_curve": "steady",
          "milestones": [
            {{"id": "a1", "summary": "课堂小胜", "earliest_chapter": 6}},
            {{"id": "a2", "summary": "校内认可", "earliest_chapter": 18}}
          ],
          "stages": [
            {{"level": 0, "id": "baseline", "label": "学业基线", "ceiling": "仅展示成绩水平"}},
            {{"level": 1, "id": "small_win", "label": "小试牛刀", "ceiling": "允许小测验进步"}},
            {{"level": 2, "id": "recognition", "label": "校内认可", "ceiling": "允许校内认可"}}
          ]
        }},
        {{
          "id": "mystery",
          "label": "悬疑线",
          "priority_curve": "low_early_high_mid",
          "milestones": [
            {{"id": "y1", "summary": "违和细节", "earliest_chapter": 2}},
            {{"id": "y2", "summary": "可验证线索", "earliest_chapter": 12}}
          ],
          "stages": [
            {{"level": 0, "id": "unease", "label": "轻微违和", "ceiling": "仅违和与疑问"}},
            {{"level": 1, "id": "clue", "label": "线索浮现", "ceiling": "可埋线索不可揭底"}},
            {{"level": 2, "id": "pattern", "label": "规律成形", "ceiling": "允许局部规律"}}
          ]
        }}
      ],
      "allowed_knowledge": ["本卷允许逐步揭示的信息条目"],
      "opening_knowledge": ["卷初前若干章唯一允许出现的信息（日常/人设/轻微违和）"],
      "forbidden_reveals": ["本卷前期禁止揭示的谜底（含后续卷/终局关键词）"],
      "knowledge_ceiling": "本卷结束时读者最多知道什么",
      "foreshadowing_plants": [
        {{
          "hook": "伏笔名",
          "plant_hint": "如何暗示",
          "earliest_chapter": 5,
          "latest_chapter": 28
        }}
      ]
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>

<RULES>
- acts 的 chapter_range 并集应覆盖 1..{total_chapters}，不重叠、无缺口
- volumes 与 acts 在剧情上保持一致
- ending_goal 仅用于全书终局策划，不得写入早期卷 scope
- 每卷必须填写 opening_knowledge / forbidden_reveals，作为章节蓝图的硬边界
- 每卷必须填写 opening_focus / opening_knowledge / forbidden_reveals
- opening_focus 与 threads 用于慢热开篇：卷初不得把 stage_goal 拆成每章感情任务
- 每卷 threads 必须由 AI 根据 Story Bible 与题材自动推断，禁止留空
- threads 至少包含 main；并根据题材自动加入 romance / academic / mystery / villain 等
- 每条线程必须带完整 stages（≥3）与 milestones（≥2），milestone 章号落在本卷 chapter_range 内
- romance 若启用，priority_curve 应为 low_early_high_mid
- arc_phases 按章位阶分段，避免卷初泄露卷末弧线
</RULES>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""

OUTLINE_THREADS_SYSTEM = """你是叙事线程策划。根据设定与分卷目标，自动为各卷生成可执行的叙事线程。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

OUTLINE_THREADS_TEMPLATE = """<TASK>
为每个 volume_id 自动推断叙事线程，不要询问用户。
线程应覆盖本卷真正会推进的故事线。
</TASK>

<PROJECT>
《{project_name}》｜题材：{genre}
</PROJECT>

<BIBLE_SUMMARY>
{bible_summary}
</BIBLE_SUMMARY>

<VOLUMES_TO_FILL>
{volumes_json}
</VOLUMES_TO_FILL>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "volumes": [
    {{
      "volume_id": "vol_01",
      "opening_focus": "卷初焦点（日常/人设/违和）",
      "threads": [
        {{
          "id": "main",
          "label": "主线",
          "priority_curve": "high_early",
          "milestones": [
            {{"id": "m1", "summary": "确认处境", "earliest_chapter": 1}},
            {{"id": "m2", "summary": "初次冲突", "earliest_chapter": 10}}
          ],
          "stages": [
            {{"level": 0, "id": "situation", "label": "处境确认", "ceiling": "仅确认处境"}},
            {{"level": 1, "id": "adaptation", "label": "适应调整", "ceiling": "允许适应环境"}},
            {{"level": 2, "id": "first_conflict", "label": "初冲突", "ceiling": "允许首次冲突"}}
          ]
        }}
      ]
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>

<RULES>
- 必须为输入中的每个 volume_id 各生成一条
- 按题材自动选择线程：校园甜宠偏 romance+academic；悬疑偏 mystery；可自定义 villain 等
- priority_curve 只能是 high_early|low_early_high_mid|steady
- opening_focus 必填；里程碑章号必须落在该卷 chapter_range
- 卷初需要休眠的线用 low_early_high_mid
</RULES>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""

OUTLINE_CHAPTERS_SYSTEM = """你是章节蓝图编剧。为指定章节生成可执行的标题、节拍与约束。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
你必须遵守各章 chapter_mandate：主线程、休眠线程、各线程 thread_ceilings 优先级高于卷级策划目标。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

OUTLINE_CHAPTERS_TEMPLATE = """<TASK>
为指定章节生成蓝图（标题、节拍、约束）。
</TASK>

<PROJECT>
《{project_name}》｜题材：{genre}
</PROJECT>

<CHAPTER_MANDATES>
{chapter_mandates}
</CHAPTER_MANDATES>

<VOLUME_SCOPE>
{volume_scope}
</VOLUME_SCOPE>

<SCOPED_CONTEXT>
{scoped_context}
</SCOPED_CONTEXT>

<CHAPTER_IDS>
{chapter_ids}
</CHAPTER_IDS>

<SPOILER_GUARD>
{spoiler_guard}
</SPOILER_GUARD>

<NEIGHBOR_CONTEXT>
{neighbor_context}
</NEIGHBOR_CONTEXT>

<OUTPUT_FORMAT>
json
</OUTPUT_FORMAT>

<OUTPUT_JSON_SCHEMA>
{{
  "chapters": [
    {{
      "chapter_id": "ch_001",
      "title": "第1章：具体标题",
      "chapter_role": "setup|breather|bridge|escalation|payoff",
      "primary_thread": "main",
      "dormant_threads": ["romance", "mystery"],
      "beats": ["节拍1", "节拍2", "节拍3"],
      "constraints": ["软约束1（可被硬约束覆盖）"],
      "author_notes": "",
      "status": "ready"
    }}
  ]
}}
</OUTPUT_JSON_SCHEMA>

<RULES>
- 必须为每个请求的 chapter_id 各生成一条，并遵守该章 mandate
- beats 3-5 条；一章只推进 mandate.primary_thread，dormant_threads 不得推进
- 各线程推进须符合 thread_ceilings；休眠线程不得出现超出台阶的 payoff
- 不得把整卷 stage_goal 拆成每章固定任务
- forbidden_reveals 中的词义/概念不得以揭晓形式出现
- constraints 仅为软参考；硬约束由系统根据 mandate 注入，勿在 beats 中推进 dormant_threads
- constraints 若写伏笔，只写“埋设方式”，不写“揭示结果”
</RULES>

<OUTPUT_STRICT_RULES>
- 仅输出合法 JSON
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""

# 动态注入片段（由 spoiler.py 按章节位阶选择拼接）
NARRATIVE_GOAL_CURRENT_ACT = "当前幕目标（第{start}-{end}章）：{summary}"
NARRATIVE_GOAL_EARLY_STAGE = "当前阶段目标：{summary}"
NARRATIVE_GOAL_TOWARD_ENDING = "朝全书终局推进：{ending_goal}"
NARRATIVE_GOAL_DEFAULT = "推进当前卷主线，仅兑现已到 reveal 时机的伏笔"
NARRATIVE_GOAL_FALLBACK_SUMMARY = "完成开篇铺垫，建立人物与世界观"

SPOILER_GUARD_HEADER = "伏笔与剧透纪律："
SPOILER_GUARD_BASE_RULES = [
    "- beats 只写本章允许出现的信息；禁止提前揭晓后续幕/卷的谜底",
    "- constraints 若涉及伏笔，只能写“如何埋设/暗示”，禁止写“揭示/真相是/原来是”",
    "- 未登场的重要角色、组织、世界观真相不得在本章 beats 中直接登场或点破",
]
SPOILER_GUARD_OPENING_RULE = (
    "- 开篇前几章：以日常、悬念、违和感为主；"
    "禁止闪回完整前世被杀、金手指全面觉醒、反派真面目等大揭晓"
)
SPOILER_GUARD_EARLY_RULE = (
    "- 早期章节：仅可埋设线索（细节异常、未解疑问），"
    "不可兑现中后期伏笔的 payoff"
)
SPOILER_GUARD_THREAD_RULE = (
    "- 线程节奏：一章最多推进一个线程台阶；"
    "dormant_threads 中的线程禁止任何推进"
)
