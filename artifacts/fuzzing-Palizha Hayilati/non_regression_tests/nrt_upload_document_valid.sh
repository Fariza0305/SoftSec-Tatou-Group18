#!/bin/bash
# Non-Regression Test: nrt_upload_document_valid
# Description: Test valid document upload still works
# Generated: 2025-10-17T18:59:33.731010

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="nrt_upload_document_valid"

echo "Running non-regression test: $TEST_NAME"
echo "Description: Test valid document upload still works"
echo ""

# Test valid document upload
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="upload_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"uploadtest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for upload test"
    exit 1
fi

# Create a valid test file
echo "This is a test document" > /tmp/test_doc_${TIMESTAMP}.txt

# Upload the document
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/upload-document" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/test_doc_${TIMESTAMP}.txt" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

# Cleanup
rm -f /tmp/test_doc_${TIMESTAMP}.txt

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "✓ PASS: Valid document upload works"
    exit 0
else
    echo "✗ FAIL: Valid document upload failed with code $HTTP_CODE"
    exit 1
fi
