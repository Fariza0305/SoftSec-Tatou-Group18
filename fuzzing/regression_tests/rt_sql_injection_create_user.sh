#!/bin/bash
# Regression Test: rt_sql_injection_create_user
# Description: Test SQL injection protection in create-user
# Generated: 2025-10-17T18:58:26.235786

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_sql_injection_create_user"

echo "Running regression test: $TEST_NAME"
echo "Description: Test SQL injection protection in create-user"
echo ""

# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{{"login":"admin\'--","email":"test@test.com","password":"test123"}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF 'admin'--'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
