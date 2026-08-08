"""任务管理核心逻辑"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from src.core.data_storage import Category, DataStorage, Task, TaskLog
from src.utils.constants import (
    DEFAULT_POMODORO_WORK,
    TASK_TYPE_HABIT,
    TASK_TYPE_POMODORO,
    TASK_TYPE_TODO,
)


class TaskManager:
    """封装任务/分类/日志的高层 API，供 UI 与提醒引擎调用"""

    def __init__(self, storage: DataStorage):
        self.storage = storage

    # ----- 任务 CRUD -----

    def list_tasks(self, enabled_only: bool = False) -> list[Task]:
        return self.storage.list_tasks(enabled_only=enabled_only)

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.storage.get_task(task_id)

    def add_task(
        self,
        title: str,
        task_type: str = TASK_TYPE_TODO,
        category: str = "未分类",
        reminder_time: Optional[str] = None,
        repeat_days: Optional[list[int]] = None,
        duration: int = DEFAULT_POMODORO_WORK,
        is_enabled: bool = True,
    ) -> Task:
        task = Task(
            id=0,
            title=title,
            category=category,
            type=task_type,
            reminder_time=reminder_time,
            repeat_days=repeat_days or [],
            duration=duration,
            is_enabled=is_enabled,
        )
        task.id = self.storage.add_task(task)
        return task

    def update_task(self, task: Task) -> None:
        self.storage.update_task(task)

    def delete_task(self, task_id: int) -> None:
        self.storage.delete_task(task_id)

    def toggle_task(self, task_id: int) -> None:
        task = self.storage.get_task(task_id)
        if task:
            task.is_enabled = not task.is_enabled
            self.storage.update_task(task)

    # ----- 今日任务 / 完成状态 -----

    def today_tasks(self, today: Optional[date] = None) -> list[Task]:
        """返回今日需要完成的任务（按 repeat_days 过滤）"""
        today = today or date.today()
        iso_weekday = today.isoweekday()  # 1=Mon ... 7=Sun
        result: list[Task] = []
        for t in self.storage.list_tasks(enabled_only=True):
            if not t.repeat_days:
                # 没设置重复日，每天都会出现
                result.append(t)
            elif iso_weekday in t.repeat_days:
                result.append(t)
        return result

    def completed_task_ids_today(self, today: Optional[date] = None) -> set[int]:
        today = today or date.today()
        return {log.task_id for log in self.storage.logs_for_date(today)}

    def complete_task(self, task_id: int, duration_minutes: int = 0) -> None:
        """标记任务为已完成（写入日志）"""
        self.storage.add_log(task_id, duration_minutes=duration_minutes)

    def uncomplete_task(self, task_id: int, today: Optional[date] = None) -> None:
        """撤销今日的完成记录"""
        today = today or date.today()
        # 删除当日该任务所有日志
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
        with self.storage._cursor() as cur:  # 复用连接，简单实现
            cur.execute(
                "DELETE FROM task_logs WHERE task_id=? AND completed_at BETWEEN ? AND ?",
                (task_id, start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            )

    # ----- 分类 -----

    def list_categories(self) -> list[Category]:
        return self.storage.list_categories()

    def upsert_category(self, name: str, color: str = "#3B82F6", cat_id: Optional[int] = None) -> int:
        return self.storage.upsert_category(name, color, cat_id)

    def delete_category(self, cat_id: int) -> None:
        self.storage.delete_category(cat_id)

    # ----- 统计 -----

    def stats_for_date(self, day: Optional[date] = None) -> dict:
        day = day or date.today()
        today_tasks = self.today_tasks(day)
        completed_ids = self.completed_task_ids_today(day)
        total = len(today_tasks)
        done = sum(1 for t in today_tasks if t.id in completed_ids)
        logs = self.storage.logs_for_date(day)
        focus_minutes = sum(l.duration_minutes for l in logs if l.duration_minutes > 0)
        return {
            "total": total,
            "done": done,
            "rate": (done / total) if total else 0.0,
            "focus_minutes": focus_minutes,
        }

    def weekly_summary(self, today: Optional[date] = None) -> dict:
        """返回最近 7 天每日完成数与专注分钟数"""
        today = today or date.today()
        days = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            stats = self.stats_for_date(d)
            days.append({"date": d.isoformat(), "done": stats["done"], "focus_minutes": stats["focus_minutes"]})
        return {"days": days}

    def streak_days(self, today: Optional[date] = None) -> int:
        """连续打卡天数（按完成数 > 0 判定）"""
        today = today or date.today()
        streak = 0
        d = today
        for _ in range(365):
            stats = self.stats_for_date(d)
            if stats["done"] > 0:
                streak += 1
                d = d - timedelta(days=1)
            else:
                break
        return streak

    # ----- 提醒触发判定 -----

    def due_tasks_at(self, when: datetime) -> list[Task]:
        """返回在 when 时刻（HH:MM）应被提醒的任务"""
        hhmm = when.strftime("%H:%M")
        iso = when.isoweekday()
        out: list[Task] = []
        for t in self.storage.list_tasks(enabled_only=True):
            if t.reminder_time != hhmm:
                continue
            if t.repeat_days and iso not in t.repeat_days:
                continue
            out.append(t)
        return out
