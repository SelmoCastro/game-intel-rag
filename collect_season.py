from pathlib import Path

from app.collectors import SEASON_10_URL, collect_steam_news
from app.storage import save_document


if __name__ == "__main__":
    document = collect_steam_news(SEASON_10_URL)
    output = save_document(
        document,
        Path("data/raw/hero-siege-season-10-steam.json"),
    )
    print(f"Documento salvo em: {output}")
    print(f"Categoria: {document.category.value}")
    print(f"Temporada: {document.season}")
    print(f"Caracteres coletados: {len(document.content)}")
