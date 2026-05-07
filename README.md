# Clipboard Monitor

剪切板监控工具 - 自动检测 curl 命令并替换域名

## 功能特性

- 🔍 **实时监控剪切板** - 每秒检测剪切板变化
- 🌍 **域名自动替换** - 将线上域名替换为本地变量
- ⚙️ **可配置规则** - 支持自定义替换规则
- 📊 **Web 管理界面** - 图形化配置和历史查看
- 🔔 **系统通知** - 替换成功后推送通知
- 🚀 **开机自启** - 支持 systemd 服务

## 域名替换规则

| 线上域名 | 本地变量 |
|---------|---------|
| dev.huilianyi.com | {{local-dev-host}} |
| uat.huilianyi.com | {{local-uat-host}} |
| pro.huilianyi.com | {{local-pro-host}} |

## 快速开始

### 1. 启动服务

```bash
cd ~/code/script/clipboard-monitor
./start.sh
```

### 2. 管理控制

```bash
# 查看状态
./ctl.sh status

# 停止服务
./ctl.sh stop

# 重启服务
./ctl.sh restart
```

### 3. Web 管理界面

启动后访问：http://localhost:5000

- 查看替换历史
- 修改替换规则
- 开关监控功能

## 配置说明

配置文件位于：`~/.config/clipboard-monitor/config.json`

```json
{
  "rules": [
    {"pattern": "dev.huilianyi.com", "replace": "{{local-dev-host}}"},
    {"pattern": "uat.huilianyi.com", "replace": "{{local-uat-host}}"},
    {"pattern": "pro.huilianyi.com", "replace": "{{local-pro-host}}"}
  ],
  "enabled": true,
  "notifications": true,
  "check_interval": 1.0
}
```

## 使用场景

开发时复制线上 curl 命令，自动替换为本地环境变量，方便本地测试：

```
# 原始（线上）
curl https://dev.huilianyi.com/api/user

# 替换后（本地）
curl {{local-dev-host}}/api/user
```

## 系统服务

如需开机自启，可配置 systemd 服务：

```bash
cp clipboard-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable clipboard-monitor
```

## 技术栈

- Python 3
- pyperclip - 剪切板读取
- Flask - Web 管理界面
- systemd - 开机自启
