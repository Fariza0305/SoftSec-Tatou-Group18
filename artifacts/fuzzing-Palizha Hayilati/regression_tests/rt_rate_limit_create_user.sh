#!/bin/bash
# Regression Test: rt_rate_limit_create_user
# Description: Test rate limiting on create-user endpoint
# Generated: 2025-10-17T18:58:26.235968

BASE_URL="${1:-http://localhost:5000}"
TEST_NAME="rt_rate_limit_create_user"

echo "Running regression test: $TEST_NAME"
echo "Description: Test rate limiting on create-user endpoint"
echo ""

# Test rate limiting
echo "Testing rate limiting on /api/create-user..."
COUNT=0
for i in {1..10}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/create-user" \
        -H "Content-Type: application/json" \
        -d '{"email":"test$i@test.com","password":"test123"}' 2>/dev/null)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    
    if [ "$HTTP_CODE" = "429" ]; then
        echo "✓ Rate limit triggered after $i requests"
        exit 0
    fi
done

echo "✗ FAIL: No rate limiting detected after 10 requests"
exit 1
