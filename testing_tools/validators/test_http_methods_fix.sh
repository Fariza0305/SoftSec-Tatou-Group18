#!/bin/bash

# HTTP方法修复测试脚本
# 测试修复后的HTTP方法处理是否正确返回405而不是500

echo "🔧 测试HTTP方法修复..."
echo "目标: http://localhost:5000"
echo ""

# 测试 /api/login 端点的不同HTTP方法
echo "📋 测试 /api/login 端点:"
echo ""

echo "✅ POST (应该返回401 - 认证失败):"
curl -s -w "状态码: %{http_code}\n" -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}' | head -1

echo ""
echo "❌ GET (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X GET http://localhost:5000/api/login | head -1

echo ""
echo "❌ PUT (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X PUT http://localhost:5000/api/login | head -1

echo ""
echo "❌ DELETE (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X DELETE http://localhost:5000/api/login | head -1

echo ""
echo "❌ PATCH (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X PATCH http://localhost:5000/api/login | head -1

echo ""
echo "❌ HEAD (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X HEAD http://localhost:5000/api/login | head -1

echo ""
echo "✅ OPTIONS (应该返回200 - 预检请求):"
curl -s -w "状态码: %{http_code}\n" -X OPTIONS http://localhost:5000/api/login | head -1

echo ""
echo "=========================================="
echo ""

# 测试 /api/get-watermarking-methods 端点
echo "📋 测试 /api/get-watermarking-methods 端点:"
echo ""

echo "✅ GET (应该返回200 - 正常):"
curl -s -w "状态码: %{http_code}\n" -X GET http://localhost:5000/api/get-watermarking-methods | head -1

echo ""
echo "❌ POST (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X POST http://localhost:5000/api/get-watermarking-methods | head -1

echo ""
echo "❌ PUT (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X PUT http://localhost:5000/api/get-watermarking-methods | head -1

echo ""
echo "=========================================="
echo ""

# 测试 /healthz 端点
echo "📋 测试 /healthz 端点:"
echo ""

echo "✅ GET (应该返回200 - 正常):"
curl -s -w "状态码: %{http_code}\n" -X GET http://localhost:5000/healthz | head -1

echo ""
echo "❌ POST (应该返回405 - 方法不允许):"
curl -s -w "状态码: %{http_code}\n" -X POST http://localhost:5000/healthz | head -1

echo ""
echo "=========================================="
echo ""

echo "🎯 测试总结:"
echo "- 如果修复成功，所有不支持的HTTP方法都应该返回405状态码"
echo "- 支持的HTTP方法应该返回相应的正常状态码(200/401等)"
echo "- 不再出现500内部服务器错误"
echo ""
echo "✅ 修复完成！"

