@echo off
REM ═══════════════════════════════════════════════════════════
REM  QCKit 一键启动脚本 (Windows · 需先装 Docker Desktop)
REM ═══════════════════════════════════════════════════════════
setlocal
cd /d "%~dp0"

echo.
echo   ╔═══════════════════════════════════════════╗
echo   ║   QCKit · QCC 品管圈工具箱 · 启动中...    ║
echo   ╚═══════════════════════════════════════════╝
echo.

REM 检查 Docker 是否已装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker Desktop
    echo.
    echo 请先安装: https://www.docker.com/products/docker-desktop
    echo 装好后重新运行本脚本
    pause
    exit /b 1
)

REM 检查 docker daemon 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Desktop 未启动
    echo 请打开 Docker Desktop 后再运行本脚本
    pause
    exit /b 1
)

REM 启动 (首次自动 build)
docker compose up -d --build
if errorlevel 1 (
    echo [错误] 启动失败, 查看上方输出
    pause
    exit /b 1
)

echo.
echo   ✓ QCKit 已启动
echo.
echo   浏览器打开: http://localhost:8000
echo   数据目录:   %CD%\data
echo.
echo   停止服务:   qckit-stop.bat
echo   查看日志:   docker compose logs -f qckit
echo.

REM 等 3 秒后自动开浏览器
timeout /t 3 /nobreak >nul
start http://localhost:8000

pause
