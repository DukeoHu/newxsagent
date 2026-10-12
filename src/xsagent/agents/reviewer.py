from xsagent.agents.prompts import DRIFT_SYSTEM, DRIFT_TEMPLATE, SYNC_SYSTEM, SYNC_TEMPLATE
from xsagent.domain.memory.patch_models import BiblePatch, RiskLevel
from xsagent.domain.quality.models import DriftReport, Finding, FindingType
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask
from xsagent.llm.parse import parse_llm_json


class ReviewerAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def sync_bible(self, chapter_id: str, content: str) -> BiblePatch:
        prompt = SYNC_TEMPLATE.format(chapter_id=chapter_id, content=content)
        raw = await self._llm.generate(
            LLMRequest(task=LLMTask.BIBLE_SYNC, system=SYNC_SYSTEM, prompt=prompt, json_mode=True)
        )
        data = parse_llm_json(raw)
        patch = BiblePatch.model_validate(data)
        patch.source_chapter = chapter_id
        return patch

    async def detect_drift(self, chapter_id: str, content: str, bible_summary: str) -> DriftReport:
        prompt = DRIFT_TEMPLATE.format(
            chapter_id=chapter_id, content=content, bible_summary=bible_summary
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.DRIFT_DETECT, system=DRIFT_SYSTEM, prompt=prompt, json_mode=True
            )
        )
        data = parse_llm_json(raw)
        findings: list[Finding] = []
        for item in data.get("findings", []):
            suggested = item.get("suggested_patch")
            patch = BiblePatch.model_validate(suggested) if suggested else None
            findings.append(
                Finding(
                    id=item.get("id", "finding"),
                    type=item.get("type", FindingType.TIMELINE),
                    severity=RiskLevel(item.get("severity", "low")),
                    description=item.get("description", ""),
                    suggested_patch=patch,
                )
            )
        return DriftReport(findings=findings)
