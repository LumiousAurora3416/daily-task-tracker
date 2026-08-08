"""主窗口：三栏布局 + 番茄钟控件"""
from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.data_storage import Task
from src.core.pomodoro_timer import PomodoroTimer
from src.core.task_manager import TaskManager
from src.utils.constants import (
    APP_NAME,
    DEFAULT_POMODORO_BREAK,
    DEFAULT_POMODORO_WORK,
    TASK_TYPE_LABELS,
    TASK_TYPE_POMODORO,
)
from src.ui.category_dialog import CategoryDialog
from src.ui.task_dialog import TaskDialog


class MainWindow(QMainWindow):
    """主窗口：今日任务 / 分类筛选 / 统计概览 + 番茄钟"""

    request_quit = Signal()

    def __init__(
        self,
        task_manager: TaskManager,
        pomodoro: PomodoroTimer,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.task_manager = task_manager
        self.pomodoro = pomodoro
        self._filter_category: Optional[str] = None
        self.setWindowTitle(APP_NAME)
        self.resize(920, 600)
        self._build_ui()
        self._connect()
        self.refresh()

        # 番茄钟显示用 1s tick
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(1000)
        self._ui_timer.timeout.connect(self._update_pomodoro_label)
        self._ui_timer.start()

    # ----- UI 构建 -----

    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        root.addWidget(self._build_task_panel(), 5)
        root.addWidget(self._build_side_panel(), 2)
        root.addWidget(self._build_stats_panel(), 2)
        self.setCentralWidget(central)

    def _build_task_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        title = QLabel("今日任务")
        title.setFont(self._title_font())
        layout.addWidget(title)

        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(True)
        self.task_list.itemDoubleClicked.connect(self._on_edit_task)
        layout.addWidget(self.task_list, 1)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("＋ 添加任务")
        self.btn_complete = QPushButton("标记完成")
        self.btn_uncomplete = QPushButton("撤销完成")
        self.btn_edit = QPushButton("编辑")
        self.btn_del = QPushButton("删除")
        for b in (self.btn_add, self.btn_complete, self.btn_uncomplete, self.btn_edit, self.btn_del):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        # 番茄钟区
        pomo_box = QGroupBox("专注番茄钟")
        pomo_layout = QVBoxLayout(pomo_box)
        self.pomodoro_label = QLabel(PomodoroTimer.format(DEFAULT_POMODORO_WORK * 60))
        self.pomodoro_label.setFont(QFont("Menlo", 28, QFont.Bold))
        self.pomodoro_label.setAlignment(Qt.AlignCenter)
        self.pomodoro_task_label = QLabel("未开始")
        self.pomodoro_task_label.setAlignment(Qt.AlignCenter)
        pomo_layout.addWidget(self.pomodoro_label)
        pomo_layout.addWidget(self.pomodoro_task_label)

        pomo_btn_row = QHBoxLayout()
        self.btn_pomo_start = QPushButton("开始工作")
        self.btn_pomo_break = QPushButton("开始休息")
        self.btn_pomo_pause = QPushButton("暂停")
        self.btn_pomo_stop = QPushButton("停止")
        for b in (self.btn_pomo_start, self.btn_pomo_break, self.btn_pomo_pause, self.btn_pomo_stop):
            pomo_btn_row.addWidget(b)
        pomo_layout.addLayout(pomo_btn_row)
        layout.addWidget(pomo_box)

        return panel

    def _build_side_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        title = QLabel("分类")
        title.setFont(self._title_font())
        layout.addWidget(title)

        self.category_list = QListWidget()
        layout.addWidget(self.category_list, 1)

        btn_row = QHBoxLayout()
        self.btn_manage_category = QPushButton("管理分类")
        btn_row.addWidget(self.btn_manage_category)
        layout.addLayout(btn_row)

        layout.addStretch()
        return panel

    def _build_stats_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        title = QLabel("统计概览")
        title.setFont(self._title_font())
        layout.addWidget(title)

        self.lbl_rate = QLabel("完成率 0%")
        self.lbl_done = QLabel("已完成 0 / 0")
        self.lbl_focus = QLabel("今日专注 0 分钟")
        self.lbl_streak = QLabel("连续打卡 0 天")
        for lbl in (self.lbl_rate, self.lbl_done, self.lbl_focus, self.lbl_streak):
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        self.weekly_label = QLabel("近 7 天")
        self.weekly_label.setFont(self._title_font(11))
        layout.addWidget(self.weekly_label)
        self.weekly_list = QListWidget()
        layout.addWidget(self.weekly_list, 1)

        layout.addStretch()
        return panel

    @staticmethod
    def _title_font(size: int = 14) -> QFont:
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        return f

    # ----- 信号连接 -----

    def _connect(self) -> None:
        self.btn_add.clicked.connect(self._on_add_task)
        self.btn_complete.clicked.connect(self._on_complete_task)
        self.btn_uncomplete.clicked.connect(self._on_uncomplete_task)
        self.btn_edit.clicked.connect(self._on_edit_task)
        self.btn_del.clicked.connect(self._on_delete_task)
        self.btn_manage_category.clicked.connect(self._on_manage_category)
        self.category_list.itemClicked.connect(self._on_category_clicked)

        self.btn_pomo_start.clicked.connect(self._on_pomo_start)
        self.btn_pomo_break.clicked.connect(self._on_pomo_break)
        self.btn_pomo_pause.clicked.connect(self._on_pomo_pause)
        self.btn_pomo_stop.clicked.connect(self._on_pomo_stop)
        self.pomodoro.tick.connect(self._update_pomodoro_label)
        self.pomodoro.phase_changed.connect(self._on_pomo_phase_changed)
        self.pomodoro.finished.connect(self._on_pomo_finished)

    # ----- 数据刷新 -----

    def refresh(self) -> None:
        self._refresh_tasks()
        self._refresh_categories()
        self._refresh_stats()

    def _refresh_tasks(self) -> None:
        completed_ids = self.task_manager.completed_task_ids_today()
        tasks = self.task_manager.today_tasks()
        if self._filter_category:
            tasks = [t for t in tasks if t.category == self._filter_category]

        self.task_list.clear()
        for t in tasks:
            label = self._task_label(t, t.id in completed_ids)
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, t.id)
            if t.id in completed_ids:
                f = item.font()
                f.setStrikeOut(True)
                item.setFont(f)
            self.task_list.addItem(item)

    def _refresh_categories(self) -> None:
        current = self._filter_category
        self.category_list.clear()
        all_item = QListWidgetItem("全部")
        all_item.setData(Qt.UserRole, None)
        self.category_list.addItem(all_item)
        for c in self.task_manager.list_categories():
            item = QListWidgetItem(f"{c.name}")
            item.setData(Qt.UserRole, c.name)
            if c.name == current:
                self.category_list.setCurrentItem(item)
            self.category_list.addItem(item)
        if current is None:
            self.category_list.setCurrentRow(0)

    def _refresh_stats(self) -> None:
        stats = self.task_manager.stats_for_date()
        self.lbl_rate.setText(f"完成率 {stats['rate']*100:.0f}%")
        self.lbl_done.setText(f"已完成 {stats['done']} / {stats['total']}")
        hours = stats["focus_minutes"] / 60
        self.lbl_focus.setText(f"今日专注 {stats['focus_minutes']} 分钟 ({hours:.1f}h)")
        self.lbl_streak.setText(f"连续打卡 {self.task_manager.streak_days()} 天")

        self.weekly_list.clear()
        for d in self.task_manager.weekly_summary()["days"]:
            self.weekly_list.addItem(f"{d['date']}  完成 {d['done']}  专注 {d['focus_minutes']}m")

    # ----- 事件处理 -----

    @staticmethod
    def _task_label(t: Task, done: bool) -> str:
        prefix = TASK_TYPE_LABELS.get(t.type, "任务")
        check = "✅" if done else "▢"
        time_part = f"  ⏰{t.reminder_time}" if t.reminder_time else ""
        return f"{check} [{t.category}/{prefix}] {t.title}{time_part}"

    def _selected_task_id(self) -> Optional[int]:
        item = self.task_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _on_add_task(self) -> None:
        if TaskDialog.new_task(self.task_manager, self):
            self.refresh()

    def _on_edit_task(self, *_: object) -> None:
        tid = self._selected_task_id()
        if tid is None:
            return
        task = self.task_manager.get_task(tid)
        if not task:
            return
        if TaskDialog.edit_task(self.task_manager, task, self):
            self.refresh()

    def _on_complete_task(self) -> None:
        tid = self._selected_task_id()
        if tid is None:
            return
        self.task_manager.complete_task(tid, 0)
        self.refresh()

    def _on_uncomplete_task(self) -> None:
        tid = self._selected_task_id()
        if tid is None:
            return
        self.task_manager.uncomplete_task(tid)
        self.refresh()

    def _on_delete_task(self) -> None:
        tid = self._selected_task_id()
        if tid is None:
            return
        if QMessageBox.question(self, "删除任务", "确定删除该任务吗？") != QMessageBox.Yes:
            return
        self.task_manager.delete_task(tid)
        self.refresh()

    def _on_manage_category(self) -> None:
        dlg = CategoryDialog(self.task_manager, self)
        dlg.exec()
        self.refresh()

    def _on_category_clicked(self, item: QListWidgetItem) -> None:
        self._filter_category = item.data(Qt.UserRole)
        self._refresh_tasks()

    # ----- 番茄钟 -----

    def _on_pomo_start(self) -> None:
        tid = self._selected_task_id()
        task = self.task_manager.get_task(tid) if tid else None
        minutes = task.duration if task and task.type == TASK_TYPE_POMODORO else DEFAULT_POMODORO_WORK
        title = task.title if task else "专注"
        # 选中番茄钟任务并完成时记录时长
        self.pomodoro.start_work(task_id=(task.id if task else None), task_title=title, minutes=minutes)

    def _on_pomo_break(self) -> None:
        self.pomodoro.start_break(DEFAULT_POMODORO_BREAK)

    def _on_pomo_pause(self) -> None:
        self.pomodoro.pause()

    def _on_pomo_stop(self) -> None:
        self.pomodoro.stop()
        self._update_pomodoro_label()

    def _on_pomo_phase_changed(self, phase: str) -> None:
        text = {
            PomodoroTimer.PHASE_WORK: "工作中",
            PomodoroTimer.PHASE_BREAK: "休息中",
            PomodoroTimer.PHASE_IDLE: "未开始",
        }.get(phase, "")
        title = self.pomodoro.task_title if phase != PomodoroTimer.PHASE_IDLE else ""
        self.pomodoro_task_label.setText(f"{text}{' · ' + title if title else ''}")

    def _update_pomodoro_label(self, *_: object) -> None:
        if self.pomodoro.is_running:
            self.pomodoro_label.setText(PomodoroTimer.format(self.pomodoro.remaining_seconds))
        elif self.pomodoro.phase == PomodoroTimer.PHASE_IDLE:
            self.pomodoro_label.setText(PomodoroTimer.format(DEFAULT_POMODORO_WORK * 60))

    def _on_pomo_finished(self, phase: str, minutes: int) -> None:
        if phase == PomodoroTimer.PHASE_WORK and self.pomodoro.task_id:
            self.task_manager.complete_task(self.pomodoro.task_id, minutes)
            self.refresh()
        QMessageBox.information(self, "番茄钟", f"{'工作' if phase == PomodoroTimer.PHASE_WORK else '休息'}阶段完成 ({minutes} 分钟)")

    # ----- 窗口行为 -----

    def closeEvent(self, event) -> None:  # noqa: N802
        # 关闭窗口不退出，由托盘统一管理退出
        event.ignore()
        self.hide()
