#!/bin/bash
# 剪贴板监控管理脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="/usr/bin/python3"
LOG_DIR="/tmp"

action="$1"

case "$action" in
    start)
        echo "🚀 启动剪贴板监控..."
        
        # 激活虚拟环境
        # 使用系统 python
        
        # 后台启动监控
        nohup python3 "$SCRIPT_DIR/clipboard_monitor.py" > "$LOG_DIR/clipboard-monitor.log" 2>&1 &
        echo "✅ 监控已启动 (PID: $!)"
        
        # 后台启动 Web 界面
        nohup python3 "$SCRIPT_DIR/web_manager.py" > "$LOG_DIR/clipboard-web.log" 2>&1 &
        echo "✅ Web界面已启动: http://localhost:5000"
        
        echo ""
        echo "📝 日志查看:"
        echo "   监控: tail -f $LOG_DIR/clipboard-monitor.log"
        echo "   Web:  tail -f $LOG_DIR/clipboard-web.log"
        ;;
        
    stop)
        echo "🛑 停止剪贴板监控..."
        pkill -f "clipboard_monitor.py" && echo "✅ 监控已停止"
        pkill -f "web_manager.py" && echo "✅ Web界面已停止"
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if pgrep -f "clipboard_monitor.py" > /dev/null; then
            echo "✅ 监控: 运行中"
        else
            echo "❌ 监控: 未运行"
        fi
        
        if pgrep -f "web_manager.py" > /dev/null; then
            echo "✅ Web界面: 运行中"
        else
            echo "❌ Web界面: 未运行"
        fi
        ;;
        
    install)
        echo "📦 安装 systemd 服务..."
        
        # 复制服务文件
        sudo cp "$SCRIPT_DIR/clipboard-monitor.service" /etc/systemd/system/
        
        # 重载 systemd
        sudo systemctl daemon-reload
        
        # 启用开机自启动
        sudo systemctl enable clipboard-monitor
        
        echo "✅ 已安装并启用开机自启动"
        echo ""
        echo "使用方法:"
        echo "   sudo systemctl start clipboard-monitor   # 启动"
        echo "   sudo systemctl stop clipboard-monitor    # 停止"
        echo "   sudo systemctl status clipboard-monitor  # 状态"
        ;;
        
    uninstall)
        echo "🗑️ 卸载 systemd 服务..."
        sudo systemctl stop clipboard-monitor 2>/dev/null
        sudo systemctl disable clipboard-monitor 2>/dev/null
        sudo rm /etc/systemd/system/clipboard-monitor.service 2>/dev/null
        sudo systemctl daemon-reload
        echo "✅ 已卸载"
        ;;
        
    log)
        echo "📝 监控日志 (Ctrl+C 退出):"
        tail -f "$LOG_DIR/clipboard-monitor.log"
        ;;
        
    web-log)
        echo "📝 Web日志 (Ctrl+C 退出):"
        tail -f "$LOG_DIR/clipboard-web.log"
        ;;
        
    *)
        echo "用法: $0 {start|stop|restart|status|install|uninstall|log|web-log}"
        echo ""
        echo "  start      - 启动监控和Web界面"
        echo "  stop       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  status     - 查看运行状态"
        echo "  install    - 安装并启用开机自启动"
        echo "  uninstall  - 卸载服务"
        echo "  log        - 查看监控日志"
        echo "  web-log    - 查看Web日志"
        ;;
esac
