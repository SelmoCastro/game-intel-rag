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

    def organize_many(self, document: GameDocument, max_chars: int = 900) -> list[OrganizedDocument]:
        """Divide uma fonte longa em chunks preservando linhas/seções."""
        lines = [line.strip() for line in document.content.splitlines() if line.strip()]
        chunks: list[str] = []
        current: list[str] = []
        size = 0
        for line in lines:
            if current and size + len(line) + 1 > max_chars:
                chunks.append("\n".join(current))
                current, size = [], 0
            current.append(line)
            size += len(line) + 1
        if current:
            chunks.append("\n".join(current))
        if not chunks:
            return [self.organize(document)]
        if len(chunks) == 1:
            return [self.organize(document)]

        organized: list[OrganizedDocument] = []
        for index, chunk in enumerate(chunks, start=1):
            chunk_document = document.model_copy(update={
                "title": f"{document.title} — seção {index}",
                "content": chunk,
            })
            organized.append(self.organize(chunk_document))
        return organized

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
