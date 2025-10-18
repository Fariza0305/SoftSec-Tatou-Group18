#!/bin/bash
# Non-Regression Test: nrt_healthz_verbose
# Description: Test verbose healthz endpoint
# Generated: 2025-10-17T18:59:33.732509

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_healthz_verbose"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test verbose healthz endpoint"
echo ""

# Test healthz-verbose endpoint
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/healthz-verbose" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: Healthz-verbose endpoint works"
    exit 0
else
    echo "✗ FAIL: Healthz-verbose endpoint failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
