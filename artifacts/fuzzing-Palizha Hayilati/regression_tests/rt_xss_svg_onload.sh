#!/bin/bash
# Regression Test: rt_xss_svg_onload
# Description: Test XSS protection against SVG onload attack
# Generated: 2025-10-17T18:58:26.234746

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_xss_svg_onload"

echo "Running regression test: $TEST_NAME"
echo "Description: Test XSS protection against SVG onload attack"
echo ""

# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{{"login":"<svg onload=alert(\"XSS\")>","email":"test@test.com","password":"test123"}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '<svg onload=alert("XSS")>'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
