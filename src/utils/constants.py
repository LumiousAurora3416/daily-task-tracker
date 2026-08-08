"""常量定义"""
from PySide6.QtGui import QColor

# 应用信息
APP_NAME = "每日任务管理"
APP_VERSION = "0.1.0"

# 默认分类（启动时自动创建）
DEFAULT_CATEGORIES = [
    ("未分类", "#9CA3AF"),
    ("求职", "#3B82F6"),
    ("学习", "#10B981"),
    ("健康", "#F59E0B"),
]

# 任务类型标识
TASK_TYPE_TODO = "todo"
TASK_TYPE_HABIT = "habit"
TASK_TYPE_POMODORO = "pomodoro"

TASK_TYPE_LABELS = {
    TASK_TYPE_TODO: "待办",
    TASK_TYPE_HABIT: "打卡",
    TASK_TYPE_POMODORO: "专注",
}

# 番茄钟默认配置
DEFAULT_POMODORO_WORK = 25  # 分钟
DEFAULT_POMODORO_BREAK = 5  # 分钟

# 重复周期：周一到周日（ISO 周几，1=Mon ... 7=Sun）
WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]

# 提醒引擎轮询间隔（毫秒）
REMINDER_TICK_MS = 1000

# 每日重置检查间隔（毫秒）
DAILY_RESET_TICK_MS = 60_000

# 数据库文件相对路径
DB_REL_PATH = "data/tasks.db"


def hex_to_qcolor(hex_str: str) -> QColor:
    """将 #RRGGBB 转换为 QColor"""
    if not hex_str:
        return QColor("#9CA3AF")
    return QColor(hex_str)
