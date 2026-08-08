"""程序入口"""
import os
import sys

# 让 `python main.py` 也能找到 src 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from src.core.data_storage import DataStorage
from src.core.pomodoro_timer import PomodoroTimer
from src.core.reminder_engine import ReminderEngine
from src.core.task_manager import TaskManager
from src.ui.tray_app import TrayApp
from src.utils.constants import APP_NAME, DB_REL_PATH


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # 关闭主窗口后托盘继续运行

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, DB_REL_PATH)

    storage = DataStorage(db_path)
    task_manager = TaskManager(storage)
    pomodoro = PomodoroTimer()
    reminder_engine = ReminderEngine(task_manager)

    tray = TrayApp(task_manager, reminder_engine, pomodoro)
    tray.show()
    reminder_engine.start()
    tray._update_tooltip()

    # 启动时直接显示主窗口
    tray.show_window()

    code = app.exec()
    storage.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
