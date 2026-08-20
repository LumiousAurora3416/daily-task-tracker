# 学习目标工作台

一个轻量、本地优先的学习目标执行工具。它把目标规划、每日打卡、番茄专注、数据看板和周复盘放在同一个工作台中，不需要账号或云端服务。

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](https://www.python.org/)
[![pywebview](https://img.shields.io/badge/Desktop-pywebview-2F6F4E.svg)](https://pywebview.flowrl.com/)
[![Storage](https://img.shields.io/badge/Storage-localStorage-E5A50A.svg)](#数据与隐私)

## 核心功能

- **目标管理**：设置目标名称、单位、总量、截止日期、颜色、阻碍与执行策略。
- **执行周期**：支持每天、工作日和自定义星期；非执行日不会被判定为漏打。
- **今日行动**：只展示当天应执行的目标，可记录完成量、专注分钟数、补记和休息日。
- **番茄钟联动**：从目标卡片直接开始专注，自定义工作与休息时长；专注完成后自动写入目标记录。
- **数据看板**：查看目标进度、连续完成情况、近 14 天完成量与专注时长。
- **周复盘**：汇总本周数据，记录保持事项、问题、尝试与下周计划，并生成可复制的周报文本。
- **本地备份**：所有数据保存在本机，可随时导出或导入 JSON。
- **响应式布局**：同一套界面适配桌面、平板和手机尺寸。

## 快速开始

### 桌面版（推荐）

当前桌面版主要在 macOS 上验证，运行时使用系统 WKWebView，不包含 Electron。

```bash
git clone https://github.com/LumiousAurora3416/daily-task-tracker.git
cd daily-task-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 desktop.py
```

`desktop.py` 会启动仅监听 `127.0.0.1` 的本地 HTTP 服务，再打开原生桌面窗口。默认端口为 `18923`。

### 浏览器版

不安装桌面依赖也可以直接运行工作台：

```bash
python3 -m http.server 18923
```

然后访问：

```text
http://127.0.0.1:18923/learning-dashboard.html
```

不建议通过 `file://` 直接打开 HTML。部分 WebView 和浏览器在该协议下无法稳定持久化 `localStorage`。

## 使用流程

1. 在「今日」页新建目标，并选择每天、工作日或自定义执行日。
2. 在当天目标卡片上直接打卡，或点击「专注」启动与该目标绑定的番茄钟。
3. 番茄钟完成后，专注分钟数会自动计入当天记录。
4. 在「看板」查看近 14 天趋势与单个目标进度。
5. 在「周报」完成复盘并复制生成的周报文本。
6. 在「我的」定期导出 JSON 备份。

## 技术架构

```text
desktop.py
  ├── 本地 HTTP 服务（127.0.0.1:18923）
  └── pywebview 原生窗口
          │
          ▼
learning-dashboard.html
  ├── HTML / CSS 响应式界面
  ├── 原生 JavaScript 状态与业务逻辑
  ├── 目标周期 / 打卡 / 番茄钟 / 看板 / 周报
  └── localStorage 本地持久化
```

工作台本身是一个无前端框架、无构建步骤的单文件应用。Python 层只负责桌面窗口、本地静态服务和打包环境适配，业务数据不会经过 Python 服务。

### 为什么使用 pywebview

- macOS 使用系统 WKWebView，避免携带完整 Chromium 运行时。
- 保留 HTML 工作台快速迭代和响应式适配的能力。
- 相比 Electron，安装体积与基础内存占用更低。
- 本地 HTTP origin 可让桌面版和浏览器版使用一致的数据机制。

## 数据与隐私

- 主存储键：`learning_dashboard_v1`
- 存储内容：目标、打卡记录、周报内容、备份提示状态和番茄钟配置
- 网络依赖：无
- 账号系统：无
- 数据同步：无

数据与访问 origin 绑定。桌面版会优先使用固定端口 `18923`；如果端口被占用，应用会临时切换端口，此时原端口下的数据不会显示。关闭占用程序并重新启动即可恢复。

建议通过「我的 → 导出」定期生成 JSON 备份。导入会覆盖当前数据，执行前请先导出。

## 项目结构

```text
daily-task-tracker/
├── learning-dashboard.html   # 当前主线：完整工作台界面与业务逻辑
├── desktop.py                # 当前主线：pywebview 桌面入口
├── requirements.txt          # Python 依赖
├── README.md
├── design_doc.md             # 原 PySide6 版本技术方案
├── main.py                   # 原 PySide6 版本入口（保留）
└── src/                      # 原 PySide6 版本源码（保留）
```

当前推荐入口是 `desktop.py`。`main.py` 与 `src/` 是早期 SQLite + PySide6 实现，仍保留在仓库中，但与当前工作台的 `localStorage` 数据相互独立。

## 兼容性

| 环境 | 状态 |
|------|------|
| macOS + WKWebView | 已验证 |
| Chrome / Safari 桌面浏览器 | 已验证 |
| Windows + Edge WebView2 | pywebview 支持，待完整验证 |
| Linux + GTK WebKit | pywebview 支持，待完整验证 |

## 路线图

- [x] 学习目标、量化进度与每日打卡
- [x] 番茄钟与目标记录联动
- [x] 近 14 天看板、目标详情与周报
- [x] 每天 / 工作日 / 自定义星期执行周期
- [x] JSON 导入导出与旧数据兼容
- [x] pywebview 桌面壳与 macOS 应用打包
- [ ] 暗色主题与交互动效优化
- [ ] 系统提醒通知
- [ ] Windows / Linux 完整测试与发行包

## 开发原则

- 本地优先，不引入不必要的在线服务。
- 保持单文件前端，不增加构建链路。
- 优先使用系统 WebView，控制桌面端资源占用。
- 变更数据结构时保持旧数据向后兼容。
