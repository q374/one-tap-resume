@echo off
title 简历定制工具 - 启动器
setlocal

cd /d "%~dp0"
set "APP_DIR=%CD%"
set "URL=http://127.0.0.1:8765"

rem ===== 检查服务是否已在运行 =====
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [提示] 工具已在运行，正在打开浏览器...
    start "" "%URL%"
    exit /b
)

rem ===== 检查 Python =====
set "PY_CMD=python"
where python >nul 2>&1
if errorlevel 1 (
    set "PY_CMD=py"
    where py >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到 Python，请先安装 Python 并勾选 Add to PATH。
        pause
        exit /b 1
    )
)

echo.
echo   ============================================
echo      简历定制工具  正在启动，请稍候...
echo      请勿关闭弹出的服务窗口（关掉即停止服务）
echo   ============================================
echo.

start "简历定制工具 - 关闭此窗口即停止服务" cmd /k "%PY_CMD% app.py"

rem ===== 等待服务就绪（最多 25 秒） =====
set /a tries=0
:waitloop
timeout /t 1 /nobreak >nul
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% lss 25 goto waitloop

echo [错误] 服务启动超时，请查看服务窗口中的报错信息。
pause
exit /b 1

:ready
echo [成功] 工具已启动，正在打开浏览器...
start "" "%URL%"
timeout /t 1 /nobreak >nul
exit /b 0
