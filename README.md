# 每日任务管理 · Daily Task Tracker

> 一款轻量级、本地优先的桌面任务管理工具，集任务管理、定时提醒、番茄专注、习惯打卡于一体。常驻系统托盘，零网络依赖。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#51-兼容性)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#许可证)

## ✨ 特性

- **多类型任务一体化** — 待办事项 / 习惯打卡 / 番茄专注，三种任务类型统一管理
- **定时提醒** — 按 `HH:MM` + 重复周期触发系统通知，跨日自动重置
- **番茄钟计时** — 工作 / 休息循环，完成自动记录专注时长
- **分类管理** — 自定义分类与颜色，按分类筛选任务
- **统计概览** — 今日完成率、专注时长、连续打卡天数、近 7 天趋势
- **系统托盘常驻** — 关闭主窗口后台运行，单击托盘图标呼出
- **本地存储** — SQLite 单文件数据库，零网络依赖，数据隐私可控
- **轻量** — 单进程运行，无 Electron，无 Web 引擎

## 🖥 界面预览

```
┌──────────────────────────────────────────────────┐
│ 今日任务           │ 分类筛选   │ 统计概览        │
│ ─────────────────  │ ─────────  │ ────────────── │
│ ✅ [求职/待办] ... │ 全部       │ 完成率 60%      │
│ ▢  [学习/打卡] ... │ 求职       │ 已完成 3 / 5    │
│ ▢  [健康/待办] ... │ 学习       │ 今日专注 2.5h   │
│                    │ 健康       │ 连续打卡 3 天   │
│ [+ 添加] [完成] ...│ [管理分类] │ ────────────── │
│                    │            │ 近 7 天         │
│ ┌─ 专注番茄钟 ───┐ │            │ 08-08 完成 3   │
│ │   25:00        │ │            │ 08-07 完成 5   │
│ │  工作中 · 写代码│ │            │ ...            │
│ │ [开始][休息][停]│ │            │                │
│ └────────────────┘ │            │                │
└──────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.9 或更高版本
- macOS 13+ / Windows 10+ / Linux（X11 或 Wayland）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/LumiousAurora3416/daily-task-tracker.git
cd daily-task-tracker

# 2. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动应用
python main.py
```

首次启动会在 `data/` 目录下自动创建 `tasks.db` 数据库，并预置「未分类 / 求职 / 学习 / 健康」四个默认分类。

## 📖 使用指南

### 添加任务

1. 点击托盘图标或主窗口的「＋ 添加任务」
2. 填写任务名称（必填）
3. 选择任务类型：
   - **待办** — 一次性或周期性事项
   - **打卡** — 习惯养成，每日打卡计入连续天数
   - **专注** — 需要番茄钟计时的工作
4. 选择分类、设置提醒时间与重复周期
5. 保存

### 番茄专注

1. 在任务列表中选中一个「专注」类型任务
2. 点击番茄钟区的「开始工作」
3. 计时器按任务设置的时长倒数（默认 25 分钟）
4. 完成后自动记录专注时长到该任务，今日统计实时更新
5. 可继续点击「开始休息」进入 5 分钟休息

### 系统托盘

| 操作 | 行为 |
|------|------|
| 单击 / 双击托盘图标 | 显示主窗口 |
| 右键托盘图标 | 菜单：打开主窗口 / 添加任务 / 今日统计 / 退出 |
| 关闭主窗口 | 隐藏到托盘，应用继续运行 |
| 到点提醒 | 弹出系统通知 |

## 🏗 项目结构

```
daily-task-tracker/
├── main.py                      # 程序入口
├── requirements.txt             # 依赖列表
├── design_doc.md                # 技术方案文档
├── src/
│   ├── core/                    # 核心业务逻辑
│   │   ├── data_storage.py      # SQLite 数据持久化
│   │   ├── task_manager.py      # 任务管理
│   │   ├── reminder_engine.py   # 提醒引擎（QTimer）
│   │   └── pomodoro_timer.py    # 番茄钟计时器
│   ├── ui/                      # 界面层
│   │   ├── tray_app.py          # 系统托盘
│   │   ├── main_window.py       # 主窗口（三栏布局）
│   │   ├── task_dialog.py       # 任务编辑对话框
│   │   └── category_dialog.py   # 分类管理对话框
│   └── utils/
│       └── constants.py         # 常量定义
└── data/                        # 运行时自动创建
    └── tasks.db                 # SQLite 数据库
```

## 🛠 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 语言 | Python 3.9+ | 标准库 sqlite3 / json / datetime |
| GUI | PySide6 (Qt6) | 原生系统托盘，LGPL 友好 |
| 存储 | SQLite | WAL 模式，单文件，零配置 |
| 打包 | PyInstaller | v2.0 规划，生成独立可执行文件 |

### 为什么选 PySide6 而不是 Electron？

- Electron 基础内存 ≥ 150MB，PySide6 实测约 100MB（打包后可降至 60MB 以下）
- 启动速度更快，原生系统集成更好
- 无需 Node.js 运行时

## 📊 资源占用

| 指标 | 实测值 |
|------|--------|
| 进程数 | 1（无子进程） |
| 运行内存（RSS） | ~100 MB |
| CPU 空闲占用 | < 1% |
| 数据库体积 | < 100 KB（初期） |

## 🗺 路线图

- [x] **v1.0 MVP** — 任务管理 + 番茄钟 + 提醒 + 分类 + 统计 + 托盘
- [ ] **v1.1 体验增强** — 优先级、子任务、暗色主题、提醒音效
- [ ] **v1.2 可视化与备份** — 浮动番茄钟、托盘倒计时、JSON 导入导出、统计图表
- [ ] **v2.0 分发就绪** — PyInstaller 打包、macOS .dmg / Windows .exe、开机自启、全局快捷键

## 📝 文档

- [design_doc.md](./design_doc.md) — 技术实现方案

## 🤝 贡献

欢迎提 Issue 和 Pull Request。开发前请先阅读 [design_doc.md](./design_doc.md) 了解技术方案。

## 📄 许可证

MIT License — 详见 [LICENSE](./LICENSE)。
