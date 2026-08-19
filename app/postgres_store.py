from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import psycopg

from app.embeddings import EMBEDDING_DIMENSIONS, EmbeddingService
from app.models import DocumentCategory, GameDocument, OrganizedDocument


class PostgresKnowledgeStore:
    def __init__(self, database_url: str, embeddings: EmbeddingService | None = None):
        self.database_url = database_url
        self.embeddings = embeddings or EmbeddingService()
        self._init_db()

    def _connect(self):
        return psycopg.connect(self.database_url)

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("CREATE EXTENSION IF NOT EXISTS vector")
            db.execute(f"""
                CREATE TABLE IF NOT EXISTS game_documents (
                    document_id TEXT PRIMARY KEY,
                    game TEXT NOT NULL,
                    season TEXT,
                    patch TEXT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    content TEXT NOT NULL,
                    keywords TEXT[] NOT NULL DEFAULT '{{}}',
                    source_url TEXT NOT NULL,
                    source_document_id TEXT NOT NULL,
                    embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS game_documents_game_season_idx ON game_documents (game, season)")
            db.commit()

    def upsert_raw(self, document: GameDocument, organizer=None) -> bool:
        from app.organizer import OrganizerAgent
        documents = (organizer or OrganizerAgent()).organize_many(document)
        with self._connect() as db:
            db.execute("DELETE FROM game_documents WHERE source_url = %s", (str(document.source_url),))
            db.commit()
        return self.upsert_many(documents) > 0

    def upsert_many(self, documents: list[OrganizedDocument]) -> int:
        return sum(self.upsert(document) for document in documents)

    def upsert(self, document: OrganizedDocument) -> bool:
        embedding = self.embeddings.as_pgvector(
            self.embeddings.embed(f"{document.title}\n{document.summary}\n{document.content}")
        )
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO game_documents
                (document_id, game, season, patch, category, title, summary,
                 content, keywords, source_url, source_document_id, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (document_id) DO NOTHING
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
                    document.keywords,
                    str(document.source_url),
                    document.source_document_id,
                    embedding,
                ),
            )
            db.commit()
            return cursor.rowcount == 1

    def count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM game_documents").fetchone()[0])

    def search(self, query: str, game: str | None = None, season: str | None = None, limit: int = 5) -> list[OrganizedDocument]:
        embedding = self.embeddings.as_pgvector(self.embeddings.embed(query))
        filters: list[str] = []
        params: list[object] = []
        if game:
            filters.append("game = %s")
            params.append(game)
        if season:
            filters.append("season = %s")
            params.append(season)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.extend([embedding, limit])
        with self._connect() as db:
            rows = db.execute(
                f"SELECT source_document_id, game, season, patch, category, title, summary, content, keywords, source_url FROM game_documents {where} ORDER BY embedding <=> %s::vector LIMIT %s",
                params,
            ).fetchall()
        return [
            OrganizedDocument(
                source_document_id=row[0], game=row[1], season=row[2], patch=row[3],
                category=DocumentCategory(row[4]), title=row[5], summary=row[6],
                content=row[7], keywords=list(row[8] or []), source_url=row[9],
            )
            for row in rows
        ]
