SYNC_SYSTEM = """你是 Story Bible 编辑。
输入内容按 XML 标签分区；请严格按标签边界理解各段，不要跨标签混淆。
仅输出合法 JSON，不要 markdown 代码块，不要额外解释。"""

SYNC_TEMPLATE = """<TASK>
从新章节正文中提取增量事实，并输出 Bible Patch JSON。
</TASK>

<EXTRACT_TARGETS>
- 新增/变更人物状态
- 时间线事件
- 伏笔进展
- 世界观细节
- 各叙事线程进度（写入 plot.thread_ledgers）
</EXTRACT_TARGETS>

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
  "updates": [{{"section": "characters|plot|world|notes|timeline", "op": "set|append|merge", "path": "...", "value": ...}}],
  "risk_level": "low|medium|high",
  "explanation": "..."
}}
</OUTPUT_JSON_SCHEMA>

<PATH_RULES>
- path 使用点分路径；列表用数字下标，如 characters.0.current_state
- 也可用角色 id 定位，如 characters.char_lin_yuan.current_state
- 禁止用角色中文名当列表下标（错误示例：characters.林渊.current_state）
- 禁止在 section 根上新建以中文名为键的旁路对象；人物状态必须写回 characters 数组内的对应项
- 新增人物用 op=append、path=characters
- timeline 事件用 op=append、path=events（或该 section 内的事件列表字段）
</PATH_RULES>

<THREAD_LEDGER_RULES>
- thread_ledgers 为对象，键为线程 id（如 main / romance / academic / mystery）
- 每个线程状态含：progress_level（整数台阶）、current_stage、last_progress_chapter、history（可选）
- romance 线程可额外含 pair（两人角色 id 列表）
- 仅当本章确实推进了某线程时才提升该线程 progress_level；无推进则不更新
- 参考台阶：main 0处境 1适应 2初冲突 3升级 4兑现；romance 0无交集…5情感转折；
  academic 0基线 1小胜 2认可 3突破 4大成；mystery 0违和 1线索 2规律 3局部真相 4揭晓
- 兼容字段：若只更新感情线，也可写 plot.relationship_ledger（将自动映射到 romance 线程）
</THREAD_LEDGER_RULES>

<OUTPUT_STRICT_RULES>
- 仅输出可信事实，避免 hallucination
- 禁止 markdown 代码块
- 禁止输出 JSON 以外的任何文字
</OUTPUT_STRICT_RULES>"""
