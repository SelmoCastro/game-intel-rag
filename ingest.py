from pathlib import Path

from app.collectors import collect_steam_news
from app.store import KnowledgeStore


def ingest_hero_siege(database: str | Path = "data/game_intel.sqlite3") -> int:
    store = KnowledgeStore(database)
    document = collect_steam_news()
    inserted = store.upsert_raw(document)
    return int(inserted)


if __name__ == "__main__":
    inserted = ingest_hero_siege()
    print(f"Documentos novos: {inserted}")
