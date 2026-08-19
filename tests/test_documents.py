from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.collectors import _category_from_text, _clean_text
from app.models import DocumentCategory, GameDocument


URL = "https://store.steampowered.com/news/app/269210/view/461208205952813643"


def test_document_requires_content():
    with pytest.raises(ValidationError):
        GameDocument(title="sem conteúdo", content="", source_url=URL, source_type="test")


def test_document_requires_explicit_game():
    document = GameDocument(
        game="Hero Siege",
        title="Season 10",
        content="Ebontharn",
        source_url=URL,
        source_type="steam_official_news",
    )

    assert document.game == "Hero Siege"
    assert document.category == DocumentCategory.UNKNOWN
    assert document.collected_at.tzinfo is not None


def test_season_category_is_detected():
    assert _category_from_text("Ebontharn Season 10") == DocumentCategory.SEASON


def test_html_is_cleaned():
    result = _clean_text("<script>bad()</script><h1>Patch notes</h1><p>Act 9</p>")
    assert result == "Patch notes Act 9"
    assert "bad" not in result
