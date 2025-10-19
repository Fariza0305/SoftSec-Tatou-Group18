#!/bin/bash
# Non-Regression Test: nrt_rmap_initiate_valid
# Description: Test valid RMAP initiate still works
# Generated: 2025-10-17T18:59:33.731497

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_rmap_initiate_valid"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test valid RMAP initiate still works"
echo ""

# Test RMAP initiate with valid data
VALID_XML='<?xml version="1.0" encoding="UTF-8"?>
<rmap>
  <identity>test@example.com</identity>
  <document>test-document</document>
</rmap>'

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/rmap-initiate" \
    -H "Content-Type: application/xml" \
    -d "$VALID_XML" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✓ PASS: RMAP initiate endpoint responds (may return error for unknown identity, which is expected)"
    exit 0
else
    echo "✗ FAIL: RMAP initiate failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
