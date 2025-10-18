#!/bin/bash
# Regression Test: rt_path_traversal_rmap
# Description: Test path traversal protection in rmap-initiate
# Generated: 2025-10-17T18:58:26.235036

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_path_traversal_rmap"

echo "Running regression test: $TEST_NAME"
echo "Description: Test path traversal protection in rmap-initiate"
echo ""

# Test payload injection in RMAP
RESPONSE=$(curl -s -X POST "$BASE_URL/api/rmap-initiate" \
    -H "Content-Type: application/xml" \
    -d '../../../etc/passwd' 2>/dev/null)

# Check for indicators of successful attack
if echo "$RESPONSE" | grep -qE "(root:|/etc/passwd|file:///|ENTITY)"; then
    echo "✗ FAIL: Attack may have succeeded"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Attack was blocked"
    exit 0
fi
