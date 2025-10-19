#!/bin/bash
# Non-Regression Test: nrt_list_documents
# Description: Test listing documents still works
# Generated: 2025-10-17T18:59:33.731279

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_list_documents"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test listing documents still works"
echo ""

# Test listing documents
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="listdocs_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"listdocstest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for list documents test"
    exit 1
fi

# List documents
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/documents" \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: List documents works"
    exit 0
else
    echo "✗ FAIL: List documents failed with code $HTTP_CODE"
    exit 1
fi
