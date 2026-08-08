"""数据持久化层：基于 SQLite 的轻量存储"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

from src.utils.constants import DEFAULT_CATEGORIES


# ------------------ 数据模型 ------------------


@dataclass
class Category:
    id: int
    name: str
    color: str = "#3B82F6"


@dataclass
class Task:
    id: int
    title: str
    category: str = "未分类"
    type: str = "todo"
    reminder_time: Optional[str] = None  # "HH:MM"
    repeat_days: list[int] = field(default_factory=list)  # ISO 周几 [1..7]
    duration: int = 25  # 番茄钟时长（分钟）
    is_enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TaskLog:
    id: int
    task_id: int
    completed_at: str
    duration_minutes: int = 0


# ------------------ 存储引擎 ------------------


class DataStorage:
    """线程安全的 SQLite 包装层"""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT '未分类',
        type TEXT NOT NULL,
        reminder_time TEXT,
        repeat_days TEXT,
        duration INTEGER DEFAULT 25,
        is_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS task_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        completed_at TIMESTAMP NOT NULL,
        duration_minutes INTEGER DEFAULT 0,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT DEFAULT '#3B82F6'
    );
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # check_same_thread=False + 显式锁，保证跨线程安全
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._lock = threading.RLock()
        self._init_schema()
        self._ensure_default_categories()

    # ----- 基础工具 -----

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def _init_schema(self) -> None:
        with self._cursor() as cur:
            cur.executescript(self.SCHEMA)

    def _ensure_default_categories(self) -> None:
        with self._cursor() as cur:
            for name, color in DEFAULT_CATEGORIES:
                cur.execute(
                    "INSERT OR IGNORE INTO categories(name, color) VALUES (?, ?)",
                    (name, color),
                )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ----- 分类 -----

    def list_categories(self) -> list[Category]:
        with self._cursor() as cur:
            cur.execute("SELECT id, name, color FROM categories ORDER BY id")
            return [Category(r["id"], r["name"], r["color"]) for r in cur.fetchall()]

    def upsert_category(self, name: str, color: str = "#3B82F6", cat_id: Optional[int] = None) -> int:
        with self._cursor() as cur:
            if cat_id is None:
                cur.execute(
                    "INSERT INTO categories(name, color) VALUES (?, ?)",
                    (name, color),
                )
                return cur.lastrowid
            cur.execute(
                "UPDATE categories SET name=?, color=? WHERE id=?",
                (name, color, cat_id),
            )
            return cat_id

    def delete_category(self, cat_id: int) -> None:
        with self._cursor() as cur:
            # 删除前把关联任务的 category 重置为 "未分类"
            cur.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE tasks SET category='未分类' WHERE category=?",
                    (row["name"],),
                )
            cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))

    # ----- 任务 -----

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        repeat = row["repeat_days"]
        repeat_days = json.loads(repeat) if repeat else []
        return Task(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            type=row["type"],
            reminder_time=row["reminder_time"],
            repeat_days=repeat_days,
            duration=row["duration"],
            is_enabled=bool(row["is_enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_tasks(self, enabled_only: bool = False) -> list[Task]:
        with self._cursor() as cur:
            sql = "SELECT * FROM tasks"
            if enabled_only:
                sql += " WHERE is_enabled=1"
            sql += " ORDER BY id"
            cur.execute(sql)
            return [self._row_to_task(r) for r in cur.fetchall()]

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = cur.fetchone()
            return self._row_to_task(row) if row else None

    def add_task(self, task: Task) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO tasks
                   (title, category, type, reminder_time, repeat_days, duration,
                    is_enabled, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.title,
                    task.category,
                    task.type,
                    task.reminder_time,
                    json.dumps(task.repeat_days),
                    task.duration,
                    1 if task.is_enabled else 0,
                    now,
                    now,
                ),
            )
            return cur.lastrowid

    def update_task(self, task: Task) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._cursor() as cur:
            cur.execute(
                """UPDATE tasks SET
                   title=?, category=?, type=?, reminder_time=?, repeat_days=?,
                   duration=?, is_enabled=?, updated_at=?
                   WHERE id=?""",
                (
                    task.title,
                    task.category,
                    task.type,
                    task.reminder_time,
                    json.dumps(task.repeat_days),
                    task.duration,
                    1 if task.is_enabled else 0,
                    now,
                    task.id,
                ),
            )

    def delete_task(self, task_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    # ----- 任务日志 -----

    def add_log(self, task_id: int, duration_minutes: int = 0) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO task_logs(task_id, completed_at, duration_minutes) VALUES (?, ?, ?)",
                (task_id, now, duration_minutes),
            )
            return cur.lastrowid

    def logs_between(self, start: datetime, end: datetime) -> list[TaskLog]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT id, task_id, completed_at, duration_minutes
                   FROM task_logs
                   WHERE completed_at BETWEEN ? AND ?
                   ORDER BY completed_at""",
                (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            )
            return [
                TaskLog(r["id"], r["task_id"], r["completed_at"], r["duration_minutes"])
                for r in cur.fetchall()
            ]

    def logs_for_date(self, day) -> list[TaskLog]:
        # 兼容 date 与 datetime 输入
        if isinstance(day, datetime):
            d = day.date()
        else:
            d = day
        start = datetime.combine(d, datetime.min.time())
        end = datetime.combine(d, datetime.max.time())
        return self.logs_between(start, end)
