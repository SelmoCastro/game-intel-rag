import argparse
from pathlib import Path

from app.answer import AnswerAgent
from app.collectors import collect_steam_news
from app.retriever import RetrievalService
from app.store_factory import create_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Game Intel RAG")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="Coleta e indexa Hero Siege Season 10")
    ask = sub.add_parser("ask", help="Consulta a base local")
    ask.add_argument("question")
    args = parser.parse_args()

    store = create_store(Path("data/game_intel.sqlite3"))
    if args.command == "ingest":
        document = collect_steam_news()
        print(f"Documento novo: {store.upsert_raw(document)}")
        print(f"Total indexado: {store.count()}")
        return

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
