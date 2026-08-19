import re
from typing import Protocol

from app.models import Answer
from app.retriever import RetrievalService


class TextLLM(Protocol):
    def complete_text(self, system: str, user: str) -> str: ...


class AnswerAgent:
    def __init__(self, retriever: RetrievalService, llm: TextLLM | None = None):
        self.retriever = retriever
        self.llm = llm

    def answer(self, question: str, game: str | None = None, season: str | None = None) -> Answer:
        documents = self.retriever.retrieve(question, game=game, season=season)
        if not documents:
            return Answer(
                question=question,
                response="Não encontrei informação suficiente na base para responder com segurança.",
                confidence="low",
                warning="Tente informar o jogo, a temporada ou uma classe específica.",
            )

        context = "\n\n".join(
            f"[{index}] {document.title}\n{document.content[:1800]}\nFonte: {document.source_url}"
            for index, document in enumerate(documents[:5], start=1)
        )
        if self.llm is not None:
            try:
                response = self.llm.complete_text(
                    "Responda em português usando somente o CONTEXTO. Se ele não bastar, diga que não há evidência. Cite as fontes pelo número entre colchetes.",
                    f"PERGUNTA:\n{question}\n\nCONTEXTO:\n{context}",
                ).strip()
                if response:
                    return Answer(
                        question=question,
                        response=response,
                        sources=self.retriever.sources(documents[:5]),
                        confidence="high" if len(documents) > 1 else "medium",
                    )
            except Exception:
                pass

        excerpts = []
        for document in documents[:3]:
            clean_summary = re.sub(r"\s+", " ", document.summary).strip()
            excerpts.append(f"{document.title}: {clean_summary}")
        response = "Com base nas fontes indexadas:\n\n" + "\n".join(f"- {item}" for item in excerpts)
        return Answer(
            question=question,
            response=response,
            sources=self.retriever.sources(documents[:3]),
            confidence="medium" if len(documents) > 1 else "low",
            warning="Resposta usando recuperação local; configure OPENROUTER_API_KEY para ativar geração contextual.",
        )
