#!/bin/bash
# Non-Regression Test: nrt_create_user_valid
# Description: Test valid user creation still works
# Generated: 2025-10-17T18:59:33.729973

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_create_user_valid"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test valid user creation still works"
echo ""

# Test valid user creation
TIMESTAMP=$(date +%s)
USER_EMAIL="validuser_${TIMESTAMP}@test.com"
USER_LOGIN="validuser_${TIMESTAMP}"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"'"$USER_LOGIN"'","email":"'"$USER_EMAIL"'","password":"ValidPass123!"}' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "✓ PASS: Valid user creation works"
    echo "Response: $BODY"
    exit 0
else
    echo "✗ FAIL: Valid user creation failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
