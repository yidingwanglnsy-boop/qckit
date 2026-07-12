@echo off
REM QCKit 停止脚本
setlocal
cd /d "%~dp0"

echo 正在停止 QCKit...
docker compose down

if errorlevel 1 (
    echo [错误] 停止失败
    pause
    exit /b 1
)

echo.
echo   ✓ 已停止 (数据保留在 %CD%\data)
echo.
pause
