#!/bin/bash
# Quick Validation Script
# Verifies that all security fixes are working correctly

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Tatou API - Quick Security Validation                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if server is running
SERVER_URL="${1:-http://localhost:5000}"
echo "🔍 Checking server at: $SERVER_URL"
echo ""

# Test server availability
echo "1️⃣  Testing server availability..."
HEALTH_CHECK=$(curl -s "$SERVER_URL/api/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ Server is running"
else
    echo "   ❌ Server is not responding"
    echo ""
    echo "Please start the server first:"
    echo "  cd server/src && python3 server.py"
    exit 1
fi

echo ""

# Test XSS protection
echo "2️⃣  Testing XSS protection..."
XSS_RESULT=$(curl -s -X POST "$SERVER_URL/api/create-user" \
    -H "Content-Type: application/json" \
    -d '{"login":"<script>alert(1)</script>","email":"test@test.com","password":"pass"}' 2>/dev/null)

if echo "$XSS_RESULT" | grep -q "<script>" 2>/dev/null; then
    echo "   ❌ XSS protection FAILED - script tag not sanitized"
else
    echo "   ✅ XSS protection working"
fi

echo ""

# Test path traversal protection
echo "3️⃣  Testing path traversal protection..."
PATH_RESULT=$(curl -s -X POST "$SERVER_URL/api/upload-document" \
    -H "Content-Type: application/json" \
    -d '{"filename":"../../../etc/passwd","content":"test"}' 2>/dev/null)

if echo "$PATH_RESULT" | grep -q "error" || echo "$PATH_RESULT" | grep -q "Invalid"; then
    echo "   ✅ Path traversal protection working"
else
    echo "   ❌ Path traversal protection FAILED"
fi

echo ""

# Test SQL injection protection
echo "4️⃣  Testing SQL injection protection..."
SQL_RESULT=$(curl -s -X POST "$SERVER_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin' OR '1'='1\",\"password\":\"test\"}" 2>/dev/null)

if echo "$SQL_RESULT" | grep -q "Invalid\|error\|failed" 2>/dev/null; then
    echo "   ✅ SQL injection protection working"
else
    echo "   ⚠️  SQL injection response (check logs)"
fi

echo ""

# Test rate limiting (if enabled)
echo "5️⃣  Testing rate limiting..."
echo "   Sending 6 rapid requests to /api/login..."
RATE_LIMIT_HIT=false
for i in {1..6}; do
    RATE_RESULT=$(curl -s -w "%{http_code}" -X POST "$SERVER_URL/api/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"test"}' 2>/dev/null | tail -n1)
    
    if [ "$RATE_RESULT" = "429" ]; then
        RATE_LIMIT_HIT=true
        break
    fi
    sleep 0.1
done

if [ "$RATE_LIMIT_HIT" = true ]; then
    echo "   ✅ Rate limiting working (HTTP 429 received)"
else
    echo "   ⚠️  Rate limiting not triggered (may need more requests)"
fi

echo ""

# Test security headers
echo "6️⃣  Testing security headers..."
HEADERS=$(curl -s -I "$SERVER_URL/api/health" 2>/dev/null)

HEADERS_OK=true
if echo "$HEADERS" | grep -q "X-Content-Type-Options:"; then
    echo "   ✅ X-Content-Type-Options header present"
else
    echo "   ❌ X-Content-Type-Options header missing"
    HEADERS_OK=false
fi

if echo "$HEADERS" | grep -q "X-Frame-Options:"; then
    echo "   ✅ X-Frame-Options header present"
else
    echo "   ❌ X-Frame-Options header missing"
    HEADERS_OK=false
fi

if echo "$HEADERS" | grep -q "X-XSS-Protection:"; then
    echo "   ✅ X-XSS-Protection header present"
else
    echo "   ❌ X-XSS-Protection header missing"
    HEADERS_OK=false
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Validation Summary                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Quick validation complete! For comprehensive testing, run:"
echo ""
echo "  📋 Regression Tests (17 tests):"
echo "     cd fuzzing/regression_tests"
echo "     ./run_all_regression_tests.sh $SERVER_URL"
echo ""
echo "  📋 Non-Regression Tests (9 tests):"
echo "     cd fuzzing/non_regression_tests"
echo "     ./run_all_non_regression_tests.sh $SERVER_URL"
echo ""
echo "  📊 Full Report:"
echo "     cat FINAL_SECURITY_REPORT.md"
echo ""


