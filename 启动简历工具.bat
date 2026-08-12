@echo off
title 简历定制工具 - 启动器
chcp 65001 >nul 2>&1
setlocal

cd /d "%~dp0"
set "APP_DIR=%CD%"
set "URL=http://127.0.0.1:8765"

rem ===== 清理残留：结束占用 8765 端口的进程（上次异常关闭可能残留，导致启动失败）=====
echo [准备] 检查并清理残留服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
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

rem ===== 等待服务就绪（最多 30 秒）=====
set /a tries=0
:waitloop
rem timeout 在个别环境可能直接返回，失败时用 ping 延时兜底
timeout /t 1 /nobreak >nul 2>&1 || ping -n 2 127.0.0.1 >nul 2>&1
rem 优先 HTTP 探测（能确认服务真正可访问）；无 curl 时退回端口检测
curl -s -o nul "%URL%/" >nul 2>&1
if not errorlevel 1 goto ready
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% lss 30 goto waitloop

echo [错误] 服务启动超时，请查看服务窗口中的报错信息。
pause
exit /b 1

:ready
echo [成功] 工具已启动，正在打开浏览器...
start "" "%URL%"
timeout /t 1 /nobreak >nul 2>&1
exit /b 0
