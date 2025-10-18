#!/bin/bash
# Master Non-Regression Test Runner
# Generated: 2025-10-17T18:59:33.732806

BASE_URL="${1:-http://localhost:5000}"
PASSED=0
FAILED=0
TOTAL=0

echo "========================================="
echo "  Running All Non-Regression Tests"
echo "========================================="
echo ""


echo "Running: nrt_create_user_valid..."
if bash "fuzzing/non_regression_tests/nrt_create_user_valid.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_create_user_valid"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_create_user_valid"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_login_valid..."
if bash "fuzzing/non_regression_tests/nrt_login_valid.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_login_valid"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_login_valid"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_user_info..."
if bash "fuzzing/non_regression_tests/nrt_user_info.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_user_info"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_user_info"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_upload_document_valid..."
if bash "fuzzing/non_regression_tests/nrt_upload_document_valid.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_upload_document_valid"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_upload_document_valid"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_list_documents..."
if bash "fuzzing/non_regression_tests/nrt_list_documents.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_list_documents"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_list_documents"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_rmap_initiate_valid..."
if bash "fuzzing/non_regression_tests/nrt_rmap_initiate_valid.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_rmap_initiate_valid"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_rmap_initiate_valid"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_rmap_finalize_valid..."
if bash "fuzzing/non_regression_tests/nrt_rmap_finalize_valid.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_rmap_finalize_valid"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_rmap_finalize_valid"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_healthz..."
if bash "fuzzing/non_regression_tests/nrt_healthz.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_healthz"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_healthz"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "Running: nrt_healthz_verbose..."
if bash "fuzzing/non_regression_tests/nrt_healthz_verbose.sh" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: nrt_healthz_verbose"
    ((PASSED++))
else
    echo "✗ FAIL: nrt_healthz_verbose"
    ((FAILED++))
fi
((TOTAL++))
sleep 1  # Add delay to avoid rate limiting
echo ""

echo "========================================="
echo "  Non-Regression Test Summary"
echo "========================================="
echo "Total: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All non-regression tests passed!"
    echo "  All legitimate functionality still works"
    exit 0
else
    echo "✗ Some non-regression tests failed"
    echo "  Some legitimate functionality may be broken"
    exit 1
fi
