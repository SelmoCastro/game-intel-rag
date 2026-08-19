from app.build_sources import SourceDefinition, collect_public_page
from app.models import DocumentCategory


def test_public_page_source_is_classified(monkeypatch):
    monkeypatch.setattr(
        "app.build_sources._fetch",
        lambda url, timeout: "<html><title>Build S10</title><body>Season 10 White Mage skills and build details " + "x" * 100 + "</body></html>",
    )
    document = collect_public_page(SourceDefinition(
        name="test",
        url="https://example.com/build",
        source_type="written_build_guide",
        priority=80,
        category=DocumentCategory.BUILD,
    ))
    assert document.game == "Hero Siege"
    assert document.season == "Season 10"
    assert document.category == DocumentCategory.BUILD
    assert document.source_priority == 80
