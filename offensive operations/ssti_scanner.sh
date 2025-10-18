#!/usr/bin/env bash
# 对所有开放的 Flask 服务尝试 SSTI 探测

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

echo "🔍 尝试 {{7*7}} 探测各组的模板注入漏洞..."

for ip in "${targets[@]}"; do
    resp=$(curl -s -m 3 "http://$ip:5000/?name={{7*7}}")
    if echo "$resp" | grep -q "49"; then
        echo "🎯 可能存在 SSTI 漏洞: $ip"
    else
        echo "ℹ️  $ip 没有直接返回 49（可能无漏洞，或参数不同）"
    fi
done
