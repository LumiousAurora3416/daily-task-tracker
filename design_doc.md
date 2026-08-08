# 轻量级每日任务管理与提醒工具 - 技术实现方案

## 一、项目概述

一款轻量级、低系统资源占用的桌面应用，帮助用户管理日常任务、设置定时提醒、进行专注计时。

### 核心需求
1. **多类型任务管理**：待办事项、固定动作打卡、专注计时（番茄钟）
2. **定时提醒系统**：每日固定时间点提醒，支持自定义频率和时间
3. **任务分类功能**：按类别（求职、学习、健康等）管理
4. **极简界面**：低资源占用、后台运行、系统托盘
5. **本地存储**：SQLite 轻量存储，离线可用，隐私安全

---

## 二、开发语言及框架选择

| 方案 | 推荐选型 | 理由 |
|------|----------|------|
| **首选** | Python 3.11+ + PySide6 | 轻量高效、原生系统托盘、SQLite 内置 |
| **备选** | Tauri 2.0 + React | 现代 Web UI，比 Electron 轻 10 倍 |

### 为什么不选 Electron？
- 基础内存占用 ≥ 150MB，远超"轻量级"要求
- 启动速度慢，资源消耗大

---

## 三、项目结构

```
daily-task-tracker/
├── main.py                    # 程序入口
├── requirements.txt           # 依赖列表
├── design_doc.md              # 技术方案文档
├── src/
│   ├── __init__.py
│   ├── core/                  # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── task_manager.py    # 任务管理
│   │   ├── reminder_engine.py # 提醒引擎
│   │   ├── pomodoro_timer.py  # 番茄钟
│   │   └── data_storage.py    # 数据持久化
│   ├── ui/                    # 界面层
│   │   ├── __init__.py
│   │   ├── tray_app.py        # 系统托盘
│   │   ├── main_window.py     # 主窗口
│   │   ├── task_dialog.py     # 任务编辑对话框
│   │   └── category_dialog.py # 分类管理对话框
│   └── utils/                 # 工具类
│       ├── __init__.py
│       └── constants.py       # 常量定义
└── data/
    └── tasks.db               # SQLite 数据库（自动创建）
```

---

## 四、核心功能模块设计

### 4.1 任务管理模块 (TaskManager)

```python
from enum import Enum

class TaskType(Enum):
    TODO = "todo"           # 待办事项：投递简历、准备面试
    HABIT = "habit"         # 习惯打卡：刷行测题
    POMODORO = "pomodoro"   # 专注计时：番茄钟

class Task:
    id: int
    title: str
    category: str           # 求职、学习、健康等
    type: TaskType
    reminder_time: str      # "09:00" 格式
    repeat_days: list[int]  # [0,1,2,3,4] 周一到周五
    duration: int           # 专注时长（分钟）
    is_completed: bool
    created_at: datetime
```

### 4.2 提醒引擎 (ReminderEngine)

- **基于 QTimer 实现**，精确到秒级
- 每天 00:00 自动重置任务状态
- 两种提醒模式：
  - 固定时间点提醒：如每天 09:00
  - 间隔提醒：如每 25 分钟（番茄钟）
- 使用 `QSystemTrayIcon.showMessage()` 发送系统通知

### 4.3 番茄钟模块 (PomodoroTimer)

- 默认 25 分钟工作 + 5 分钟休息
- 可自定义时长
- 完成后自动记录统计

### 4.4 数据存储层 (DataStorage)

- 使用 Python 内置 `sqlite3` 模块
- 无需网络连接，完全本地
- 单文件数据库，便于备份

---

## 五、SQLite 数据库设计

```sql
-- 任务表
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT DEFAULT '未分类',
    type TEXT NOT NULL,           -- todo/habit/pomodoro
    reminder_time TEXT,           -- "HH:MM" 格式
    repeat_days TEXT,             -- JSON: "[0,1,2,3,4]"
    duration INTEGER DEFAULT 25, -- 番茄钟时长（分钟）
    is_enabled INTEGER DEFAULT 1, -- 是否启用
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 任务完成记录表（用于统计）
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    completed_at TIMESTAMP,
    duration_minutes INTEGER,     -- 实际专注时长
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- 分类表
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#3B82F6'  -- 分类颜色
);
```

---

## 六、界面设计

### 6.1 系统托盘菜单

```
┌─────────────────────────┐
│  📋 今日任务 (3/5)      │
├─────────────────────────┤
│  ✅ 投递简历 - 10:00    │
│  ⏳ 行测打卡 - 14:00    │
│  🍅 专注中 - 23:45      │
├─────────────────────────┤
│  🕐 计时器 ──────────── │
│  [▶ 开始] [⏸ 暂停]     │
├─────────────────────────┤
│  ───────────────────────│
│  📝 添加任务            │
│  📂 分类管理            │
│  📊 本周统计            │
│  ⚙️ 设置               │
├─────────────────────────┤
│  ❌ 退出程序            │
└─────────────────────────┘
```

