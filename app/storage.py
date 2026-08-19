from pathlib import Path

from app.models import GameDocument


def save_document(document: GameDocument, destination: Path) -> Path:
    """Salva o documento normalizado em JSON para inspeção e versionamento local."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        document.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return destination
