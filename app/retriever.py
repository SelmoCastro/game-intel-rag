from app.models import AnswerSource, OrganizedDocument
from app.store import KnowledgeStore


class RetrievalService:
    def __init__(self, store: KnowledgeStore):
        self.store = store

    def retrieve(self, question: str, game: str | None = None, season: str | None = None, limit: int = 5) -> list[OrganizedDocument]:
        return self.store.search(question, game=game, season=season, limit=limit)

    @staticmethod
    def sources(documents: list[OrganizedDocument]) -> list[AnswerSource]:
        return [
            AnswerSource(
                title=document.title,
                url=document.source_url,
                game=document.game,
                season=document.season,
                category=document.category,
            )
            for document in documents
        ]
