#!/bin/bash
# Regression Test: rt_xss_img_onerror
# Description: Test XSS protection against img onerror attack
# Generated: 2025-10-17T18:58:26.234694

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_xss_img_onerror"

echo "Running regression test: $TEST_NAME"
echo "Description: Test XSS protection against img onerror attack"
echo ""

# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{{"login":"<img src=x onerror=alert(\"XSS\")>","email":"test@test.com","password":"test123"}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '<img src=x onerror=alert("XSS")>'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
