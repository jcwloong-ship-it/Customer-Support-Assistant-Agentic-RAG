"""
SQLite document metadata registry.

Sits alongside ChromaDB to track document-level metadata (title, source,
full text, tags, chunk count, timestamps) so the Knowledge Base UI can
browse, search, edit and delete whole documents without scanning vectors.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "chroma_db" / "kb_registry.sqlite3"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_registry() -> None:
    """Create the documents table if it does not already exist."""
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id      TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                source      TEXT DEFAULT '',
                text        TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                tags        TEXT DEFAULT '[]',
                added_at    TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        con.commit()


def upsert_document(
    doc_id: str,
    title: str,
    source: str,
    text: str,
    chunk_count: int = 0,
    tags: Optional[List[str]] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute("""
            INSERT INTO documents
                (doc_id, title, source, text, chunk_count, tags, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                title       = excluded.title,
                source      = excluded.source,
                text        = excluded.text,
                chunk_count = excluded.chunk_count,
                tags        = excluded.tags,
                updated_at  = excluded.updated_at
        """, (doc_id, title, source, text, chunk_count, json.dumps(tags or []), now, now))
        con.commit()


def get_all_documents() -> List[Dict[str, Any]]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM documents ORDER BY added_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_document(doc_id: str) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        con.commit()
    return cur.rowcount > 0


def search_documents(query: str) -> List[Dict[str, Any]]:
    q = f"%{query.lower()}%"
    with _conn() as con:
        rows = con.execute("""
            SELECT * FROM documents
            WHERE lower(title)  LIKE ?
               OR lower(source) LIKE ?
               OR lower(text)   LIKE ?
               OR lower(tags)   LIKE ?
            ORDER BY added_at DESC
        """, (q, q, q, q)).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_stats() -> Dict[str, Any]:
    with _conn() as con:
        row = con.execute("""
            SELECT
                COUNT(*)            AS total_docs,
                SUM(chunk_count)    AS total_chunks,
                COUNT(DISTINCT source) AS unique_sources,
                MAX(added_at)       AS last_added
            FROM documents
        """).fetchone()
    return dict(row) if row else {}


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d["tags"] = json.loads(d.get("tags", "[]"))
    return d


# Initialise on import
init_registry()
