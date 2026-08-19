from app.models import GameDocument


def is_duplicate(left: GameDocument, right: GameDocument) -> bool:
    return left.document_id == right.document_id or left.content_hash == right.content_hash
