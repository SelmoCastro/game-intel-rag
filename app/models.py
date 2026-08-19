from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DocumentCategory(StrEnum):
    PATCH = "patch"
    SEASON = "season"
    BUILD = "build"
    CLASS = "class"
    ITEM = "item"
    GUIDE = "guide"
    BOSS = "boss"
    UNKNOWN = "unknown"


class GameDocument(BaseModel):
    """Documento normalizado antes de entrar no banco de conhecimento."""

    game: str
    season: str | None = None
    patch: str | None = None
    category: DocumentCategory = DocumentCategory.UNKNOWN
    title: str
    content: str = Field(min_length=1)
    source_url: HttpUrl
    source_type: str
    source_priority: int = Field(default=50, ge=1, le=100)
    published_at: datetime | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("game", "title", "content")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("campo textual não pode ficar vazio")
        return value

    @property
    def game_slug(self) -> str:
        return self.game.lower().replace(" ", "-")

    @property
    def document_id(self) -> str:
        key = f"{self.source_url}|{self.title}|{self.content}"
        return sha256(key.encode("utf-8")).hexdigest()

    @property
    def content_hash(self) -> str:
        return sha256(self.content.encode("utf-8")).hexdigest()

    def freshness_key(self) -> tuple[int, int, datetime]:
        return (
            1 if self.season else 0,
            self.source_priority,
            self.published_at or self.collected_at,
        )


class OrganizedDocument(BaseModel):
    source_document_id: str
    game: str
    season: str | None = None
    patch: str | None = None
    category: DocumentCategory = DocumentCategory.UNKNOWN
    title: str
    summary: str
    content: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    source_url: HttpUrl


class AnswerSource(BaseModel):
    title: str
    url: HttpUrl
    game: str
    season: str | None = None
    category: DocumentCategory = DocumentCategory.UNKNOWN


class Answer(BaseModel):
    question: str
    response: str
    sources: list[AnswerSource] = Field(default_factory=list)
    confidence: str = "low"
    warning: str | None = None
