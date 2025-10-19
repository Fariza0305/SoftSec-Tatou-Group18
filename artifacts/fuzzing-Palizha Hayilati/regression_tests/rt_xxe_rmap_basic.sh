#!/bin/bash
# Regression Test: rt_xxe_rmap_basic
# Description: Test XXE protection in rmap-initiate
# Generated: 2025-10-17T18:58:26.235826

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_xxe_rmap_basic"

echo "Running regression test: $TEST_NAME"
echo "Description: Test XXE protection in rmap-initiate"
echo ""

# Test payload injection in RMAP
RESPONSE=$(curl -s -X POST "$BASE_URL/api/rmap-initiate" \
    -H "Content-Type: application/xml" \
    -d '<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><root>&xxe;</root>' 2>/dev/null)

# Check for indicators of successful attack
if echo "$RESPONSE" | grep -qE "(root:|/etc/passwd|file:///|ENTITY)"; then
    echo "✗ FAIL: Attack may have succeeded"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Attack was blocked"
    exit 0
fi
