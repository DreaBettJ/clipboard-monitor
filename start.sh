#!/bin/bash
# 剪贴板监控启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 依赖检查
if ! command -v xclip >/dev/null 2>&1 && ! command -v xsel >/dev/null 2>&1; then
    echo "❌ 错误: 缺少剪贴板工具 (xclip 或 xsel)"
    echo "   请运行: sudo apt install xclip"
    exit 1
fi

cd "$SCRIPT_DIR"

# 后台启动监控
nohup python3 clipboard_monitor.py > /tmp/clipboard-monitor.log 2>&1 &
echo "监控已启动: $!"

# 启动 Web 管理界面
nohup python3 web_manager.py > /tmp/clipboard-web.log 2>&1 &
echo "Web界面已启动: http://localhost:5000"
