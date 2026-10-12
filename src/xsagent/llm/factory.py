from xsagent.core.config import Settings, get_settings
from xsagent.domain.llm_log.service import LLMLogService
from xsagent.llm.base import LLMProvider
from xsagent.llm.deepseek import DeepSeekProvider
from xsagent.llm.logging_provider import LoggingLLMProvider
from xsagent.llm.ollama import OllamaProvider
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore

_provider: LLMProvider | None = None


def _build_inner_provider(settings: Settings) -> LLMProvider:
    mode = settings.llm_mode.lower()
    if mode == "ollama":
        return OllamaProvider(settings)
    if mode == "deepseek":
        return DeepSeekProvider(settings)
    return SimulatorProvider()


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider
    s = settings or get_settings()
    inner = _build_inner_provider(s)
    store = ProjectStore(s.data_dir)
    _provider = LoggingLLMProvider(inner, LLMLogService(store), s)
    return _provider


def reset_llm_provider() -> None:
    global _provider
    _provider = None


def set_llm_provider(provider: LLMProvider) -> None:
    global _provider
    _provider = provider
