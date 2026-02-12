#!/bin/bash
# curl 命令处理脚本
# 1. 读取剪切板
# 2. 校验 curl 格式
# 3. 替换 host
# 4. 写回剪切板
# 5. 触发 Ctrl+i

set -e

# 检查依赖工具
check_deps() {
    for cmd in xclip xdotool xdg-open notify-send; do
        if ! command -v $cmd &> /dev/null; then
            echo "需要安装: $cmd"
            exit 1
        fi
    done
}

# 弹框报错
show_error() {
    notify-send "❌ 错误" "$1" --urgency=critical
    zenity --error --text="$1" 2>/dev/null || echo "ERROR: $1"
    exit 1
}

# 弹框成功
show_success() {
    notify-send "✅ 成功" "已处理并复制到剪切板" --urgency=low
}

# 读取剪切板
read_clipboard() {
    xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null
}

# 写入剪切板
write_clipboard() {
    echo "$1" | xclip -selection clipboard 2>/dev/null || xsel --clipboard --input "$1" 2>/dev/null
}

# 触发快捷键 Ctrl+i
trigger_ctrl_i() {
    xdotool key --delay 50 ctrl+i
}

# 主逻辑
main() {
    check_deps

    # 1. 读取剪切板
    content=$(read_clipboard)

    if [ -z "$content" ]; then
        show_error "剪切板为空"
    fi

    # 2. 校验 curl 格式
    if ! echo "$content" | grep -qE "^\s*curl\s+"; then
        show_error "剪切板内容不是 curl 命令"
    fi

    # 3. 替换 host
    modified="$content"

    # 替换 dev host
    if echo "$content" | grep -q "dev"; then
        modified=$(echo "$modified" | sed -E "s|https?://[^/]+|{{local-dev-host}}|g")
    fi

    # 替换 uat host
    if echo "$content" | grep -q "uat"; then
        modified=$(echo "$modified" | sed -E "s|https?://[^/]+|{{local-uat-host}}|g")
    fi

    # 4. 写回剪切板
    write_clipboard "$modified"

    # 5. 触发快捷键
    trigger_ctrl_i

    show_success
}

main "$@"
