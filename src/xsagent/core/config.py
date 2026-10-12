import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _config_path() -> Path:
    custom = os.environ.get("XSAGENT_CONFIG_PATH")
    if custom:
        return Path(custom)
    return _repo_root() / "config.yaml"


def _load_yaml_config() -> dict[str, Any]:
    config_path = _config_path()
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="XSAGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=Path("./data/projects"))
    debug: bool = False
    log_level: str = Field(default="info")

    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000)
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen2.5:14b")
    llm_mode: str = Field(default="simulator")
    llm_log_enabled: bool = Field(default=True)
    llm_log_max_chars: int = Field(default=32000)
    ollama_think: bool = Field(default=False)
    strip_think_tags: bool = Field(default=True)
    deepseek_base_url: str = Field(default="https://api.deepseek.com")
    deepseek_api_key: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-v4-pro")
    deepseek_reasoning_effort: str = Field(default="high")
    deepseek_thinking_enabled: bool = Field(default=True)

    @property
    def repo_root(self) -> Path:
        return _repo_root()

    @property
    def template_dir(self) -> Path:
        return self.repo_root / "templates" / "default"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        yaml_config = _load_yaml_config()
        server = yaml_config.get("server", {})
        llm = yaml_config.get("llm", {})
        logging = yaml_config.get("logging", {})
        env = os.environ
        use_env = lambda key: key in env and env.get(key) not in (None, "")
        _settings = Settings(
            log_level=env.get("XSAGENT_LOG_LEVEL")
            if use_env("XSAGENT_LOG_LEVEL")
            else logging.get("level", "info"),
            server_host=env.get("XSAGENT_SERVER_HOST")
            if use_env("XSAGENT_SERVER_HOST")
            else server.get("host", "0.0.0.0"),
            server_port=int(env.get("XSAGENT_SERVER_PORT"))
            if use_env("XSAGENT_SERVER_PORT")
            else server.get("port", 8000),
            cors_origins=server.get("cors_origins", ["http://localhost:5173", "http://127.0.0.1:5173"]),
            ollama_base_url=env.get("XSAGENT_OLLAMA_BASE_URL")
            if use_env("XSAGENT_OLLAMA_BASE_URL")
            else llm.get("ollama_base_url", "http://localhost:11434"),
            ollama_model=env.get("XSAGENT_OLLAMA_MODEL")
            if use_env("XSAGENT_OLLAMA_MODEL")
            else llm.get("ollama_model", "qwen2.5:14b"),
            llm_mode=env.get("XSAGENT_LLM_MODE")
            if use_env("XSAGENT_LLM_MODE")
            else llm.get("mode", "simulator"),
            llm_log_enabled=(env.get("XSAGENT_LLM_LOG_ENABLED", "").lower() not in {"0", "false", "no", "off"})
            if use_env("XSAGENT_LLM_LOG_ENABLED")
            else llm.get("llm_log_enabled", True),
            llm_log_max_chars=int(env.get("XSAGENT_LLM_LOG_MAX_CHARS"))
            if use_env("XSAGENT_LLM_LOG_MAX_CHARS")
            else llm.get("llm_log_max_chars", 32000),
            ollama_think=(env.get("XSAGENT_OLLAMA_THINK", "").lower() in {"1", "true", "yes", "on"})
            if use_env("XSAGENT_OLLAMA_THINK")
            else llm.get("ollama_think", False),
            strip_think_tags=(env.get("XSAGENT_STRIP_THINK_TAGS", "").lower() in {"1", "true", "yes", "on"})
            if use_env("XSAGENT_STRIP_THINK_TAGS")
            else llm.get("strip_think_tags", True),
            deepseek_base_url=env.get("XSAGENT_DEEPSEEK_BASE_URL")
            if use_env("XSAGENT_DEEPSEEK_BASE_URL")
            else llm.get("deepseek_base_url", "https://api.deepseek.com"),
            deepseek_api_key=env.get("XSAGENT_DEEPSEEK_API_KEY")
            if use_env("XSAGENT_DEEPSEEK_API_KEY")
            else llm.get("deepseek_api_key", ""),
            deepseek_model=env.get("XSAGENT_DEEPSEEK_MODEL")
            if use_env("XSAGENT_DEEPSEEK_MODEL")
            else llm.get("deepseek_model", "deepseek-v4-pro"),
            deepseek_reasoning_effort=env.get("XSAGENT_DEEPSEEK_REASONING_EFFORT")
            if use_env("XSAGENT_DEEPSEEK_REASONING_EFFORT")
            else llm.get("deepseek_reasoning_effort", "high"),
            deepseek_thinking_enabled=(
                env.get("XSAGENT_DEEPSEEK_THINKING_ENABLED", "").lower() in {"1", "true", "yes", "on"}
            )
            if use_env("XSAGENT_DEEPSEEK_THINKING_ENABLED")
            else llm.get("deepseek_thinking_enabled", True),
        )
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
    return _settings


def reset_settings() -> None:
    """Reset cached settings (for tests)."""
    global _settings
    _settings = None


def get_llm_runtime_config() -> dict[str, Any]:
    settings = get_settings()
    return {
        "mode": settings.llm_mode,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "ollama_think": settings.ollama_think,
        "strip_think_tags": settings.strip_think_tags,
        "deepseek_base_url": settings.deepseek_base_url,
        "deepseek_api_key": settings.deepseek_api_key,
        "deepseek_model": settings.deepseek_model,
        "deepseek_reasoning_effort": settings.deepseek_reasoning_effort,
        "deepseek_thinking_enabled": settings.deepseek_thinking_enabled,
    }


def update_llm_runtime_config(payload: dict[str, Any]) -> dict[str, Any]:
    config_path = _config_path()
    config = _load_yaml_config()
    llm = dict(config.get("llm", {}))
    llm.update(
        {
            "mode": payload.get("mode", llm.get("mode", "simulator")),
            "ollama_base_url": payload.get(
                "ollama_base_url", llm.get("ollama_base_url", "http://localhost:11434")
            ),
            "ollama_model": payload.get("ollama_model", llm.get("ollama_model", "qwen2.5:14b")),
            "ollama_think": bool(payload.get("ollama_think", llm.get("ollama_think", False))),
            "strip_think_tags": bool(
                payload.get("strip_think_tags", llm.get("strip_think_tags", True))
            ),
            "deepseek_base_url": payload.get(
                "deepseek_base_url", llm.get("deepseek_base_url", "https://api.deepseek.com")
            ),
            "deepseek_api_key": payload.get("deepseek_api_key", llm.get("deepseek_api_key", "")),
            "deepseek_model": payload.get(
                "deepseek_model", llm.get("deepseek_model", "deepseek-v4-pro")
            ),
            "deepseek_reasoning_effort": payload.get(
                "deepseek_reasoning_effort", llm.get("deepseek_reasoning_effort", "high")
            ),
            "deepseek_thinking_enabled": bool(
                payload.get(
                    "deepseek_thinking_enabled", llm.get("deepseek_thinking_enabled", True)
                )
            ),
        }
    )
    config["llm"] = llm
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    reset_settings()
    from xsagent.llm.factory import reset_llm_provider

    reset_llm_provider()
    return get_llm_runtime_config()
