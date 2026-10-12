from typing import Any

from pydantic import BaseModel, Field


class ChapterSummary(BaseModel):
    id: str
    title: str
    word_count: int
    filename: str


class Chapter(BaseModel):
    id: str
    title: str
    content_md: str
    word_count: int
    filename: str


class ChapterCreate(BaseModel):
    id: str = Field(pattern=r"^ch_\d{3,}$")
    title: str | None = None
    content_md: str = ""


class ChapterUpdate(BaseModel):
    title: str | None = None
    content_md: str | None = None
