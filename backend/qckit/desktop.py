"""QCKit 桌面壳 —— PyInstaller 入口.

启动流程:
  1. 子线程跑 uvicorn (本地 127.0.0.1:8000, 只监听本机)
  2. 主线程等 1.5s 后自动打开默认浏览器
  3. 系统托盘常驻, 右键菜单可打开界面 / 数据目录 / 退出

日志:
  所有 stdout/stderr 重定向到 %USERPROFILE%\\.qckit\\qckit.log
  用户报告 bug 时把这个文件发过来即可定位。
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

APP_URL = "http://localhost:8000"
APP_HOST = "127.0.0.1"
APP_PORT = 8000

# ────────────────────────────────────────────────────────
# 日志重定向: --windowed 模式下 stdout/stderr 是 None,
# 未接管会导致 print / traceback 直接崩溃
# ────────────────────────────────────────────────────────
_DATA_DIR = Path.home() / ".qckit"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_LOG_PATH = _DATA_DIR / "qckit.log"

def _install_logging() -> None:
    """把 stdout/stderr 重定向到日志文件, 保证 windowed 模式不崩."""
    try:
        f = open(_LOG_PATH, "a", encoding="utf-8", buffering=1)
        sys.stdout = f
        sys.stderr = f
        print(f"\n{'='*60}\n[qckit] started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}", flush=True)
    except Exception:
        pass  # 权限不够就算了, 至少托盘还能起


def _resource(rel: str) -> Path:
    """PyInstaller 打包后的资源路径."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).parent.parent / rel


def _run_server() -> None:
    """后台 uvicorn, 异常写日志."""
    try:
        import uvicorn
        from .main import app
        # log_level=info 让请求日志也进 qckit.log, 方便定位 500/404
        uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")
    except Exception:
        print("[qckit] uvicorn 崩溃:", flush=True)
        traceback.print_exc()


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


def _open_log(icon, item) -> None:
    if _LOG_PATH.exists():
        if sys.platform == "win32":
            os.startfile(str(_LOG_PATH))  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(_LOG_PATH)])
        else:
            subprocess.Popen(["xdg-open", str(_LOG_PATH)])


def _on_quit(icon, item) -> None:
    icon.stop()
    os._exit(0)  # 强制退出所有子线程


def main() -> None:
    _install_logging()   # 先接管 stdout/stderr, 之后所有崩溃都进日志
    try:
        _main_body()
    except Exception:
        print("[qckit] 主流程崩溃:", flush=True)
        traceback.print_exc()
        # 让日志刷盘再退出, 保证 qckit.log 里能看到 traceback
        time.sleep(0.5)
        raise


def _main_body() -> None:
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
            MenuItem("查看日志", _open_log),
            Menu.SEPARATOR,
            MenuItem(f"运行中 · {APP_URL}", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("退出 QCKit", _on_quit),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
