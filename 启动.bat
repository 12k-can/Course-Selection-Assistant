@echo off
chcp 65001 >nul

REM ============================================
REM 📚 大学选课助手 — 一键启动脚本 (Windows)
REM ============================================

echo ========================================
echo 📚 大学选课助手 — 启动中...
echo ========================================
echo.

REM 进入脚本所在目录
cd /d "%~dp0"

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  未找到虚拟环境，尝试直接运行...
)
echo.

echo 🚀 启动 Streamlit 应用...
echo    应用将在浏览器中自动打开
echo    如未自动打开，请访问: http://localhost:8501
echo.

REM 启动 Streamlit
streamlit run app.py

echo.
echo ⚠️  应用已停止运行
pause
