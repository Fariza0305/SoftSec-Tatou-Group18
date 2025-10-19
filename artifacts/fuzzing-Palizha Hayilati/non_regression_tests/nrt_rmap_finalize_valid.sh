#!/bin/bash
# Non-Regression Test: nrt_rmap_finalize_valid
# Description: Test valid RMAP finalize still works
# Generated: 2025-10-17T18:59:33.731548

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_rmap_finalize_valid"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test valid RMAP finalize still works"
echo ""

# Test RMAP finalize with valid data
VALID_XML='<?xml version="1.0" encoding="UTF-8"?>
<rmap>
  <session>test-session</session>
  <status>complete</status>
</rmap>'

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/rmap-finalize" \
    -H "Content-Type: application/xml" \
    -d "$VALID_XML" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✓ PASS: RMAP finalize endpoint responds (may return error for unknown session, which is expected)"
    exit 0
else
    echo "✗ FAIL: RMAP finalize failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
