#!/bin/bash
# Regression Test: rt_info_disclosure_null_values
# Description: Test no stack traces on null values
# Generated: 2025-10-17T18:58:26.236588

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_info_disclosure_null_values"

echo "Running regression test: $TEST_NAME"
echo "Description: Test no stack traces on null values"
echo ""

# Test information disclosure protection
RESPONSE=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d 'null' 2>/dev/null)

if echo "$RESPONSE" | grep -qE "(Traceback|File \"|line [0-9]+|Exception:|stack trace)"; then
    echo "✗ FAIL: Stack trace found in response"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: No stack trace in response"
    exit 0
fi
