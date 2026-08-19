from functools import lru_cache
import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.answer import AnswerAgent
from app.llm import OpenRouterLLM
from app.retriever import RetrievalService
from app.store import KnowledgeStore

app = FastAPI(title="Game Intel RAG", version="0.1.0")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    game: str | None = None
    season: str | None = None


@lru_cache
def get_agent() -> AnswerAgent:
    store = KnowledgeStore(Path("data/game_intel.sqlite3"))
    llm = OpenRouterLLM() if os.getenv("OPENROUTER_API_KEY") else None
    return AnswerAgent(RetrievalService(store), llm=llm)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest):
    return get_agent().answer(request.question, request.game, request.season)
