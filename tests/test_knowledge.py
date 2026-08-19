import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import app, get_agent
from app.models import GameDocument
from app.store import KnowledgeStore

URL = "https://example.com/hero-siege"


def _seed(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "test.sqlite3")
    store.upsert_raw(GameDocument(
        game="Hero Siege",
        season="Season 10",
        title="Ebontharn adds Act 9",
        content="Season 10 Ebontharn adds Act 9 and three new Uber Bosses.",
        source_url=URL,
        source_type="test",
    ))
    return store


def test_store_deduplicates(tmp_path):
    store = _seed(tmp_path)
    document = GameDocument(
        game="Hero Siege",
        season="Season 10",
        title="Ebontharn adds Act 9",
        content="Season 10 Ebontharn adds Act 9 and three new Uber Bosses.",
        source_url=URL,
        source_type="test",
    )
    assert store.count() == 1
    assert store.upsert_raw(document) is False
    assert store.count() == 1


def test_search_filters_season(tmp_path):
    store = _seed(tmp_path)
    results = store.search("Act 9", game="Hero Siege", season="Season 10")
    assert len(results) == 1
    assert results[0].title == "Ebontharn adds Act 9"


def test_api_health():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
