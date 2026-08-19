from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.answer import AnswerAgent
from app.api import AskRequest
from app.retriever import RetrievalService
from app.store import KnowledgeStore


def test_answer_without_evidence_is_explicit(tmp_path: Path):
    agent = AnswerAgent(RetrievalService(KnowledgeStore(tmp_path / "empty.sqlite3")))
    answer = agent.answer("Qual é a build?", game="Hero Siege", season="Season 10")
    assert answer.confidence == "low"
    assert "Não encontrei" in answer.response
    assert answer.sources == []


def test_ask_request_validates_length():
    try:
        AskRequest(question="x")
    except ValueError:
        return
    raise AssertionError("pergunta curta deveria ser rejeitada")
