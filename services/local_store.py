from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime


def _connect(db_path: str) -> sqlite3.Connection:
    base_dir = os.path.dirname(db_path)
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def load_sqlite_payload(db_path: str) -> dict | None:
    try:
        with _connect(db_path) as conn:
            row = conn.execute("SELECT payload FROM app_state WHERE id = 1").fetchone()
    except Exception:
        return None

    if not row or row[0] is None:
        return None

    try:
        payload = json.loads(str(row[0]))
    except Exception:
        return None

    return payload if isinstance(payload, dict) else None


def save_sqlite_payload(db_path: str, payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False

    try:
        serialized = json.dumps(payload, ensure_ascii=False)
    except Exception:
        return False

    now_iso = datetime.now().isoformat(timespec="seconds")
    try:
        with _connect(db_path) as conn:
            conn.execute(
                "REPLACE INTO app_state (id, payload, updated_at) VALUES (1, ?, ?)",
                (serialized, now_iso),
            )
            conn.commit()
        return True
    except Exception:
        return False


def delete_sqlite_payload(db_path: str) -> None:
    # Remove DB and sidecar WAL/SHM files if they exist.
    paths = [db_path, f"{db_path}-wal", f"{db_path}-shm"]
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
