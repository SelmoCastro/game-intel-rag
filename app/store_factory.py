import os
from pathlib import Path

from dotenv import load_dotenv

from app.postgres_store import PostgresKnowledgeStore
from app.store import KnowledgeStore

load_dotenv()


def create_store(path: str | Path = "data/game_intel.sqlite3"):
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return PostgresKnowledgeStore(database_url)
    return KnowledgeStore(path)
