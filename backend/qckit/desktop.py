"""QCKit 桌面壳 —— PyInstaller 入口。

启动流程:
  1. 子线程跑 uvicorn (本地 127.0.0.1:8000, 只监听本机)
  2. 主线程等 1.5s 后自动打开默认浏览器
  3. 系统托盘常驻, 右键菜单可打开界面 / 数据目录 / 退出

用法:
  python -m qckit.desktop            # 开发调试
  pyinstaller ... qckit/desktop.py   # 打包 exe
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

APP_URL = "http://localhost:8000"
APP_HOST = "127.0.0.1"
APP_PORT = 8000


def _resource(rel: str) -> Path:
    """PyInstaller 打包后的资源路径."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).parent.parent / rel


def _run_server() -> None:
    """后台 uvicorn."""
    import uvicorn
    from .main import app
    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="warning")


def _open_browser_delayed() -> None:
    time.sleep(1.5)
    try:
        webbrowser.open(APP_URL)
    except Exception:
        pass


def _load_icon():
    """图标: assets/qckit.png -> PIL Image."""
    from PIL import Image, ImageDraw
    icon_path = _resource("assets/qckit.png")
    if icon_path.exists():
        return Image.open(icon_path)
    # 兜底: 生成一个简单的方形图标
    img = Image.new("RGB", (64, 64), (30, 64, 175))
    draw = ImageDraw.Draw(img)
    draw.rectangle([12, 12, 52, 52], fill=(255, 255, 255))
    draw.text((22, 20), "QC", fill=(30, 64, 175))
    return img


def _open_data_dir(icon, item) -> None:
    d = Path.home() / ".qckit"
    d.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(str(d))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(d)])
    else:
        subprocess.Popen(["xdg-open", str(d)])


def _open_ui(icon, item) -> None:
    webbrowser.open(APP_URL)


def _on_quit(icon, item) -> None:
    icon.stop()
    os._exit(0)  # 强制退出所有子线程


def main() -> None:
    # 1. 后端子线程 (daemon, 主退出即结束)
    threading.Thread(target=_run_server, daemon=True).start()

    # 2. 延迟开浏览器
    threading.Thread(target=_open_browser_delayed, daemon=True).start()

    # 3. 托盘 (阻塞主线程)
    import pystray
    from pystray import Menu, MenuItem

    icon = pystray.Icon(
        "qckit",
        _load_icon(),
        "QCKit · QCC 品管圈工具箱",
        menu=Menu(
            MenuItem("打开界面", _open_ui, default=True),
            MenuItem("打开数据目录", _open_data_dir),
            Menu.SEPARATOR,
            MenuItem(f"运行中 · {APP_URL}", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("退出 QCKit", _on_quit),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
