"""
Bunny Backend - Database Layer
SQLite database for authors, documents, and commit history.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from app.config import settings

DB_PATH = settings.DATABASE_PATH


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS authors (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            total_commits INTEGER NOT NULL DEFAULT 0,
            solana_pubkey TEXT
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            author_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (author_id) REFERENCES authors(id)
        );

        CREATE TABLE IF NOT EXISTS commits (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            commit_number INTEGER NOT NULL,
            manuscript_hash TEXT NOT NULL,
            humanity_score REAL NOT NULL,
            ai_score REAL NOT NULL,
            temporal_score REAL NOT NULL,
            linguistic_features TEXT,
            commit_message TEXT NOT NULL DEFAULT '',
            word_count INTEGER NOT NULL DEFAULT 0,
            char_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            tx_signature TEXT,
            on_chain_status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (author_id) REFERENCES authors(id)
        );

        CREATE INDEX IF NOT EXISTS idx_commits_document ON commits(document_id);
        CREATE INDEX IF NOT EXISTS idx_commits_author   ON commits(author_id);
        CREATE INDEX IF NOT EXISTS idx_commits_hash     ON commits(manuscript_hash);
    """)
    conn.commit()
    conn.close()


# ── Authors ──────────────────────────────────────────────────────────

def create_author(author_id: str, display_name: str) -> dict:
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO authors (id, display_name) VALUES (?, ?)",
        (author_id, display_name),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM authors WHERE id = ?", (author_id,)).fetchone()
    conn.close()
    return dict(row)


def get_author(author_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM authors WHERE id = ?", (author_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def increment_author_commits(author_id: str):
    conn = get_db()
    conn.execute("UPDATE authors SET total_commits = total_commits + 1 WHERE id = ?", (author_id,))
    conn.commit()
    conn.close()


# ── Documents ────────────────────────────────────────────────────────

def create_document(doc_id: str, author_id: str, title: str) -> dict:
    conn = get_db()
    conn.execute("INSERT INTO documents (id, author_id, title) VALUES (?, ?, ?)", (doc_id, author_id, title))
    conn.commit()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row)


def get_document(doc_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_documents_by_author(author_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM documents WHERE author_id = ? ORDER BY updated_at DESC", (author_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_document_timestamp(doc_id: str):
    conn = get_db()
    conn.execute("UPDATE documents SET updated_at = datetime('now') WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


# ── Commits ──────────────────────────────────────────────────────────

def create_commit(
    commit_id: str, document_id: str, author_id: str, commit_number: int,
    manuscript_hash: str, humanity_score: float, ai_score: float, temporal_score: float,
    linguistic_features: dict, commit_message: str, word_count: int, char_count: int,
) -> dict:
    conn = get_db()
    conn.execute(
        """INSERT INTO commits
           (id, document_id, author_id, commit_number, manuscript_hash,
            humanity_score, ai_score, temporal_score, linguistic_features,
            commit_message, word_count, char_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (commit_id, document_id, author_id, commit_number, manuscript_hash,
         humanity_score, ai_score, temporal_score, json.dumps(linguistic_features),
         commit_message, word_count, char_count),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM commits WHERE id = ?", (commit_id,)).fetchone()
    conn.close()
    result = dict(row)
    result["linguistic_features"] = json.loads(result["linguistic_features"] or "{}")
    return result


def get_commits_by_document(document_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM commits WHERE document_id = ? ORDER BY commit_number ASC", (document_id,)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["linguistic_features"] = json.loads(d["linguistic_features"] or "{}")
        out.append(d)
    return out


def get_latest_commit(document_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM commits WHERE document_id = ? ORDER BY commit_number DESC LIMIT 1",
        (document_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["linguistic_features"] = json.loads(d["linguistic_features"] or "{}")
        return d
    return None


def get_commit_count(document_id: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM commits WHERE document_id = ?", (document_id,)
    ).fetchone()
    conn.close()
    return row["cnt"]


def update_commit_tx(commit_id: str, tx_signature: str, status: str = "confirmed"):
    conn = get_db()
    conn.execute(
        "UPDATE commits SET tx_signature = ?, on_chain_status = ? WHERE id = ?",
        (tx_signature, status, commit_id),
    )
    conn.commit()
    conn.close()


def get_commit_by_hash(manuscript_hash: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM commits WHERE manuscript_hash = ? ORDER BY created_at DESC LIMIT 1",
        (manuscript_hash,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["linguistic_features"] = json.loads(d["linguistic_features"] or "{}")
        return d
    return None


def get_all_commits_by_author(author_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, d.title as document_title
           FROM commits c JOIN documents d ON c.document_id = d.id
           WHERE c.author_id = ? ORDER BY c.created_at DESC""",
        (author_id,),
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["linguistic_features"] = json.loads(d["linguistic_features"] or "{}")
        out.append(d)
    return out
