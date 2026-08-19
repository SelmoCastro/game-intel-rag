import argparse
import os
from pathlib import Path

from app.build_sources import collect_build_sources
from app.collectors import collect_steam_documents, collect_steam_news
from app.llm import OpenRouterLLM
from app.organizer import OrganizerAgent
from app.store_factory import create_store


def _organizer() -> OrganizerAgent:
    llm = OpenRouterLLM() if os.getenv("OPENROUTER_API_KEY") else None
    return OrganizerAgent(llm)


def ingest_documents(documents, store) -> int:
    organizer = _organizer()
    inserted = 0
    for document in documents:
        inserted += int(store.upsert_raw(document, organizer))
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Game Intel RAG")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="Coleta e indexa a Season 10 de Hero Siege")
    sub.add_parser("ingest-all", help="Coleta Steam, wiki e sites de builds")
    ask = sub.add_parser("ask", help="Consulta a base local")
    ask.add_argument("question")
    args = parser.parse_args()

    store = create_store(Path("data/game_intel.sqlite3"))
    if args.command == "ingest":
        inserted = ingest_documents([collect_steam_news()], store)
        print(f"Fontes processadas: 1 | fontes atualizadas: {inserted}")
        print(f"Total indexado: {store.count()}")
        return

    if args.command == "ingest-all":
        documents = collect_steam_documents()
        documents.extend(collect_build_sources())
        inserted = ingest_documents(documents, store)
        print(f"Documentos coletados: {len(documents)} | fontes atualizadas: {inserted}")
        print(f"Total indexado: {store.count()}")
        return

    from app.answer import AnswerAgent
    from app.retriever import RetrievalService

    answer = AnswerAgent(RetrievalService(store)).answer(
        args.question,
        game="Hero Siege",
        season="Season 10",
    )
    print(answer.response)
    for source in answer.sources:
        print(f"Fonte: {source.url}")
    if answer.warning:
        print(f"Aviso: {answer.warning}")


if __name__ == "__main__":
    main()
