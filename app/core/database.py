import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


DB_DIR = Path("/app/data") if Path("/app/data").exists() else Path("data")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def get_all() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, data, created_at, updated_at FROM items").fetchall()
        return [dict(r) for r in rows]


def get_by_id(item_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, data, created_at, updated_at FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        return dict(row) if row else None


def create(data: str) -> dict:
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO items (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (item_id, data, now, now),
        )
    return {"id": item_id, "data": data, "created_at": now, "updated_at": now}


def update(item_id: str, data: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE items SET data = ?, updated_at = ? WHERE id = ?",
            (data, now, item_id),
        )
        if cursor.rowcount == 0:
            return None
    return {"id": item_id, "data": data, "updated_at": now}


def delete(item_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cursor.rowcount > 0


def delete_all() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM items")


def insert_many(items: list[dict]) -> None:
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO items (id, data, created_at, updated_at) VALUES (:id, :data, :created_at, :updated_at)",
            items,
        )