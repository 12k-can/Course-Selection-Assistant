@echo off
chcp 65001 >nul
title 📚 大学选课助手

REM ============================================
REM 📚 大学选课助手 — 一键启动脚本 (Windows)
REM 双击即可运行，放在任何目录都支持
REM ============================================

echo ========================================
echo 📚 大学选课助手 — 启动中...
echo ========================================
echo.

REM 进入脚本所在目录
cd /d "%~dp0"

REM 检查 venv
if not exist "venv\Scripts\python.exe" (
    echo 📦 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\pip install -r requirements.txt -q
    echo ✅ 环境准备完成！
    echo.
)

REM 使用本地缓存的模型（无需联网下载）
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

echo 🚀 启动 Streamlit 应用...
echo    浏览器将自动打开
echo    如未自动打开，请访问: http://localhost:8501
echo.

REM 启动 Streamlit
call venv\Scripts\streamlit run app.py --server.port 8501

echo.
echo ⚠️  应用已停止运行
pause
