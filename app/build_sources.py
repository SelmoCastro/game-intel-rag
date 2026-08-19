from dataclasses import dataclass
import re
from html import unescape

from bs4 import BeautifulSoup

from app.collectors import _clean_text, _fetch
from app.models import DocumentCategory, GameDocument


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    url: str
    source_type: str
    priority: int
    category: DocumentCategory


BUILD_SOURCES = (
    SourceDefinition(
        name="Hero Siege Wiki — White Mage",
        url="https://herosiege.wiki.gg/wiki/White_Mage",
        source_type="official_wiki",
        priority=90,
        category=DocumentCategory.CLASS,
    ),
    SourceDefinition(
        name="Graxy Guides — Hero Siege",
        url="https://www.graxyguides.com/herosiege",
        source_type="written_build_guide",
        priority=80,
        category=DocumentCategory.BUILD,
    ),
    SourceDefinition(
        name="Metaroad — Hero Siege",
        url="https://metaroad.gg/hero-siege",
        source_type="build_planner",
        priority=75,
        category=DocumentCategory.BUILD,
    ),
)


def collect_public_page(source: SourceDefinition, timeout: float = 20.0) -> GameDocument:
    html = _fetch(source.url, timeout)
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("title")
    title = title_node.get_text(" ", strip=True) if title_node else source.name
    content = _clean_text(unescape(html))
    if len(content) < 80:
        raise ValueError(f"Fonte com conteúdo insuficiente: {source.url}")
    season_match = re.search(r"Season\s+(\d+)", content, re.IGNORECASE)
    season = f"Season {season_match.group(1)}" if season_match else None
    return GameDocument(
        game="Hero Siege",
        season=season,
        category=source.category,
        title=title,
        content=content,
        source_url=source.url,
        source_type=source.source_type,
        source_priority=source.priority,
    )


def collect_build_sources(timeout: float = 20.0) -> list[GameDocument]:
    documents = []
    for source in BUILD_SOURCES:
        documents.append(collect_public_page(source, timeout))
    return documents
