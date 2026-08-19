from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class DocumentCategory(StrEnum):
    PATCH = "patch"
    SEASON = "season"
    BUILD = "build"
    CLASS = "class"
    ITEM = "item"
    GUIDE = "guide"
    UNKNOWN = "unknown"


class GameDocument(BaseModel):
    """Documento normalizado antes de entrar no banco vetorial."""

    game: str = "Hero Siege"
    season: str | None = None
    patch: str | None = None
    category: DocumentCategory = DocumentCategory.UNKNOWN
    title: str
    content: str = Field(min_length=1)
    source_url: HttpUrl
    source_type: str
    published_at: datetime | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def freshness_key(self) -> tuple[int, datetime]:
        """Permite priorizar documentos de temporada e data mais recentes."""
        return (1 if self.season == "Season 10" else 0, self.published_at or self.collected_at)
