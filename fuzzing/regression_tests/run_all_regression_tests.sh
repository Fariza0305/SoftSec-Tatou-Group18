#!/bin/bash
# Master Regression Test Runner
# Generated: 2025-10-17T18:58:26.236818

BASE_URL="${1:-http://localhost:5000}"
PASSED=0
FAILED=0
TOTAL=0

echo "========================================="
echo "  Running All Regression Tests"
echo "========================================="
echo ""


echo "Running: rt_xss_create_user_login..."
if bash "fuzzing/regression_tests/rt_xss_create_user_login.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xss_create_user_login"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xss_create_user_login"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_xss_create_user_email..."
if bash "fuzzing/regression_tests/rt_xss_create_user_email.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xss_create_user_email"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xss_create_user_email"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_xss_img_onerror..."
if bash "fuzzing/regression_tests/rt_xss_img_onerror.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xss_img_onerror"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xss_img_onerror"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_xss_svg_onload..."
if bash "fuzzing/regression_tests/rt_xss_svg_onload.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xss_svg_onload"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xss_svg_onload"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_path_traversal_upload_basic..."
if bash "fuzzing/regression_tests/rt_path_traversal_upload_basic.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_path_traversal_upload_basic"
    ((PASSED++))
else
    echo "✗ FAIL: rt_path_traversal_upload_basic"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_path_traversal_upload_windows..."
if bash "fuzzing/regression_tests/rt_path_traversal_upload_windows.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_path_traversal_upload_windows"
    ((PASSED++))
else
    echo "✗ FAIL: rt_path_traversal_upload_windows"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_path_traversal_rmap..."
if bash "fuzzing/regression_tests/rt_path_traversal_rmap.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_path_traversal_rmap"
    ((PASSED++))
else
    echo "✗ FAIL: rt_path_traversal_rmap"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_path_traversal_encoded..."
if bash "fuzzing/regression_tests/rt_path_traversal_encoded.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_path_traversal_encoded"
    ((PASSED++))
else
    echo "✗ FAIL: rt_path_traversal_encoded"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_sql_injection_login_or..."
if bash "fuzzing/regression_tests/rt_sql_injection_login_or.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_sql_injection_login_or"
    ((PASSED++))
else
    echo "✗ FAIL: rt_sql_injection_login_or"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_sql_injection_login_union..."
if bash "fuzzing/regression_tests/rt_sql_injection_login_union.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_sql_injection_login_union"
    ((PASSED++))
else
    echo "✗ FAIL: rt_sql_injection_login_union"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_sql_injection_create_user..."
if bash "fuzzing/regression_tests/rt_sql_injection_create_user.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_sql_injection_create_user"
    ((PASSED++))
else
    echo "✗ FAIL: rt_sql_injection_create_user"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_xxe_rmap_basic..."
if bash "fuzzing/regression_tests/rt_xxe_rmap_basic.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xxe_rmap_basic"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xxe_rmap_basic"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_xxe_rmap_external..."
if bash "fuzzing/regression_tests/rt_xxe_rmap_external.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_xxe_rmap_external"
    ((PASSED++))
else
    echo "✗ FAIL: rt_xxe_rmap_external"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_rate_limit_login..."
if bash "fuzzing/regression_tests/rt_rate_limit_login.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_rate_limit_login"
    ((PASSED++))
else
    echo "✗ FAIL: rt_rate_limit_login"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_rate_limit_create_user..."
if bash "fuzzing/regression_tests/rt_rate_limit_create_user.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_rate_limit_create_user"
    ((PASSED++))
else
    echo "✗ FAIL: rt_rate_limit_create_user"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_info_disclosure_invalid_json..."
if bash "fuzzing/regression_tests/rt_info_disclosure_invalid_json.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_info_disclosure_invalid_json"
    ((PASSED++))
else
    echo "✗ FAIL: rt_info_disclosure_invalid_json"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "Running: rt_info_disclosure_null_values..."
if bash "fuzzing/regression_tests/rt_info_disclosure_null_values.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: rt_info_disclosure_null_values"
    ((PASSED++))
else
    echo "✗ FAIL: rt_info_disclosure_null_values"
    ((FAILED++))
fi
((TOTAL++))
echo ""

echo "========================================="
echo "  Regression Test Summary"
echo "========================================="
echo "Total: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All regression tests passed!"
    exit 0
else
    echo "✗ Some regression tests failed"
    exit 1
fi
