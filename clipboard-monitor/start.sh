#!/bin/bash
# 剪贴板监控启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="/home/lijiang/.openclaw/workspace/Mini-Agent/.venv/bin"

# 激活虚拟环境并启动
source "$VENV_PATH/activate"

cd "$SCRIPT_DIR"

# 后台启动监控
nohup python clipboard_monitor.py > /tmp/clipboard-monitor.log 2>&1 &
echo "监控已启动: $!"

# 启动 Web 管理界面
nohup python web_manager.py > /tmp/clipboard-web.log 2>&1 &
echo "Web界面已启动: http://localhost:5000"
