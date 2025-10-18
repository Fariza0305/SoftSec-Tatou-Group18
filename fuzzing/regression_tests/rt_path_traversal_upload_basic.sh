#!/bin/bash
# Regression Test: rt_path_traversal_upload_basic
# Description: Test path traversal protection in upload (../ attack)
# Generated: 2025-10-17T18:58:26.234795

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_path_traversal_upload_basic"

echo "Running regression test: $TEST_NAME"
echo "Description: Test path traversal protection in upload (../ attack)"
echo ""

# Test path traversal in file upload
# First create a test user and login
USER_EMAIL="test_$(date +%s)@test.com"
curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"testuser","email":"'$USER_EMAIL'","password":"test123"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"'$USER_EMAIL'","password":"test123"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate"
    exit 1
fi

# Test malicious filename
RESPONSE=$(curl -s -X POST "$BASE_URL/api/upload-document" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/dev/null;filename=../../../etc/passwd" 2>/dev/null)

# Check if path traversal was blocked
if echo "$RESPONSE" | grep -qE "(error|invalid|forbidden|denied)"; then
    echo "✓ PASS: Path traversal was blocked"
    exit 0
else
    echo "✗ FAIL: Path traversal may not be blocked"
    echo "$RESPONSE"
    exit 1
fi
