#!/bin/bash

# ============================================
# 📚 大学选课助手 — 一键启动脚本
# ============================================

# 获取脚本所在目录（支持双击运行）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "📚 大学选课助手 — 启动中..."
echo "========================================"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  未找到虚拟环境，尝试直接运行..."
fi

echo ""
echo "🚀 启动 Streamlit 应用..."
echo "   应用将在浏览器中自动打开"
echo "   如未自动打开，请访问: http://localhost:8501"
echo ""

# 启动 Streamlit 并自动打开浏览器
streamlit run app.py --server.headless true

# 如果 Streamlit 退出，暂停以便查看错误信息
echo ""
echo "⚠️  应用已停止运行"
read -p "按回车键关闭此窗口..."
