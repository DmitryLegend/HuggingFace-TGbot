"""
Простое хранилище на SQLite (через aiosqlite, без блокировки event loop):
- кто пользуется ботом (users)
- какие задачи и когда запускали (requests) — для админ-статистики

Файл базы задаётся в config.DB_PATH (по умолчанию bot_data.db, лежит рядом с ботом).
"""

from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_requests_task ON requests(task);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def upsert_user(user_id: int, username: str | None, first_name: str | None) -> None:
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_seen = excluded.last_seen
            """,
            (user_id, username, first_name, now, now),
        )
        await db.commit()


async def log_request(user_id: int, task: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO requests (user_id, task, created_at) VALUES (?, ?, ?)",
            (user_id, task, _now()),
        )
        await db.commit()


async def get_stats() -> dict:
    """Возвращает агрегированную статистику для админ-панели."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute("SELECT COUNT(*) AS c FROM users")
        total_users = (await cur.fetchone())["c"]

        cur = await db.execute("SELECT COUNT(*) AS c FROM requests")
        total_requests = (await cur.fetchone())["c"]

        cur = await db.execute(
            "SELECT task, COUNT(*) AS cnt FROM requests GROUP BY task ORDER BY cnt DESC"
        )
        by_task = [(row["task"], row["cnt"]) for row in await cur.fetchall()]

        today = datetime.now(timezone.utc).date().isoformat()
        cur = await db.execute(
            "SELECT COUNT(*) AS c FROM requests WHERE created_at LIKE ?",
            (f"{today}%",),
        )
        today_count = (await cur.fetchone())["c"]

        cur = await db.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM requests WHERE created_at LIKE ?",
            (f"{today}%",),
        )
        active_today = (await cur.fetchone())["c"]

        return {
            "total_users": total_users,
            "total_requests": total_requests,
            "by_task": by_task,
            "today_count": today_count,
            "active_today": active_today,
        }
