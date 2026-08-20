#!/usr/bin/env python3
"""学习目标工作台 · 桌面壳

用 pywebview 包装 learning-dashboard.html 为桌面应用。
macOS 上使用原生 WKWebView，内存约 80MB。

通过本地 HTTP 服务器加载 HTML，确保 localStorage 正常持久化。
（file:// 协议在 WKWebView 里 localStorage 不可靠）

用法：
    pip install pywebview
    python desktop.py
"""
import http.server
import os
import socketserver
import socket
import sys
import threading

import webview


def get_base_dir():
    """兼容 PyInstaller 打包：资源目录优先 _MEIPASS（打包临时解压），否则用源码目录"""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
HTML_FILE = os.path.join(BASE_DIR, "learning-dashboard.html")
DEFAULT_PORT = 18923  # 优先默认端口，保持 localStorage origin 稳定
PORT_RANGE_END = 18950  # 端口占用时的探测上限

# 需要预创建的 WKWebView 数据目录（macOS），缺则 localStorage/IndexedDB 报权限错
_WEBKIT_SUBDIRS = [
    "LocalStorage",
    "IndexedDB",
    "MediaKeys/v1",
    "DeviceIdHashSalts",
    "ResourceLoadStatistics",
    "Default",
    "SearchHistory",
    "ServiceWorkerRegistrations",
]


def ensure_webkit_dirs():
    """确保 macOS WKWebView 数据目录存在，避免 localStorage 持久化权限错误"""
    if not sys.platform.startswith("darwin"):
        return
    base = os.path.join(
        os.path.expanduser("~"),
        "Library", "WebKit", "com.apple.python3", "WebsiteData",
    )
    for d in _WEBKIT_SUBDIRS:
        path = os.path.join(base, d)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            print(f"[warn] 无法创建 WebKit 目录 {path}: {e}", file=sys.stderr)


def find_port(start=DEFAULT_PORT, end=PORT_RANGE_END):
    """找可用端口，优先默认端口。返回 (port, changed)"""
    for p in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", p))
            if p == start:
                return p, False
            return p, True
        except OSError:
            continue
    raise RuntimeError(f"端口 {start}-{end} 全部被占用，请关闭占用程序后重试")


def start_http_server(port):
    """启动本地 HTTP 服务器提供 HTML 文件"""
    handler = lambda *args, **kw: http.server.SimpleHTTPRequestHandler(
        *args, directory=BASE_DIR, **kw
    )
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    if not os.path.exists(HTML_FILE):
        print(f"错误：找不到 {HTML_FILE}")
        sys.exit(1)

    # F16: 首次运行自动初始化 WKWebView 数据目录
    ensure_webkit_dirs()

    # F16: 端口占用容错（默认端口不可用时换端口 + 提示 localStorage 风险）
    port, changed = find_port()
    if changed:
        print(
            f"[warn] 默认端口 {DEFAULT_PORT} 被占用，改用 {port}。"
            "警告：端口变更导致 localStorage origin 变化，历史数据将不可见。"
            "建议关闭占用程序后重新启动。",
            file=sys.stderr,
        )

    # 启动本地 HTTP 服务器（localStorage 需要 http origin 才能持久化）
    httpd = start_http_server(port)
    url = f"http://127.0.0.1:{port}/learning-dashboard.html"

    webview.create_window(
        title="学习目标工作台",
        url=url,
        width=1100,
        height=750,
        min_size=(800, 600),
        text_select=False,
    )
    # private_mode=False 让 WKWebView 持久化 localStorage 到磁盘
    webview.start(debug=False, private_mode=False)

    # 窗口关闭后停止 HTTP 服务器
    httpd.shutdown()


if __name__ == "__main__":
    main()
