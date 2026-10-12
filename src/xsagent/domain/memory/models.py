from typing import Any

from pydantic import BaseModel, Field


class BibleSectionData(BaseModel):
    """Story Bible 分区数据（结构因 section 而异，保留扩展字段）。"""

    locked_fields: list[str] = Field(default_factory=list)
    model_config = {"extra": "allow"}


class BibleSectionUpdate(BaseModel):
    data: dict[str, Any]


class BibleLockUpdate(BaseModel):
    locked_fields: list[str]


class CharacterEntry(BaseModel):
    id: str
    name: str
    role: str | None = None
    current_state: str | None = None
    traits: list[str] = Field(default_factory=list)
