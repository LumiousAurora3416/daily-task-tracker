"""番茄钟计时器：基于 QTimer"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from src.utils.constants import DEFAULT_POMODORO_BREAK, DEFAULT_POMODORO_WORK


class PomodoroTimer(QObject):
    """工作 / 休息循环计时器

    状态机：idle -> working <-> break -> idle
    """

    TICK_MS = 1000

    # signals
    tick = Signal(int, int)         # remaining_seconds, total_seconds
    phase_changed = Signal(str)     # "working" | "break" | "idle"
    finished = Signal(str, int)     # phase, completed_minutes

    PHASE_IDLE = "idle"
    PHASE_WORK = "working"
    PHASE_BREAK = "break"

    def __init__(self, work_minutes: int = DEFAULT_POMODORO_WORK, break_minutes: int = DEFAULT_POMODORO_BREAK):
        super().__init__()
        self.work_minutes = work_minutes
        self.break_minutes = break_minutes
        self._phase = self.PHASE_IDLE
        self._remaining = 0
        self._total = 0
        self._task_id: Optional[int] = None
        self._task_title: str = ""
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._on_tick)

    # ----- 状态查询 -----

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def is_running(self) -> bool:
        return self._timer.isActive()

    @property
    def remaining_seconds(self) -> int:
        return self._remaining

    @property
    def total_seconds(self) -> int:
        return self._total

    @property
    def task_id(self) -> Optional[int]:
        return self._task_id

    @property
    def task_title(self) -> str:
        return self._task_title

    # ----- 控制 -----

    def start_work(self, task_id: Optional[int] = None, task_title: str = "", minutes: Optional[int] = None) -> None:
        mins = minutes or self.work_minutes
        self._task_id = task_id
        self._task_title = task_title
        self._begin_phase(self.PHASE_WORK, mins * 60)

    def start_break(self, minutes: Optional[int] = None) -> None:
        mins = minutes or self.break_minutes
        self._task_id = None
        self._task_title = "休息"
        self._begin_phase(self.PHASE_BREAK, mins * 60)

    def pause(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

    def resume(self) -> None:
        if not self._timer.isActive() and self._phase != self.PHASE_IDLE:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._phase = self.PHASE_IDLE
        self._remaining = 0
        self._total = 0
        self._task_id = None
        self._task_title = ""
        self.phase_changed.emit(self._phase)

    # ----- 内部 -----

    def _begin_phase(self, phase: str, total_seconds: int) -> None:
        self._phase = phase
        self._total = total_seconds
        self._remaining = total_seconds
        self.phase_changed.emit(phase)
        self.tick.emit(self._remaining, self._total)
        self._timer.start()

    def _on_tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            completed_minutes = self._total // 60
            phase = self._phase
            # 先重置状态，再发 finished 信号
            self._phase = self.PHASE_IDLE
            self._remaining = 0
            self.finished.emit(phase, completed_minutes)
            self.phase_changed.emit(self.PHASE_IDLE)
        else:
            self.tick.emit(self._remaining, self._total)

    @staticmethod
    def format(seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"
