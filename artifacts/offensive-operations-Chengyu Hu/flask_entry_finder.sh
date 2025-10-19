#!/usr/bin/env bash
# 自动访问各组 Flask 首页并分析可疑表单入口
# 用于找出后续 SSTI 或其他交互入口的参数和路径

targets=(
10.11.202.5
10.11.202.6
10.11.202.7
10.11.202.9
10.11.202.10
10.11.202.11
10.11.202.13
10.11.202.14
10.11.202.15
10.11.202.16
)

echo "🔍 正在抓取各组首页 HTML 并分析可能的交互入口..."

for ip in "${targets[@]}"; do
    echo "============================"
    echo "📡 目标: $ip"
    resp=$(curl -s -m 5 "http://$ip:5000/")
    
    if [[ -z "$resp" ]]; then
        echo "❌ 无响应或首页为空"
        continue
    fi

    # 显示前 20 行 HTML，方便人工查看
    echo "📜 首页 HTML (前 20 行)："
    echo "$resp" | head -n 20
    echo "--------------------------------------"

    # 自动分析表单 action
    actions=$(echo "$resp" | grep -oP '(?<=action=")[^"]+')
    if [[ -n "$actions" ]]; then
        echo "🧭 可能的表单提交路径:"
        echo "$actions" | sort -u
    else
        echo "ℹ️  未发现表单 action"
    fi

    # 自动分析参数名
    params=$(echo "$resp" | grep -oP '(?<=name=")[^"]+')
    if [[ -n "$params" ]]; then
        echo "🪪 可能的参数名:"
        echo "$params" | sort -u
    else
        echo "ℹ️  未发现参数名"
    fi

    echo ""
done
