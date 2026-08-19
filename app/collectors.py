from __future__ import annotations

import re
import warnings

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
    if "season 10" in lowered or "ebontharn" in lowered:
        return DocumentCategory.SEASON
    if "patch notes" in lowered or "patch" in lowered:
        return DocumentCategory.PATCH
    return DocumentCategory.UNKNOWN


def _fetch(url: str, timeout: float) -> str:
    response = httpx.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; hero-siege-rag-bot/0.1)"},
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.text


def collect_steam_news(
    url: str = SEASON_10_URL,
    timeout: float = 20.0,
) -> GameDocument:
    """Coleta a notícia da Steam usando o feed RSS público.

    A página HTML da Steam pode entregar apenas o shell para clientes HTTP.
    O feed RSS contém o resumo textual publicado e é mais estável para ingestão.
    """
    del url  # Mantido na assinatura para preservar a API do primeiro protótipo.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(_fetch(STEAM_NEWS_FEED_URL, timeout), "html.parser")

    items = soup.find_all("item")
    item = next(
        (
            candidate
            for candidate in items
            if "season 10" in candidate.title.get_text(" ", strip=True).lower()
        ),
        None,
    )
    if item is None:
        raise LookupError("A Season 10 não foi encontrada no feed da Steam")

    title = item.title.get_text(" ", strip=True)
    content = _clean_text(item.description.decode_contents())
    if not content:
        raise ValueError("A notícia encontrada não possui descrição textual")

    return GameDocument(
        season="Season 10",
        category=_category_from_text(f"{title} {content}"),
        title=title,
        content=content,
        source_url=SEASON_10_URL,
        source_type="steam_official_news_rss",
    )
