import json
import re
from typing import Protocol

from app.models import DocumentCategory, GameDocument, OrganizedDocument


class StructuredLLM(Protocol):
    def complete_json(self, system: str, user: str) -> dict: ...


class OrganizerAgent:
    """Organiza documentos com LLM opcional e fallback determinístico."""

    def __init__(self, llm: StructuredLLM | None = None):
        self.llm = llm

    def organize(self, document: GameDocument) -> OrganizedDocument:
        if self.llm is not None:
            try:
                payload = self.llm.complete_json(
                    "Classifique o documento de jogo. Retorne JSON válido com summary, category, keywords, season e patch.",
                    document.content,
                )
                return OrganizedDocument(
                    source_document_id=document.document_id,
                    game=document.game,
                    season=payload.get("season") or document.season,
                    patch=payload.get("patch") or document.patch,
                    category=payload.get("category", document.category),
                    title=document.title,
                    summary=payload["summary"],
                    content=document.content,
                    keywords=payload.get("keywords", []),
                    source_url=document.source_url,
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                pass

        return self._fallback(document)

    @staticmethod
    def _fallback(document: GameDocument) -> OrganizedDocument:
        text = re.sub(r"\s+", " ", document.content).strip()
        summary = text[:360].rstrip(" .") + ("..." if len(text) > 360 else "")
        lowered = text.lower()
        category = document.category
        if category == DocumentCategory.UNKNOWN:
            if "boss" in lowered:
                category = DocumentCategory.BOSS
            elif "patch" in lowered:
                category = DocumentCategory.PATCH
            elif "season" in lowered or "ebontharn" in lowered:
                category = DocumentCategory.SEASON
        keywords = sorted({word.lower() for word in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]{3,}", text) if word.lower() in {
            "season", "ebontharn", "patch", "act", "boss", "inferno", "ether", "item", "classes", "abyssal"
        }})
        return OrganizedDocument(
            source_document_id=document.document_id,
            game=document.game,
            season=document.season,
            patch=document.patch,
            category=category,
            title=document.title,
            summary=summary,
            content=document.content,
            keywords=keywords,
            source_url=document.source_url,
        )
