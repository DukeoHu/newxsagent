from typing import Any

from pydantic import BaseModel, Field


class MasterOutline(BaseModel):
    acts: list[dict[str, Any]] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    ending_goal: str = ""
    completion: float = Field(default=0, ge=0, le=100)


class VolumeForeshadowingPlant(BaseModel):
    hook: str = ""
    plant_hint: str = ""
    earliest_chapter: int = 1
    latest_chapter: int = 9999


class VolumeOutline(BaseModel):
    volume_id: str
    title: str = ""
    arcs: list[dict[str, Any]] = Field(default_factory=list)
    arc_phases: list[dict[str, Any]] = Field(default_factory=list)
    chapter_range: list[int] = Field(default_factory=list)
    stage_goal: str = ""
    opening_focus: str = ""
    threads: list[dict[str, Any]] = Field(default_factory=list)
    allowed_knowledge: list[str] = Field(default_factory=list)
    opening_knowledge: list[str] = Field(default_factory=list)
    forbidden_reveals: list[str] = Field(default_factory=list)
    knowledge_ceiling: str = ""
    foreshadowing_plants: list[dict[str, Any]] = Field(default_factory=list)


class ChapterBlueprint(BaseModel):
    chapter_id: str
    title: str = ""
    beats: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    hard_constraints: dict[str, Any] = Field(default_factory=dict)
    author_notes: str = ""
    chapter_role: str = ""
    primary_thread: str = ""
    dormant_threads: list[str] = Field(default_factory=list)
    status: str = "pending"


class OutlineBundle(BaseModel):
    master: MasterOutline
    volumes: list[VolumeOutline]
    chapters: list[ChapterBlueprint]
    completion: float
