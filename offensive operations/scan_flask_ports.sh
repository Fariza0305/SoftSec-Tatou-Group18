#!/usr/bin/env bash
# 扫描比赛环境中各组 Flask 服务是否开放 5000 端口

targets=(
10.11.202.3
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

echo "🔍 正在扫描各组 Flask 服务 (TCP 5000)..."
for ip in "${targets[@]}"; do
    timeout 2 bash -c "</dev/tcp/$ip/5000" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo "✅ $ip:5000 已开放"
    else
        echo "❌ $ip:5000 未响应"
    fi
done
