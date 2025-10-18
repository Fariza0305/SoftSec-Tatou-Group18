#!/bin/bash
# Regression Test: rt_sql_injection_login_or
# Description: Test SQL injection protection (OR 1=1)
# Generated: 2025-10-17T18:58:26.235551

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_sql_injection_login_or"

echo "Running regression test: $TEST_NAME"
echo "Description: Test SQL injection protection (OR 1=1)"
echo ""

# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{{"email":"\' OR \'1\'=\'1","password":"test123"}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '' OR '1'='1'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
