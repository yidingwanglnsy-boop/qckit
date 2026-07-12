"""PyInstaller 构建脚本 (Windows) —— 单文件 exe · 无控制台 · 含图标.

用法 (在 Windows 上运行, 或 GitHub Actions windows-latest):
  1. cd frontend && npm ci && npm run build      # 前端产物落到 backend/static
  2. cd backend && pip install -e ".[build]"     # 装 pyinstaller + pystray + pillow
  3. python build_windows.py                     # 打包
  产物: dist/QCKit.exe (双击运行, 无黑框, 系统托盘)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent   # 仓库根 (脚本就在根目录)
BACKEND = ROOT / "backend"
FRONT_DIST = BACKEND / "static"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"


def check_prereqs() -> None:
    if not FRONT_DIST.exists() or not (FRONT_DIST / "index.html").exists():
        sys.exit(
            "[ERROR] frontend not built: missing backend/static/index.html\n"
            "run first: cd frontend && npm ci && npm run build")
    if not (ASSETS / "qckit.ico").exists():
        sys.exit(f"[ERROR] missing icon {ASSETS / 'qckit.ico'}")


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)

    # PyInstaller: 单文件, windowed (无 cmd 黑框), 带图标
    # add-data 分隔符: Windows ';', Linux/Mac ':'
    sep = ";" if sys.platform == "win32" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "QCKit",
        f"--icon={ASSETS / 'qckit.ico'}",
        f"--add-data={FRONT_DIST}{sep}backend/static",
        f"--add-data={ASSETS / 'qckit.png'}{sep}assets",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import=uvicorn.loops.asyncio",
        "--hidden-import=pystray._win32",  # Windows 托盘后端
        "--collect-submodules=qckit",
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(BACKEND / "qckit" / "desktop.py"),
    ]
    print("[build] $ " + " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(BACKEND))
    print(f"\n[OK] build done: {DIST / 'QCKit.exe'}")


if __name__ == "__main__":
    check_prereqs()
    build()
