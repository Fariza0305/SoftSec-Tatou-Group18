#!/bin/bash
# Non-Regression Test: nrt_healthz
# Description: Test healthz endpoint
# Generated: 2025-10-17T18:59:33.731772

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_healthz"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test healthz endpoint"
echo ""

# Test healthz endpoint
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/healthz" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "ok"; then
    echo "✓ PASS: Healthz endpoint works"
    exit 0
else
    echo "✗ FAIL: Healthz endpoint failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi

