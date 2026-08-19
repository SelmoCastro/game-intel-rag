from __future__ import annotations

import re
import warnings
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape

import httpx
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from app.models import DocumentCategory, GameDocument

STEAM_NEWS_FEED_URL = "https://store.steampowered.com/feeds/news/app/269210/"
SEASON_10_URL = "https://store.steampowered.com/news/app/269210/view/461208205952813643"


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()
    return " ".join(soup.get_text(" ").split())


def _category_from_text(text: str) -> DocumentCategory:
    lowered = text.lower()
    if "season" in lowered or "ebontharn" in lowered:
        return DocumentCategory.SEASON
    if "patch notes" in lowered or "patch" in lowered:
        return DocumentCategory.PATCH
    if "boss" in lowered:
        return DocumentCategory.BOSS
    return DocumentCategory.UNKNOWN


def _fetch(url: str, timeout: float) -> str:
    response = httpx.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; game-intel-rag/0.1)"},
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.text


def _parse_item(item) -> GameDocument:
    title_node = item.find("title")
    description_node = item.find("description")
    guid_node = item.find("guid")
    pubdate_node = item.find("pubdate")
    if title_node is None or description_node is None or guid_node is None:
        raise ValueError("Item RSS sem título, descrição ou URL")

    title = title_node.get_text(" ", strip=True)
    content = _clean_text(unescape(description_node.decode_contents()))
    if not content:
        raise ValueError("A notícia encontrada não possui descrição textual")

    published_at: datetime | None = None
    if pubdate_node is not None:
        try:
            published_at = parsedate_to_datetime(pubdate_node.get_text(strip=True))
        except (TypeError, ValueError):
            published_at = None

    combined = f"{title} {content}"
    season_match = re.search(r"Season\s+(\d+)", combined, re.IGNORECASE)
    season = f"Season {season_match.group(1)}" if season_match else None
    return GameDocument(
        game="Hero Siege",
        season=season,
        category=_category_from_text(combined),
        title=title,
        content=content,
        source_url=guid_node.get_text(strip=True),
        source_type="steam_official_news_rss",
        source_priority=100,
        published_at=published_at,
    )


def collect_steam_documents(timeout: float = 20.0) -> list[GameDocument]:
    """Coleta todas as notícias disponíveis no feed RSS oficial."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(_fetch(STEAM_NEWS_FEED_URL, timeout), "html.parser")
    return [_parse_item(item) for item in soup.find_all("item")]


def collect_steam_news(
    url: str = SEASON_10_URL,
    timeout: float = 20.0,
) -> GameDocument:
    """Mantém o helper da Season 10 sobre o coletor genérico do feed."""
    del url
    documents = collect_steam_documents(timeout)
    for document in documents:
        if str(document.source_url) == SEASON_10_URL:
            return document
    raise LookupError("A Season 10 não foi encontrada no feed da Steam")
