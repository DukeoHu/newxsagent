import pytest

from xsagent.core.config import Settings
from xsagent.domain.llm_log.service import LLMLogService
from xsagent.llm.base import LLMRequest, LLMTask
from xsagent.llm.context import llm_call_context
from xsagent.llm.logging_provider import LoggingLLMProvider
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def log_service(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    return LLMLogService(store), store


@pytest.fixture
def logging_provider(log_service, tmp_path):
    service, store = log_service
    settings = Settings(data_dir=tmp_path / "projects", llm_mode="simulator")
    return LoggingLLMProvider(SimulatorProvider(), service, settings), store


@pytest.mark.asyncio
async def test_logging_provider_records_generate(logging_provider):
    provider, store = logging_provider
    project_id = "proj001"
    (store.project_path(project_id) / "logs").mkdir(parents=True, exist_ok=True)
    (store.project_path(project_id) / "xsagent.json").write_text(
        '{"id":"proj001","name":"测试"}', encoding="utf-8"
    )

    request = LLMRequest(
        task=LLMTask.BIBLE_SYNC,
        system="sync system",
        prompt="sync prompt",
        json_mode=True,
    )
    with llm_call_context(project_id=project_id):
        response = await provider.generate(request)

    assert response
    entries = provider._log_service.list_entries(project_id)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.task == "bible_sync"
    assert entry.system == "sync system"
    assert entry.prompt == "sync prompt"
    assert entry.json_mode is True
    assert entry.status == "ok"
    assert entry.response
    assert entry.llm_mode == "simulator"
    assert entry.model == "simulator"


@pytest.mark.asyncio
async def test_logging_provider_records_stream(logging_provider):
    provider, store = logging_provider
    project_id = "proj002"
    (store.project_path(project_id) / "logs").mkdir(parents=True, exist_ok=True)
    (store.project_path(project_id) / "xsagent.json").write_text(
        '{"id":"proj002","name":"测试"}', encoding="utf-8"
    )

    request = LLMRequest(task=LLMTask.PROSE, system="prose system", prompt="prose prompt")
    chunks: list[str] = []
    with llm_call_context(project_id=project_id, job_id="job123"):
        async for chunk in provider.stream(request):
            chunks.append(chunk)

    assert chunks
    entries = provider._log_service.list_entries(project_id)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.task == "prose"
    assert entry.job_id == "job123"
    assert entry.status == "ok"
    assert entry.response == "".join(chunks)


@pytest.mark.asyncio
async def test_logging_provider_skips_without_project_context(logging_provider):
    provider, _store = logging_provider
    request = LLMRequest(task=LLMTask.PROSE, prompt="no context")
    await provider.generate(request)

    assert provider._log_service.list_entries("any") == []


@pytest.mark.asyncio
async def test_logging_provider_truncates_large_payload(log_service, tmp_path):
    service, store = log_service
    settings = Settings(
        data_dir=tmp_path / "projects",
        llm_mode="simulator",
        llm_log_max_chars=20,
    )
    provider = LoggingLLMProvider(SimulatorProvider(), service, settings)
    project_id = "proj003"
    (store.project_path(project_id) / "logs").mkdir(parents=True, exist_ok=True)
    (store.project_path(project_id) / "xsagent.json").write_text(
        '{"id":"proj003","name":"测试"}', encoding="utf-8"
    )

    request = LLMRequest(
        task=LLMTask.BIBLE_SYNC,
        system="x" * 100,
        prompt="y" * 100,
        json_mode=True,
    )
    with llm_call_context(project_id=project_id):
        await provider.generate(request)

    entry = service.list_entries(project_id)[0]
    assert entry.prompt_truncated is True
    assert entry.system_truncated is True
    assert entry.response_truncated is True
    assert "…[truncated]" in entry.prompt
