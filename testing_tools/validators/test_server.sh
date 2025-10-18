#!/bin/bash

# 测试脚本 - 验证服务器功能
echo "=== Tatou 服务器功能测试 ==="

# 检查服务器是否运行
echo "1. 检查服务器状态..."
if curl -s http://localhost:5000/healthz > /dev/null; then
    echo "✅ 服务器正在运行"
else
    echo "❌ 服务器未运行，请先启动服务器"
    exit 1
fi

# 测试健康检查端点
echo "2. 测试健康检查端点..."
response=$(curl -s -w "%{http_code}" http://localhost:5000/healthz)
if [[ "$response" == *"200" ]]; then
    echo "✅ 健康检查端点正常"
else
    echo "❌ 健康检查端点异常"
fi

# 测试登录端点（预期会失败，因为没有数据库）
echo "3. 测试登录端点..."
response=$(curl -s -w "%{http_code}" http://localhost:5000/api/login)
if [[ "$response" == *"500" ]]; then
    echo "✅ 登录端点响应正常（500错误是预期的，因为没有数据库）"
else
    echo "❌ 登录端点响应异常"
fi

# 测试其他端点
echo "4. 测试其他端点..."
endpoints=("/api/register" "/api/upload" "/api/download" "/api/list")

for endpoint in "${endpoints[@]}"; do
    response=$(curl -s -w "%{http_code}" "http://localhost:5000$endpoint")
    echo "   $endpoint: HTTP $(echo $response | tail -c 4)"
done

echo "=== 测试完成 ==="

