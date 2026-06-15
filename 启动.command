#!/bin/bash
# ============================================
# 📚 大学选课助手 — 一键启动脚本 (macOS)
# 双击即可运行，放在任何目录都支持
# ============================================

# 切换到脚本所在目录
cd "$(dirname "$0")" || { echo "❌ 无法进入项目目录"; exit 1; }
PROJECT_DIR="$(pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"

echo "========================================"
echo "📚 大学选课助手 — 启动中..."
echo "========================================"

# 检查 venv
if [ ! -f "$VENV_PYTHON" ]; then
    echo "📦 首次运行，正在创建虚拟环境..."
    python3 -m venv "$PROJECT_DIR/venv"
    "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q
    echo "✅ 环境准备完成！"
fi

# 设置 SSL 证书路径（解决 macOS SSL 问题）
export SSL_CERT_FILE=$("$VENV_PYTHON" -c "import certifi; print(certifi.where())" 2>/dev/null)
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

# 使用本地缓存的模型（无需联网下载）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

echo ""
echo "🚀 启动 Streamlit 应用..."
echo "   浏览器将自动打开"
echo "   如未自动打开，请访问: http://localhost:8501"
echo ""

# 延迟打开浏览器
(sleep 3 && open "http://localhost:8501") &

# 启动 Streamlit
"$VENV_PYTHON" -m streamlit run "$PROJECT_DIR/app.py" --server.port 8501

echo ""
echo "⚠️  应用已停止运行"
read -p "按回车键关闭此窗口..."
