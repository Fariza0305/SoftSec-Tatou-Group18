#!/bin/bash
# Non-Regression Test: nrt_login_valid
# Description: Test valid user login still works
# Generated: 2025-10-17T18:59:33.730886

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_login_valid"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test valid user login still works"
echo ""

# Test valid user login
# First create a user
TIMESTAMP=$(date +%s)
USER_EMAIL="logintest_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"logintest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

# Now try to login
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "token"; then
    echo "✓ PASS: Valid login works"
    echo "Got token successfully"
    exit 0
else
    echo "✗ FAIL: Valid login failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
