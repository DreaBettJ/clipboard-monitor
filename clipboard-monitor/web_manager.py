#!/usr/bin/env python3
"""剪切板监控 - Web管理界面 (简化版)"""

import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# 添加主脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from clipboard_monitor import load_config, save_config

CONFIG_FILE = SCRIPT_DIR.parent / ".config" / "clipboard-monitor" / "config.json"

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>剪切板监控 - 管理界面</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { font-size: 16px; color: #666; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; font-size: 14px; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        input[type="checkbox"] { width: 20px; height: 20px; }
        button { background: #007aff; color: white; border: none; padding: 10px 20px; 
                 border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 10px; }
        button:hover { background: #0056b3; }
        button.danger { background: #ff3b30; }
        button.danger:hover { background: #d63028; }
        .rule-item { display: flex; align-items: center; gap: 10px; padding: 10px; 
                     background: #f9f9f9; border-radius: 4px; margin-bottom: 10px; }
        .rule-item .pattern { flex: 1; font-weight: 500; }
        .rule-item .replace { flex: 1; color: #007aff; }
        .rule-item .delete { color: #ff3b30; cursor: pointer; font-weight: bold; }
        .status { display: flex; align-items: center; gap: 10px; }
        .status .dot { width: 10px; height: 10px; border-radius: 50%; background: #34c759; }
        .status .dot.stopped { background: #ff3b30; }
        .add-form { display: flex; gap: 10px; margin-top: 15px; }
        .add-form input { flex: 1; }
        .add-form button { margin: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 剪切板监控 - 管理界面</h1>
        
        <div class="card">
            <h2>运行状态</h2>
            <div class="status">
                <div class="dot" id="statusDot"></div>
                <span id="statusText">运行中</span>
            </div>
        </div>
        
        <div class="card">
            <h2>基本设置</h2>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="enabled" checked onchange="updateConfig()">
                    启用监控
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="notifications" checked onchange="updateConfig()">
                    发送桌面通知
                </label>
            </div>
            <div class="form-group">
                <label>匹配前缀 (逗号分隔)</label>
                <input type="text" id="match_prefix" placeholder="如: curl, wget, http" value="curl" onchange="updateConfig()">
            </div>
            <div class="form-group">
                <label>检查间隔 (秒)</label>
                <input type="text" id="check_interval" value="1.0" onchange="updateConfig()">
            </div>
        </div>
        
        <div class="card">
            <h2>域名替换规则</h2>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="use_regex" onchange="updateConfig()">
                    启用正则表达式匹配
                </label>
            </div>
            <div id="rulesList"></div>
            <div class="add-form">
                <input type="text" id="newPattern" placeholder="原域名或正则 (如: dev\\.huilianyi\\.com)">
                <input type="text" id="newReplace" placeholder="替换为 (如: {{local-dev-host}})">
                <button onclick="addRule()">添加规则</button>
            </div>
        </div>
        
        <div class="card">
            <h2>操作</h2>
            <button onclick="restartService()">重启服务</button>
        </div>
    </div>
    
    <script>
        let config = {};
        
        function loadConfig() {
            fetch('/api/config').then(r => r.json()).then(data => {
                config = data;
                document.getElementById('enabled').checked = data.enabled;
                document.getElementById('notifications').checked = data.notifications;
                document.getElementById('check_interval').value = data.check_interval;
                document.getElementById('use_regex').checked = data.use_regex || false;
                document.getElementById('match_prefix').value = data.match_prefix || 'curl';
                renderRules();
            });
        }
        
        function renderRules() {
            const list = document.getElementById('rulesList');
            list.innerHTML = config.rules.map((r, i) => 
                '<div class="rule-item">' +
                '<span class="pattern">' + r.pattern + '</span>' +
                '<span>→</span>' +
                '<span class="replace">' + r.replace + '</span>' +
                '<span class="delete" onclick="deleteRule(' + i + ')">✕</span>' +
                '</div>'
            ).join('');
        }
        
        function updateConfig() {
            config.enabled = document.getElementById('enabled').checked;
            config.notifications = document.getElementById('notifications').checked;
            config.check_interval = parseFloat(document.getElementById('check_interval').value);
            config.use_regex = document.getElementById('use_regex').checked;
            config.match_prefix = document.getElementById('match_prefix').value;
            saveConfig();
        }
        
        function addRule() {
            const pattern = document.getElementById('newPattern').value;
            const replace = document.getElementById('newReplace').value;
            if (pattern && replace) {
                config.rules.push({pattern: pattern, replace: replace});
                document.getElementById('newPattern').value = '';
                document.getElementById('newReplace').value = '';
                saveConfig();
                renderRules();
            }
        }
        
        function deleteRule(index) {
            config.rules.splice(index, 1);
            saveConfig();
            renderRules();
        }
        
        function saveConfig() {
            fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
        }
        
        function restartService() {
            fetch('/api/restart', {method: 'POST'});
            alert('服务已重启');
        }
        
        loadConfig();
    </script>
</body>
</html>"""

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            config = load_config()
            self.wfile.write(json.dumps(config).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/config':
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)
            config = json.loads(body)
            save_config(config)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success": true}')
        elif self.path == '/api/restart':
            os.system('pkill -f clipboard_monitor.py')
            os.system('nohup python3 ~/code/script/clipboard-monitor/clipboard_monitor.py --daemon > /tmp/clipboard-monitor.log 2>&1 &')
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 禁用日志

def run(port=5001):
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f"管理界面启动: http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    run(port)
