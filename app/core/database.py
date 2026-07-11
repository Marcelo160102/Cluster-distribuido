"""Capa de persistencia con SQLite.

Cada nodo mantiene su propia base de datos local en modo WAL para
permitir concurrencia de lecturas. Todas las consultas usan
parámetros vinculados (? / :nombre) para prevenir inyección SQL.
"""
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


# Ubicación del archivo .db: dentro del contenedor en /app/data, fuera de Docker en ./data
DB_DIR = Path("/app/data") if Path("/app/data").exists() else Path("data")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "data.db"


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión SQLite con row_factory y PRAGMAs esenciales."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Crea la tabla items si no existe (ejecutado en startup de FastAPI)."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


# --- Operaciones CRUD ---

def get_all() -> list[dict]:
    """Retorna todos los registros de endpoints VoIP."""
    with get_connection() as conn:
        rows = conn.execute("SELECT id, data, created_at, updated_at FROM items").fetchall()
        return [dict(r) for r in rows]


def get_by_id(item_id: str) -> dict | None:
    """Busca un registro por su UUID; retorna None si no existe."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, data, created_at, updated_at FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        return dict(row) if row else None


def create(data: str) -> dict:
    """Inserta un nuevo registro con UUID autogenerado."""
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO items (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (item_id, data, now, now),
        )
    return {"id": item_id, "data": data, "created_at": now, "updated_at": now}


def update(item_id: str, data: str) -> dict | None:
    """Actualiza el campo data y updated_at; retorna None si el ID no existe."""
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
    """Elimina un registro por su ID; retorna True si se eliminó algo."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cursor.rowcount > 0


# --- Operaciones de sincronización total (transacción atómica) ---

def delete_all() -> None:
    """Vacía la tabla local (usado antes de la sincronización completa)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM items")


def insert_many(items: list[dict]) -> None:
    """Inserta múltiples registros en una sola transacción atómica.

    Usado cuando un nodo recuperado descarga el estado completo del líder.
    Si algo falla a medio camino, el nodo mantiene su tabla vacía y reintenta.
    """
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO items (id, data, created_at, updated_at) VALUES (:id, :data, :created_at, :updated_at)",
            items,
        )