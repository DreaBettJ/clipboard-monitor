#!/usr/bin/env python3
"""
剪切板监控工具
- 监控剪切板内容
- 检测 curl 请求并替换域名
- 支持配置多个域名替换规则
- 开机自启动
"""

import os
import re
import json
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime

# 配置目录
CONFIG_DIR = Path.home() / ".config" / "clipboard-monitor"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "clipboard.log"

# 默认配置
DEFAULT_CONFIG = {
    "rules": [
        {"pattern": "dev.huilianyi.com", "replace": "{{local-dev-host}}"},
        {"pattern": "uat.huilianyi.com", "replace": "{{local-uat-host}}"},
        {"pattern": "pro.huilianyi.com", "replace": "{{local-pro-host}}"},
    ],
    "use_regex": False,
    "match_prefix": "curl",
    "enabled": True,
    "notifications": True,
    "check_interval": 1.0,  # 秒
}

# 历史记录
last_clipboard = ""
processed_requests = []  # 已处理的请求


def load_config() -> dict:
    """加载配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """保存配置"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_clipboard() -> str:
    """获取剪切板内容"""
    try:
        # 尝试使用 xclip
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=1
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    
    try:
        # 备选方案: xsel
        result = subprocess.run(
            ["xsel", "--clipboard", "-o"],
            capture_output=True, text=True, timeout=1
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    
    return ""


def set_clipboard(text: str):
    """设置剪切板内容"""
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-i"],
            input=text, text=True, timeout=1
        )
    except Exception:
        try:
            subprocess.run(
                ["xsel", "--clipboard", "-i"],
                input=text, text=True, timeout=1
            )
        except Exception:
            pass


def is_match_request(text: str, prefixes: list) -> bool:
    """检测是否匹配配置的前缀"""
    text_lower = text.strip().lower()
    for prefix in prefixes:
        prefix = prefix.strip().lower()
        if prefix and text_lower.startswith(prefix):
            return True
    return False


def process_curl(text: str, rules: list, use_regex: bool = False) -> str:
    """处理 curl 请求，替换域名"""
    result = text
    
    for rule in rules:
        pattern = rule.get("pattern", "")
        replace = rule.get("replace", "")
        
        if pattern and replace:
            if use_regex:
                # 正则表达式模式：直接使用用户提供的 pattern 作为正则
                try:
                    result = re.sub(
                        rf"(https?://){pattern}(/[^'\" ]*)?",
                        rf"\1{replace}\2",
                        result, flags=re.IGNORECASE
                    )
                    # 也处理 curl 命令中的 URL
                    result = re.sub(
                        rf"(curl\s+['\"])(https?://){pattern}(/[^'\" ]*)?(['\"])",
                        rf"\1\2{replace}\3\4",
                        result, flags=re.IGNORECASE
                    )
                except re.error as e:
                    log(f"正则表达式错误: {e}, pattern: {pattern}")
            else:
                # 普通字符串模式
                # 检查 pattern 是否以 https?:// 开头
                if pattern.startswith("https://") or pattern.startswith("http://"):
                    # 完整 URL 模式，替换后不带 protocol
                    protocol = "https://" if pattern.startswith("https://") else "http://"
                    domain_path = pattern[len(protocol):]
                    escaped_pattern = re.escape(domain_path)
                    # 替换 URL（去掉 protocol）
                    # (curl\s+['\"]) 是 group 1, (/[^'\" ]*)? 是 group 2, (['\"]) 是 group 3
                    result = re.sub(
                        rf"(curl\s+['\"]){protocol}{escaped_pattern}(/[^'\" ]*)?(['\"])",
                        rf"\1{replace}\2\3",
                        result, flags=re.IGNORECASE
                    )
                    # 去掉 protocol 的替换
                    result = re.sub(
                        rf"{protocol}{escaped_pattern}(/[^'\" ]*)?",
                        rf"{replace}\1",
                        result, flags=re.IGNORECASE
                    )
                else:
                    # 纯域名模式（原有逻辑）
                    escaped_pattern = re.escape(pattern)
                    # 替换 URL 中的域名
                    # 处理 curl 'http://xxx' 或 curl "http://xxx" 格式（支持带或不带尾部斜杠）
                    result = re.sub(
                        rf"(curl\s+['\"])(https?://){escaped_pattern}(/[^'\" ]*)?(['\"])",
                        rf"\1\2{replace}\3\4",
                        result, flags=re.IGNORECASE
                    )
                    # 处理 -H 'Host: xxx' 格式
                    result = re.sub(
                        rf"(-H\s+['\"]Host:\s*){escaped_pattern}(['\"])",
                        rf"\1{replace}\2",
                        result, flags=re.IGNORECASE
                    )
                    # 处理直接的 URL 替换（https://dev.huilianyi.com 或 https://dev.huilianyi.com/xxx）
                    result = re.sub(
                        rf"(https?://){escaped_pattern}(/[^'\" ]*)?",
                        rf"\1{replace}\2",
                        result, flags=re.IGNORECASE
                    )
    
    return result


