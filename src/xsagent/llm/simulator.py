import json
import re
from collections.abc import AsyncIterator
from pathlib import Path

from xsagent.agents.prompts.onboarding import (
    SIM_ONBOARDING_HINT,
    SIM_ONBOARDING_QUESTIONS,
    SIM_ONBOARDING_READY_HINT,
)
from xsagent.llm.base import LLMRequest, LLMTask

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class SimulatorProvider:
    """测试用 LLM，按 task 返回固定 fixture。"""

    async def generate(self, request: LLMRequest) -> str:
        if request.task == LLMTask.PROSE:
            return (_FIXTURE_DIR / "prose_chapter.md").read_text(encoding="utf-8")
        if request.task == LLMTask.BIBLE_SYNC:
            return (_FIXTURE_DIR / "bible_sync.json").read_text(encoding="utf-8")
        if request.task == LLMTask.DRIFT_DETECT:
            return (_FIXTURE_DIR / "drift_findings.json").read_text(encoding="utf-8")
        if request.task == LLMTask.FIX:
            return json.dumps({"updates": [], "risk_level": "low", "explanation": "无需修复"})
        if request.task == LLMTask.ONBOARDING_QUESTION:
            return self._onboarding_question(request.prompt)
        if request.task == LLMTask.ONBOARDING_GENERATE:
            return (_FIXTURE_DIR / "onboarding_draft.json").read_text(encoding="utf-8")
        if request.task == LLMTask.OUTLINE_MASTER:
            return (_FIXTURE_DIR / "outline_master.json").read_text(encoding="utf-8")
        if request.task == LLMTask.OUTLINE_THREADS:
            return self._outline_threads(request.prompt)
        if request.task == LLMTask.OUTLINE_CHAPTERS:
            return self._outline_chapters(request.prompt)
        if request.task == LLMTask.GOAL_VERIFY:
            return (_FIXTURE_DIR / "goal_verdict.json").read_text(encoding="utf-8")
        if request.task == LLMTask.CHECKPOINT:
            return (_FIXTURE_DIR / "checkpoint.json").read_text(encoding="utf-8")
        if request.task == LLMTask.EXPLORE:
            return self._explore_options(request.prompt)
        if request.task == LLMTask.JUDGE:
            return self._explore_judge(request.prompt)
        if request.task == LLMTask.DREAM:
            return json.dumps(
                {"compress_style_notes": "", "drop_note_keys": [], "summary": "无需整理"},
                ensure_ascii=False,
            )
        if request.task == LLMTask.DISTILL:
            return (_FIXTURE_DIR / "distill_rules.json").read_text(encoding="utf-8")
        return ""

    def _onboarding_question(self, prompt: str) -> str:
        turn_match = re.search(r"当前是第\s*(\d+)\s*轮提问", prompt)
        turn_index = int(turn_match.group(1)) if turn_match else 1
        user_answers = len(re.findall(r"^作者：", prompt, re.MULTILINE))
        ready = user_answers >= 3 and turn_index > 3
        if ready:
            return json.dumps(
                {
                    "ready_to_generate": True,
                    "question_id": f"q_{turn_index}",
                    "question": "",
                    "hint": SIM_ONBOARDING_READY_HINT,
                },
                ensure_ascii=False,
            )
        question = SIM_ONBOARDING_QUESTIONS[
            min(turn_index - 1, len(SIM_ONBOARDING_QUESTIONS) - 1)
        ]
        return json.dumps(
            {
                "ready_to_generate": False,
                "question_id": f"q_{turn_index}",
                "question": question,
                "hint": SIM_ONBOARDING_HINT,
            },
            ensure_ascii=False,
        )

    def _outline_chapters(self, prompt: str) -> str:
        ids = re.findall(r"ch_\d+", prompt)
        chapters = []
        for cid in ids:
            no = int(cid.split("_")[1])
            chapters.append(
                {
                    "chapter_id": cid,
                    "title": f"第{no}章：主线推进",
                    "beats": [
                        f"承接第{max(1, no - 1)}章结果，明确本章目标",
                        "引入新冲突或揭示关键信息",
                        "章末设置悬念，驱动下一章",
                    ],
                    "constraints": ["保持人物动机一致", "不破坏已锁定设定"],
                    "status": "ready",
                }
            )
        return json.dumps({"chapters": chapters}, ensure_ascii=False)

    def _outline_threads(self, prompt: str) -> str:
        template = json.loads(
            (_FIXTURE_DIR / "outline_threads.json").read_text(encoding="utf-8")
        )
        volume_ids = re.findall(r"vol_\d+", prompt)
        if not volume_ids:
            return json.dumps(template, ensure_ascii=False)
        sample = template["volumes"][0]
        volumes = []
        for volume_id in dict.fromkeys(volume_ids):
            item = json.loads(json.dumps(sample))
            item["volume_id"] = volume_id
            volumes.append(item)
        return json.dumps({"volumes": volumes}, ensure_ascii=False)

    def _explore_options(self, prompt: str) -> str:
        count_match = re.search(r"生成\s*(\d+)\s*个", prompt)
        count = int(count_match.group(1)) if count_match else 3
        chapter_match = re.search(r"ch_\d+", prompt)
        chapter_id = chapter_match.group(0) if chapter_match else "ch_001"
        options = []
        variants = ["日常违和", "线索加码", "人物抉择"]
        for i in range(count):
            options.append(
                {
                    "option_id": f"opt_{i + 1}",
                    "title": f"方案 {i + 1}：{variants[i % 3]}",
                    "summary": f"以「{variants[i % 3]}」推进 {chapter_id}，与其他方案切口不同。",
                    "beats": [
                        f"承接上一章，从{variants[i % 3]}切入",
                        "中段升级冲突并给出人物选择",
                        "章末留下可续写钩子",
                    ],
                    "constraints": ["不破坏已锁定设定", "不推进休眠线程"],
                    "risk_level": ["low", "medium", "high"][min(i, 2)],
                }
            )
        return json.dumps({"options": options}, ensure_ascii=False)

    def _explore_judge(self, prompt: str) -> str:
        ids = re.findall(r"opt_[a-zA-Z0-9]+", prompt)
        winner = ids[0] if ids else "opt_1"
        return json.dumps(
            {"winner_option_id": winner, "reason": "该方案约束最紧、推进最稳"},
            ensure_ascii=False,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        text = await self.generate(request)
        chunk_size = 32
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
