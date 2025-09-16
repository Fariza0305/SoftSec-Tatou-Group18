#!/bin/bash

# 配置参数
TOKEN="eyJ1aWQiOjEsImxvZ2luIjoiTXJfSW1wb3J0YW50IiwiZW1haWwiOiJpbXBvcnRhbnRAMTYzLmNvbSJ9.aMg7Mw.zOLMTEm8TlVpe7iIkxhWzN3707A"
DOC_ID="12"
BASE_URL="http://localhost:5000"

echo "=== 完整的水印调试 ==="
echo "使用Token: ${TOKEN:0:20}..."
echo "文档ID: $DOC_ID"
echo "基础URL: $BASE_URL"
echo ""

# 1. 检查服务器状态
echo "1. ✅ 检查服务器状态..."
response=$(curl -s -w "%{http_code}" "$BASE_URL/healthz")
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
echo "响应: $response_body"
echo ""

# 2. 获取水印方法
echo "2. ✅ 获取水印方法..."
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/get-watermarking-methods")
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
if [ "$status_code" -eq 200 ]; then
    echo "响应:"
    echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
else
    echo "响应: $response_body"
fi
echo ""

# 3. 查看现有水印版本
echo "3. ✅ 查看现有水印版本..."
response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/list-versions/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN")
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
if [ "$status_code" -eq 200 ]; then
    echo "响应:"
    echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
else
    echo "响应: $response_body"
fi
echo ""

# 4. 尝试 toy-eof 方法提取水印
echo "4. ✅ 尝试 toy-eof 方法提取水印..."
response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/read-watermark/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "toy-eof",
    "key": "mr_important_secret_2024"
  }')
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
echo "响应: $response_body"
echo ""

# 5. 尝试 bash-bridge-eof 方法提取水印
echo "5. ✅ 尝试 bash-bridge-eof 方法提取水印..."
response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/read-watermark/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "bash-bridge-eof"
  }')
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
echo "响应: $response_body"
echo ""

# 6. 尝试不同的密钥
echo "6. ✅ 尝试不同的密钥..."
KEYS=("mr_important_secret_2024" "secret_key_123" "Mr_Important" "flag_secret" "watermark_key" "test")

for key in "${KEYS[@]}"; do
    echo "尝试密钥: $key"
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/read-watermark/$DOC_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"method\": \"toy-eof\", \"key\": \"$key\"}")
    status_code=${response: -3}
    response_body=${response%???}
    echo "状态码: $status_code"
    if [ "$status_code" -eq 200 ]; then
        echo "✅ 成功! 响应: $response_body"
        break
    else
        echo "响应: $response_body"
    fi
    echo "---"
done
echo ""

# 7. 检查水印文件
echo "7. ✅ 检查水印文件..."
if [ -f "mr_important_watermarked.pdf" ]; then
    watermarked_size=$(wc -c < "mr_important_watermarked.pdf")
    echo "水印文件大小: $watermarked_size bytes"
    
    if [ -f "flag.pdf" ]; then
        original_size=$(wc -c < "flag.pdf")
        echo "原始文件大小: $original_size bytes"
        echo "大小差异: $((watermarked_size - original_size)) bytes"
        
        # 查看文件末尾差异
        echo "文件末尾内容 (hex):"
        tail -c 50 "mr_important_watermarked.pdf" | hexdump -C
    else
        echo "原始文件 flag.pdf 不存在"
        echo "水印文件末尾内容 (hex):"
        tail -c 100 "mr_important_watermarked.pdf" | hexdump -C
    fi
else
    echo "❌ 水印文件 mr_important_watermarked.pdf 不存在"
fi
echo ""

# 8. 验证认证是否有效
echo "8. ✅ 验证认证令牌是否有效..."
response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/list-documents" \
  -H "Authorization: Bearer $TOKEN")
status_code=${response: -3}
response_body=${response%???}
echo "状态码: $status_code"
if [ "$status_code" -eq 200 ]; then
    echo "✅ 认证有效"
    echo "响应: $response_body"
else
    echo "❌ 认证可能已过期"
    echo "响应: $response_body"
fi

echo ""
echo "=== 调试完成 ==="
