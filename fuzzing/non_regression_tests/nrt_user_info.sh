#!/bin/bash
# Non-Regression Test: nrt_user_info
# Description: Test getting user info still works
# Generated: 2025-10-17T18:59:33.730954

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_user_info"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test getting user info still works"
echo ""

# Test getting user info
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="userinfo_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"userinfotest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for user info test"
    exit 1
fi

# Get user info
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/user/info" \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: User info retrieval works"
    exit 0
else
    echo "✗ FAIL: User info retrieval failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
