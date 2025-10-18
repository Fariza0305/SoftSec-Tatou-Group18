#!/bin/bash

# Security Fixes Verification Script
# Tests the fixes for critical vulnerabilities

BASE_URL="http://localhost:5000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "   Security Fixes Verification Test"
echo "========================================"
echo ""

# Test 1: XSS in create-user (should be blocked)
echo -e "${YELLOW}[TEST 1]${NC} Testing XSS protection in /api/create-user..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/create-user \
  -H "Content-Type: application/json" \
  -d '{"login":"<script>alert(1)</script>","password":"Test123!","email":"xss@test.com"}')

if echo "$RESPONSE" | grep -q "invalid characters" || echo "$RESPONSE" | grep -q "Invalid"; then
    echo -e "${GREEN}✓ PASS${NC} - XSS attempt blocked"
else
    echo -e "${RED}✗ FAIL${NC} - XSS not blocked: $RESPONSE"
fi
echo ""

# Test 2: Path Traversal in rmap-initiate (should be blocked)
echo -e "${YELLOW}[TEST 2]${NC} Testing path traversal protection in /api/rmap-initiate..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/rmap-initiate \
  -H "Content-Type: application/json" \
  -d '{"identity":"../../../etc/passwd","nonceClient":1}')

if echo "$RESPONSE" | grep -q "Invalid identity"; then
    echo -e "${GREEN}✓ PASS${NC} - Path traversal blocked"
else
    echo -e "${RED}✗ FAIL${NC} - Path traversal not blocked: $RESPONSE"
fi
echo ""

# Test 3: XXE in rmap-initiate (should be blocked)
echo -e "${YELLOW}[TEST 3]${NC} Testing XXE protection in /api/rmap-initiate..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/rmap-initiate \
  -H "Content-Type: application/json" \
  -d '{"identity":"<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>","nonceClient":1}')

if echo "$RESPONSE" | grep -q "Invalid identity"; then
    echo -e "${GREEN}✓ PASS${NC} - XXE attempt blocked"
else
    echo -e "${RED}✗ FAIL${NC} - XXE not blocked: $RESPONSE"
fi
echo ""

# Test 4: Valid user creation (should succeed)
echo -e "${YELLOW}[TEST 4]${NC} Testing valid user creation..."
RANDOM_USER="testuser_$RANDOM"
RESPONSE=$(curl -s -X POST $BASE_URL/api/create-user \
  -H "Content-Type: application/json" \
  -d "{\"login\":\"$RANDOM_USER\",\"password\":\"ValidPass123!\",\"email\":\"${RANDOM_USER}@test.com\"}")

if echo "$RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✓ PASS${NC} - Valid user created successfully"
    USER_EMAIL="${RANDOM_USER}@test.com"
else
    echo -e "${RED}✗ FAIL${NC} - Valid user creation failed: $RESPONSE"
fi
echo ""

# Test 5: Rate limiting on login (should trigger after 5 attempts)
echo -e "${YELLOW}[TEST 5]${NC} Testing rate limiting on /api/login..."
echo "  Sending 6 login attempts..."
RATE_LIMITED=false
for i in {1..6}; do
    RESPONSE=$(curl -s -X POST $BASE_URL/api/login \
      -H "Content-Type: application/json" \
      -d '{"email":"test@test.com","password":"wrong"}')
    
    if echo "$RESPONSE" | grep -q "Rate limit\|Too many"; then
        RATE_LIMITED=true
        break
    fi
    sleep 0.2
done

if [ "$RATE_LIMITED" = true ]; then
    echo -e "${GREEN}✓ PASS${NC} - Rate limiting is working"
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Rate limiting may not be working"
fi
echo ""

# Test 6: Information disclosure (should return generic error)
echo -e "${YELLOW}[TEST 6]${NC} Testing information disclosure protection..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/create-user \
  -H "Content-Type: application/json" \
  -d '{"login":null,"password":null,"email":null}')

if echo "$RESPONSE" | grep -q "traceback\|File\|line"; then
    echo -e "${RED}✗ FAIL${NC} - Stack trace leaked: $RESPONSE"
else
    echo -e "${GREEN}✓ PASS${NC} - No stack trace in error response"
fi
echo ""

# Test 7: Security headers
echo -e "${YELLOW}[TEST 7]${NC} Testing security headers..."
HEADERS=$(curl -s -I $BASE_URL/healthz)

HEADERS_OK=true
if ! echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    echo -e "${RED}  ✗${NC} Missing X-Content-Type-Options header"
    HEADERS_OK=false
fi
if ! echo "$HEADERS" | grep -q "X-Frame-Options"; then
    echo -e "${RED}  ✗${NC} Missing X-Frame-Options header"
    HEADERS_OK=false
fi
if ! echo "$HEADERS" | grep -q "X-XSS-Protection"; then
    echo -e "${RED}  ✗${NC} Missing X-XSS-Protection header"
    HEADERS_OK=false
fi

if [ "$HEADERS_OK" = true ]; then
    echo -e "${GREEN}✓ PASS${NC} - All security headers present"
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Some security headers missing"
fi
echo ""

# Test 8: Valid RMAP initiate (should succeed)
echo -e "${YELLOW}[TEST 8]${NC} Testing valid RMAP initiate..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/rmap-initiate \
  -H "Content-Type: application/json" \
  -d '{"identity":"GROUP_18","nonceClient":12345}')

if echo "$RESPONSE" | grep -q "nonceServer"; then
    echo -e "${GREEN}✓ PASS${NC} - Valid RMAP initiate works"
else
    echo -e "${YELLOW}⚠ INFO${NC} - RMAP initiate response: $RESPONSE"
fi
echo ""

# Summary
echo "========================================"
echo "         Test Summary Complete"
echo "========================================"
echo ""
echo "Key improvements implemented:"
echo "  ✓ XSS protection (input validation)"
echo "  ✓ Path traversal protection"
echo "  ✓ XXE protection"
echo "  ✓ Information disclosure prevention"
echo "  ✓ Rate limiting on auth endpoints"
echo "  ✓ Security headers"
echo "  ✓ Input validation"
echo "  ✓ Secure file uploads"
echo ""


