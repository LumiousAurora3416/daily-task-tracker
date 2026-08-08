"""提醒引擎：每秒检查到点任务，发送系统通知"""
from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from src.core.data_storage import Task
from src.core.task_manager import TaskManager
from src.utils.constants import DAILY_RESET_TICK_MS, REMINDER_TICK_MS, TASK_TYPE_LABELS


class ReminderEngine(QObject):
    """到点提醒 + 每日 00:00 检测重置"""

    # 信号：触发提醒时发出（task 列表）
    reminders_triggered = Signal(list)
    # 信号：跨日重置
    day_changed = Signal()

    def __init__(self, task_manager: TaskManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.task_manager = task_manager
        self._last_minute: Optional[str] = None
        self._last_date: Optional[date] = None
        self._on_remind: Optional[Callable[[list[Task]], None]] = None

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(REMINDER_TICK_MS)
        self._tick_timer.timeout.connect(self._on_tick)

        self._reset_timer = QTimer(self)
        self._reset_timer.setInterval(DAILY_RESET_TICK_MS)
        self._reset_timer.timeout.connect(self._check_day_rollover)

    def set_remind_callback(self, cb: Callable[[list[Task]], None]) -> None:
        """设置提醒回调（例如调用 tray.showMessage）"""
        self._on_remind = cb

    def start(self) -> None:
        now = datetime.now()
        self._last_minute = now.strftime("%H:%M")
        self._last_date = now.date()
        self._tick_timer.start()
        self._reset_timer.start()

    def stop(self) -> None:
        self._tick_timer.stop()
        self._reset_timer.stop()

    # ----- 内部 -----

    def _on_tick(self) -> None:
        now = datetime.now()
        hhmm = now.strftime("%H:%M")
        if hhmm == self._last_minute:
            return
        self._last_minute = hhmm
        due = self.task_manager.due_tasks_at(now)
        if due:
            self.reminders_triggered.emit(due)
            if self._on_remind:
                self._on_remind(due)

    def _check_day_rollover(self) -> None:
        today = datetime.now().date()
        if self._last_date is None or today != self._last_date:
            self._last_date = today
            self._last_minute = None  # 强制下一次 tick 重新评估
            self.day_changed.emit()

    @staticmethod
    def format_message(tasks: list[Task]) -> tuple[str, str]:
        """生成通知标题与正文"""
        if not tasks:
            return "", ""
        if len(tasks) == 1:
            t = tasks[0]
            title = f"{TASK_TYPE_LABELS.get(t.type, '任务')}提醒：{t.title}"
            body = f"分类：{t.category}"
            if t.reminder_time:
                body += f"  时间：{t.reminder_time}"
            return title, body
        title = f"有 {len(tasks)} 个任务到点了"
        body = "\n".join(f"· {t.title}" for t in tasks[:5])
        if len(tasks) > 5:
            body += f"\n…还有 {len(tasks) - 5} 个"
        return title, body