### 6.2 主窗口（三栏布局）

```
┌──────────────────────────────────────────┐
│ 今日任务         │ 分类筛选  │ 统计概览   │
│ ─────────────── │ ──────── │ ──────── │
│ [求职] 投递简历  │ 💼 求职   │ 完成率 60% │
│ [学习] 刷行测题  │ 📚 学习   │ 专注 2.5h  │
│ [健康] 散步 30m  │ 🏃 健康   │ 连续 3 天  │
│ [学习] 🍅 专注中 │ ⚙️ 设置   │           │
│                 │          │           │
│ [+ 添加新任务]   │          │           │
└──────────────────────────────────────────┘
```

### 6.3 任务添加对话框

```
┌─────────────────────────────┐
│ 添加任务                     │
├─────────────────────────────┤
│ 任务名称: [______________] │
│ 任务类型: ○待办 ○打卡 ○专注 │
│ 所属分类: [求职 ▼]          │
│ 提醒时间: [09:00]           │
│ 重复周期: ☑一二三四五六日    │
│                              │
│ 专注时长: [25] 分钟          │
├─────────────────────────────┤
│        [取消]  [保存]       │
└─────────────────────────────┘
```

---

## 七、系统资源优化策略

| 优化项 | 实施方式 |
|--------|----------|
| **内存控制** | 单例模式管理状态，避免重复实例；数据库按需加载 |
| **CPU 占用** | QTimer 单次触发，非轮询；空闲 CPU < 0.1% |
| **启动速度** | 懒加载 UI；主窗口延迟初始化；启动 < 1 秒 |
| **后台运行** | 仅保留托盘图标；关闭后主窗口继续运行 |
| **数据库** | WAL 模式提升性能；定期 VACUUM；最大 < 1MB |

### 预期资源占用
- 空闲状态内存：20-30MB
- 运行状态内存：30-50MB
- CPU 平均占用：< 1%

---

## 八、实现复杂度评估

| 模块 | 复杂度 | 预估工时 |
|------|--------|----------|
| 项目脚手架 + 环境搭建 | ⭐ | 0.5 天 |
| SQLite 数据层（CRUD） | ⭐⭐ | 1 天 |
| 任务管理核心逻辑 | ⭐⭐ | 1 天 |
| 提醒引擎（QTimer + 通知） | ⭐⭐ | 1 天 |
| 番茄钟计时器 | ⭐ | 0.5 天 |
| 系统托盘 UI + 主窗口 | ⭐⭐⭐ | 2 天 |
| 任务/分类对话框 | ⭐⭐ | 1 天 |
| 统计功能 | ⭐⭐ | 0.5 天 |
| 打包分发（PyInstaller） | ⭐⭐ | 0.5 天 |
| 测试 + Bug 修复 | ⭐⭐ | 1 天 |

---

## 九、开发周期

| 阶段 | 时间 | 交付物 |
|------|------|--------|
| **MVP 版本** | 第 1 周 | 托盘应用 + 待办任务 + 定时提醒 |
| **完善版本** | 第 2 周 | 番茄钟 + 分类管理 + 统计功能 |
| **生产就绪** | 第 3 周 | 打包分发 + 全面测试 |

**总预估**：3 周（15 个工作日）

---

## 十、快速启动示例代码

### main.py
```python
import sys
from PySide6.QtWidgets import QApplication
from src.ui.tray_app import TrayApp
from src.core.data_storage import DataStorage
from src.core.task_manager import TaskManager
from src.core.reminder_engine import ReminderEngine

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出

    # 初始化各模块
    storage = DataStorage("data/tasks.db")
    task_manager = TaskManager(storage)
    reminder_engine = ReminderEngine(task_manager)

    # 创建托盘应用
    tray = TrayApp(task_manager, reminder_engine)
    tray.show()

    # 启动提醒引擎
    reminder_engine.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### requirements.txt
```
PySide6>=6.6.0
# 无需其他第三方库
# Python 标准库已包含：sqlite3, json, datetime, threading
```

---

## 十一、打包说明

使用 PyInstaller 打包：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包为单文件可执行程序
pyinstaller --onefile --windowed --name "DailyTaskTracker" main.py

# 输出位置
dist/DailyTaskTracker
```

### 打包后体积对比
- Python + PySide6：40-60MB
- Electron 应用：150-300MB

---

## 十二、参考资源

- [PySide6 官方文档](https://doc.qt.io/qtforpython-6/)
- [SQLite Python 文档](https://docs.python.org/3/library/sqlite3.html)
- [PyInstaller 指南](https://pyinstaller.org/)
