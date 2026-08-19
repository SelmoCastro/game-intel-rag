import sqlite3
from pathlib import Path

from app.models import DocumentCategory, GameDocument, OrganizedDocument


class KnowledgeStore:
    def __init__(self, path: str | Path = "data/game_intel.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    game TEXT NOT NULL,
                    season TEXT,
                    patch TEXT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    content TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_document_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def upsert_raw(self, document: GameDocument) -> bool:
        from app.organizer import OrganizerAgent
        return self.upsert(OrganizerAgent().organize(document))

    def upsert(self, document: OrganizedDocument) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT OR IGNORE INTO documents
                (document_id, game, season, patch, category, title, summary,
                 content, keywords, source_url, source_document_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.source_document_id,
                    document.game,
                    document.season,
                    document.patch,
                    document.category.value,
                    document.title,
                    document.summary,
                    document.content,
                    ",".join(document.keywords),
                    str(document.source_url),
                    document.source_document_id,
                ),
            )
            return cursor.rowcount == 1

    def count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])

    def search(self, query: str, game: str | None = None, season: str | None = None, limit: int = 5) -> list[OrganizedDocument]:
        params: list[str] = []
        clauses = []
        if game:
            clauses.append("game = ?")
            params.append(game)
        if season:
            clauses.append("season = ?")
            params.append(season)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as db:
            rows = db.execute(f"SELECT * FROM documents {where}", params).fetchall()
        terms = {term.lower() for term in query.split() if len(term) > 2}
        ranked = []
        for row in rows:
            haystack = f"{row['title']} {row['summary']} {row['content']} {row['keywords']}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                ranked.append((score, row))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [self._row_to_document(row) for _, row in ranked[:limit]]

    @staticmethod
    def _row_to_document(row: sqlite3.Row) -> OrganizedDocument:
        return OrganizedDocument(
            source_document_id=row["source_document_id"],
            game=row["game"],
            season=row["season"],
            patch=row["patch"],
            category=DocumentCategory(row["category"]),
            title=row["title"],
            summary=row["summary"],
            content=row["content"],
            keywords=[item for item in row["keywords"].split(",") if item],
            source_url=row["source_url"],
        )
