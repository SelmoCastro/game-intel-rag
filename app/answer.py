import re

from app.models import Answer
from app.retriever import RetrievalService


class AnswerAgent:
    def __init__(self, retriever: RetrievalService):
        self.retriever = retriever

    def answer(self, question: str, game: str | None = None, season: str | None = None) -> Answer:
        documents = self.retriever.retrieve(question, game=game, season=season)
        if not documents:
            return Answer(
                question=question,
                response="Não encontrei informação suficiente na base para responder com segurança.",
                confidence="low",
                warning="Tente informar o jogo, a temporada ou uma classe específica.",
            )

        excerpts = []
        for document in documents[:3]:
            excerpts.append(f"{document.title}: {document.summary}")
        response = "Com base nas fontes indexadas:\n\n" + "\n".join(f"- {item}" for item in excerpts)
        return Answer(
            question=question,
            response=response,
            sources=self.retriever.sources(documents[:3]),
            confidence="medium" if len(documents) > 1 else "low",
            warning="Esta é a recuperação local inicial; a geração por LLM será adicionada na próxima camada.",
        )
