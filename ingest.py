from pathlib import Path
import os

from app.collectors import collect_steam_news
from app.llm import OpenRouterLLM
from app.organizer import OrganizerAgent
from app.store_factory import create_store


def ingest_hero_siege(database: str | Path = "data/game_intel.sqlite3") -> int:
    store = create_store(database)
    document = collect_steam_news()
    llm = OpenRouterLLM() if os.getenv("OPENROUTER_API_KEY") else None
    inserted = store.upsert_raw(document, OrganizerAgent(llm))
    return int(inserted)


if __name__ == "__main__":
    inserted = ingest_hero_siege()
    print(f"Documentos novos: {inserted}")
