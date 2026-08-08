"""系统托盘应用：聚合 ReminderEngine / TaskManager / MainWindow"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.core.pomodoro_timer import PomodoroTimer
from src.core.reminder_engine import ReminderEngine
from src.core.task_manager import TaskManager
from src.ui.main_window import MainWindow
from src.utils.constants import APP_NAME, TASK_TYPE_LABELS


def _make_icon() -> QIcon:
    """生成简单的圆形图标"""
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    from PySide6.QtGui import QPainter, QPen, QBrush

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#3B82F6"), 2))
    painter.setBrush(QBrush(QColor("#3B82F6")))
    painter.drawEllipse(8, 8, 48, 48)
    painter.setPen(QPen(QColor("#FFFFFF"), 2))
    font = painter.font()
    font.setPointSize(20)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), 0x84, "任")  # AlignCenter
    painter.end()
    return QIcon(pix)


class TrayApp(QObject):
    """系统托盘 + 主窗口编排"""

    def __init__(
        self,
        task_manager: TaskManager,
        reminder_engine: ReminderEngine,
        pomodoro: PomodoroTimer,
    ):
        super().__init__()
        self.task_manager = task_manager
        self.reminder_engine = reminder_engine
        self.pomodoro = pomodoro
        self.window: Optional[MainWindow] = None

        self.tray = QSystemTrayIcon(_make_icon(), self)
        self.tray.setToolTip(APP_NAME)
        self._build_menu()
        self._connect()

    def _build_menu(self) -> None:
        menu = QMenu()

        self.action_show = QAction("打开主窗口", menu)
        self.action_show.triggered.connect(self.show_window)
        menu.addAction(self.action_show)

        self.action_add = QAction("添加任务…", menu)
        menu.addAction(self.action_add)

        menu.addSeparator()

        self.stats_action = QAction("今日统计", menu)
        menu.addAction(self.stats_action)

        menu.addSeparator()

        self.action_quit = QAction("退出", menu)
        self.action_quit.triggered.connect(self._on_quit)
        menu.addAction(self.action_quit)

        self.tray.setContextMenu(menu)

    def _connect(self) -> None:
        self.tray.activated.connect(self._on_activated)
        self.reminder_engine.set_remind_callback(self._on_remind)
        self.reminder_engine.day_changed.connect(self._on_day_changed)
        self.action_add.triggered.connect(self._on_add)
        self.stats_action.triggered.connect(self.show_window)

    # ----- 生命周期 -----

    def show(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            # 没有托盘时退化为普通窗口
            self.show_window()
        self.tray.show()

    def show_window(self) -> None:
        if self.window is None:
            self.window = MainWindow(self.task_manager, self.pomodoro)
        self.window.refresh()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    # ----- 托盘回调 -----

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window()

    def _on_add(self) -> None:
        self.show_window()
        self.window._on_add_task()  # 复用主窗口的添加流程

    def _on_remind(self, tasks: list) -> None:
        from src.core.reminder_engine import ReminderEngine

        title, body = ReminderEngine.format_message(tasks)
        if title:
            self.tray.showMessage(title, body, QSystemTrayIcon.Information, 5000)

    def _on_day_changed(self) -> None:
        if self.window is not None:
            self.window.refresh()
        self._update_tooltip()

    def _update_tooltip(self) -> None:
        stats = self.task_manager.stats_for_date()
        self.tray.setToolTip(f"{APP_NAME} - 今日 {stats['done']}/{stats['total']}")

    def _on_quit(self) -> None:
        self.reminder_engine.stop()
        if self.window is not None:
            self.window.close()
        QApplication.quit()