def send_notification(title: str, message: str):
    """发送桌面通知"""
    try:
        subprocess.run([
            "notify-send", "-i", "dialog-information", title, message
        ], timeout=5)
    except Exception:
        pass


def log(message: str):
    """记录日志"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_line)
    
    print(log_line.strip())


def monitor_clipboard():
    """监控剪切板"""
    global last_clipboard, processed_requests
    
    config = load_config()
    
    if not config.get("enabled", True):
        log("监控已禁用")
        return
    
    rules = config.get("rules", [])
    check_interval = config.get("check_interval", 1.0)
    notifications = config.get("notifications", True)
    use_regex = config.get("use_regex", False)
    match_prefix = config.get("match_prefix", "curl")
    prefixes = [p.strip() for p in match_prefix.split(",") if p.strip()]
    
    log(f"开始监控剪切板 (间隔: {check_interval}秒)")
    
    while True:
        try:
            current = get_clipboard()
            
            # 检查新内容
            if current and current != last_clipboard:
                last_clipboard = current
                
                # 检测 curl 请求
                if is_match_request(current, prefixes):
                    log("检测到 curl 请求")
                    
                    # 检查是否已处理
                    if current not in processed_requests:
                        # 替换域名
                        processed = process_curl(current, rules, use_regex)
                        
                        # 记录
                        processed_requests.append(current)
                        log(f"已处理 curl 请求")
                        log(f"原始: {current[:100]}...")
                        log(f"替换后: {processed[:100]}...")
                        
                        # 替换剪切板
                        set_clipboard(processed)
                        
                        # 发送通知
                        if notifications:
                            send_notification(
                                "✅ curl 请求已转换",
                                "域名已替换为本地环境变量"
                            )
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            log("监控停止")
            break
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(5)


def show_config():
    """显示当前配置"""
    config = load_config()
    print("\n=== 剪切板监控配置 ===")
    print(json.dumps(config, indent=2))
    return config


def add_rule(pattern: str, replace: str):
    """添加替换规则"""
    config = load_config()
    config["rules"].append({"pattern": pattern, "replace": replace})
    save_config(config)
    print(f"已添加规则: {pattern} -> {replace}")


def remove_rule(pattern: str):
    """删除替换规则"""
    config = load_config()
    config["rules"] = [r for r in config["rules"] if r["pattern"] != pattern]
    save_config(config)
    print(f"已删除规则: {pattern}")


def install_autostart():
    """安装开机自启动"""
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = autostart_dir / "clipboard-monitor.desktop"
    
    script_path = Path(__file__).resolve()
    
    content = f"""[Desktop Entry]
Type=Application
Name=Clipboard Monitor
Exec={script_path} --daemon
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    
    with open(desktop_file, "w") as f:
        f.write(content)
    
    print(f"✅ 已安装开机自启动: {desktop_file}")


def remove_autostart():
    """移除开机自启动"""
    desktop_file = Path.home() / ".config" / "autostart" / "clipboard-monitor.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        print("✅ 已移除开机自启动")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--daemon":
            monitor_clipboard()
        elif cmd == "--config":
            show_config()
        elif cmd == "--add":
            if len(sys.argv) >= 4:
                add_rule(sys.argv[2], sys.argv[3])
            else:
                print("用法: --add <pattern> <replace>")
        elif cmd == "--remove":
            if len(sys.argv) >= 3:
                remove_rule(sys.argv[2])
            else:
                print("用法: --remove <pattern>")
        elif cmd == "--enable-autostart":
            install_autostart()
        elif cmd == "--disable-autostart":
            remove_autostart()
        else:
            print("用法:")
            print("  python clipboard-monitor.py --daemon      # 启动监控")
            print("  python clipboard-monitor.py --config      # 查看配置")
            print("  python clipboard-monitor.py --add <p> <r>  # 添加规则")
            print("  python clipboard-monitor.py --remove <p>    # 删除规则")
            print("  python clipboard-monitor.py --enable-autostart   # 开机自启")
            print("  python clipboard-monitor.py --disable-autostart # 关闭自启")
    else:
        show_config()
