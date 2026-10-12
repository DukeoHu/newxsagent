import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from xsagent.agents.onboarding import OnboardingAgent
from xsagent.core.config import get_settings
from xsagent.domain.common.spoiler import strip_future_author_notes
from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.memory.service import BibleService
from xsagent.domain.onboarding.models import (
    OnboardingQuestionResponse,
    OnboardingSession,
    OnboardingSessionStatus,
    OnboardingTurn,
)
from xsagent.domain.project.service import ProjectService
from xsagent.llm.context import llm_call_context
from xsagent.storage.project_store import ProjectStore

ONBOARDING_OPENING_QUESTION = "你想讲述什么样的故事？可以先从整体结构说起。"
ONBOARDING_OPENING_HINT = "可以描述主线走向、分幕结构、开局与结局方向等。"


class OnboardingService:
    def __init__(
        self,
        store: ProjectStore,
        projects: ProjectService,
        bible: BibleService,
        agent: OnboardingAgent,
    ) -> None:
        self._store = store
        self._projects = projects
        self._bible = bible
        self._agent = agent

    def get_session(self, project_id: str) -> OnboardingSession | None:
        self._projects.get_project(project_id)
        path = self._session_path(project_id)
        if not path.exists():
            return None
        return OnboardingSession.model_validate(self._store.read_json(path))

    async def start_session(self, project_id: str) -> OnboardingQuestionResponse:
        project = self._projects.get_project(project_id)
        now = datetime.now(UTC).isoformat()
        session = OnboardingSession(
            session_id=uuid4().hex[:12],
            project_id=project_id,
            status=OnboardingSessionStatus.ACTIVE,
            started_at=now,
            updated_at=now,
            turns=[],
            context={"name": project.name, "genre": project.genre},
        )
        return await self._append_question(session)

    async def submit_answer(self, project_id: str, answer: str) -> OnboardingQuestionResponse:
        with llm_call_context(project_id=project_id):
            session = self._require_active_session(project_id)
            text = answer.strip()
            if not text:
                raise ValueError("回答不能为空")

            session.turns.append(OnboardingTurn(role="user", content=text))
            session.updated_at = datetime.now(UTC).isoformat()
            user_count = sum(1 for t in session.turns if t.role == "user")

            if user_count >= 6:
                session.status = OnboardingSessionStatus.READY
                self._save_session(session)
                return OnboardingQuestionResponse(
                    session=session,
                    ready_to_generate=True,
                    hint="已收集足够信息，可以生成设定草案。",
                )

            result = await self._agent.next_question(session)
            if result.get("ready_to_generate") and user_count >= 3:
                session.status = OnboardingSessionStatus.READY
                self._save_session(session)
                return OnboardingQuestionResponse(
                    session=session,
                    ready_to_generate=True,
                    hint=result.get("hint"),
                )

            question = (result.get("question") or "").strip()
            if not question:
                if user_count >= 3:
                    session.status = OnboardingSessionStatus.READY
                    self._save_session(session)
                    return OnboardingQuestionResponse(session=session, ready_to_generate=True)
                question = "请补充更多关于故事核心冲突与开篇方向的细节。"

            session.turns.append(
                OnboardingTurn(
                    role="assistant",
                    content=question,
                    question_id=result.get("question_id"),
                )
            )
            session.updated_at = datetime.now(UTC).isoformat()
            self._save_session(session)
            return OnboardingQuestionResponse(
                session=session,
                question=question,
                question_id=result.get("question_id"),
                hint=result.get("hint"),
            )

    async def generate_draft(self, project_id: str) -> dict:
        with llm_call_context(project_id=project_id):
            session = self.get_session(project_id)
            if session is None:
                raise ValueError("请先开始引导问答")
            if session.status not in {
                OnboardingSessionStatus.READY,
                OnboardingSessionStatus.ACTIVE,
            }:
                raise ValueError("引导会话状态无效")
            if not any(t.role == "user" for t in session.turns):
                raise ValueError("请至少回答一个问题后再生成草案")

            draft = await self._agent.generate_bible_draft(session)
            session.status = OnboardingSessionStatus.READY
            session.draft = draft
            session.updated_at = datetime.now(UTC).isoformat()
            self._save_session(session)
            return draft

    def current_llm_mode(self) -> str:
        return get_settings().llm_mode.lower()

    def generation_warning(self) -> str | None:
        if self.current_llm_mode() == "simulator":
            return (
                "当前处于 simulator 模式：引导草案来自固定样例，不会严格依据你的问答内容。"
                "建议切换到 deepseek/ollama 后重新生成。"
            )
        return None

    def apply_draft(self, project_id: str, bible: dict) -> None:
        session = self.get_session(project_id)
        if not isinstance(bible, dict) or not bible:
            raise ValueError("请至少选择一个设定分区再应用")
        enriched_bible = self._inject_onboarding_notes(bible, session)
        for section, data in enriched_bible.items():
            self._bible.put_section(project_id, section, data)
        self._projects.mark_onboarding_complete(project_id)
        if session:
            session.status = OnboardingSessionStatus.APPLIED
            session.updated_at = datetime.now(UTC).isoformat()
            self._save_session(session)

    def clear_draft(self, project_id: str) -> OnboardingSession:
        session = self._require_active_session(project_id)
        session.draft = None
        session.updated_at = datetime.now(UTC).isoformat()
        user_count = sum(1 for t in session.turns if t.role == "user")
        if user_count >= 3:
            session.status = OnboardingSessionStatus.READY
        self._save_session(session)
        return session

    async def _append_question(self, session: OnboardingSession) -> OnboardingQuestionResponse:
        session.turns.append(
            OnboardingTurn(
                role="assistant",
                content=ONBOARDING_OPENING_QUESTION,
                question_id="q_opening",
            )
        )
        session.updated_at = datetime.now(UTC).isoformat()
        self._save_session(session)
        return OnboardingQuestionResponse(
            session=session,
            question=ONBOARDING_OPENING_QUESTION,
            question_id="q_opening",
            hint=ONBOARDING_OPENING_HINT,
        )

    def _require_active_session(self, project_id: str) -> OnboardingSession:
        session = self.get_session(project_id)
        if session is None:
            raise ValueError("请先开始引导问答")
        if session.status == OnboardingSessionStatus.APPLIED:
            raise ValueError("引导已完成，如需重做请重新开始")
        return session

    def _session_path(self, project_id: str) -> Path:
        return self._store.project_path(project_id) / "onboarding" / "session.json"

    def _save_session(self, session: OnboardingSession) -> None:
        if not self._store.exists(session.project_id):
            raise ProjectNotFoundError(session.project_id)
        path = self._session_path(session.project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._store.write_json(path, session.model_dump())

    def _inject_onboarding_notes(
        self, bible: dict, session: OnboardingSession | None
    ) -> dict:
        enriched = dict(bible)
        if "notes" not in enriched:
            return enriched
        notes = enriched.get("notes", {})
        if not isinstance(notes, dict):
            notes = {}
        summary = self._build_onboarding_summary(session)
        if summary:
            existing_vault = str(notes.get("spoiler_vault", "")).strip()
            notes["spoiler_vault"] = (
                f"{existing_vault}\n\n{summary}".strip() if existing_vault else summary
            )

            public_summary = self._build_public_onboarding_summary(session)
            if public_summary:
                existing = str(notes.get("author_notes", "")).strip()
                prefix = "【引导问答提炼】\n"
                addon = f"{prefix}{public_summary}"
                notes["author_notes"] = f"{existing}\n\n{addon}".strip() if existing else addon
        notes.setdefault("style_notes", "")
        notes.setdefault("style_rules", [])
        notes.setdefault("spoiler_vault", "")
        notes.setdefault("locked_fields", [])
        if not isinstance(notes.get("style_rules"), list):
            notes["style_rules"] = []
        enriched["notes"] = notes
        return enriched

    def _build_onboarding_summary(self, session: OnboardingSession | None) -> str:
        if session is None:
            return ""
        answers = [t.content.strip() for t in session.turns if t.role == "user" and t.content.strip()]
        if not answers:
            return ""
        lines: list[str] = []
        for idx, text in enumerate(answers[:8], start=1):
            normalized = re.sub(r"\s+", " ", text)
            lines.append(f"{idx}. {normalized}")
        return "\n".join(lines)

    def _build_public_onboarding_summary(self, session: OnboardingSession | None) -> str:
        if session is None:
            return ""
        answers = [
            t.content.strip()
            for t in session.turns
            if t.role == "user" and t.content.strip()
        ]
        if not answers:
            return ""

        lines: list[str] = []
        for idx, text in enumerate(answers[:2], start=1):
            normalized = re.sub(r"\s+", " ", text)
            public = strip_future_author_notes(normalized, chapter_no=3)
            if public:
                lines.append(f"{idx}. {public}")
        return "\n".join(lines)
