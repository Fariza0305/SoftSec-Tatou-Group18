#!/bin/bash
# Regression Test: rt_sql_injection_login_union
# Description: Test SQL injection protection (UNION SELECT)
# Generated: 2025-10-17T18:58:26.235588

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_sql_injection_login_union"

echo "Running regression test: $TEST_NAME"
echo "Description: Test SQL injection protection (UNION SELECT)"
echo ""

# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{{"email":"\' UNION SELECT * FROM users --","password":"test123"}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '' UNION SELECT * FROM users --'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
