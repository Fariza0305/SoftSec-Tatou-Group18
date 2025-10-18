# Regression Test Suite Documentation

Generated: 2025-10-17T18:58:26.237084

## Overview

This regression test suite verifies that all security vulnerabilities
that have been fixed in the Tatou API remain fixed.

## Test Categories

### XSS Protection Tests
Tests that verify Cross-Site Scripting (XSS) attacks are properly blocked.


### XSS Tests

- **rt_xss_create_user_login**: Test XSS protection in create-user login field
- **rt_xss_create_user_email**: Test XSS protection in create-user email field
- **rt_xss_img_onerror**: Test XSS protection against img onerror attack
- **rt_xss_svg_onload**: Test XSS protection against SVG onload attack

### Path Traversal Tests

- **rt_path_traversal_upload_basic**: Test path traversal protection in upload (../ attack)
- **rt_path_traversal_upload_windows**: Test path traversal protection (Windows style)
- **rt_path_traversal_rmap**: Test path traversal protection in rmap-initiate
- **rt_path_traversal_encoded**: Test path traversal protection (URL encoded)

### SQL Injection Tests

- **rt_sql_injection_login_or**: Test SQL injection protection (OR 1=1)
- **rt_sql_injection_login_union**: Test SQL injection protection (UNION SELECT)
- **rt_sql_injection_create_user**: Test SQL injection protection in create-user

### XXE Tests

- **rt_xxe_rmap_basic**: Test XXE protection in rmap-initiate
- **rt_xxe_rmap_external**: Test XXE protection (external entity)

### Rate Limiting Tests

- **rt_rate_limit_login**: Test rate limiting on login endpoint
- **rt_rate_limit_create_user**: Test rate limiting on create-user endpoint

### Information Disclosure Tests

- **rt_info_disclosure_invalid_json**: Test no stack traces on invalid JSON
- **rt_info_disclosure_null_values**: Test no stack traces on null values


## Running the Tests

### Run All Tests
```bash
cd fuzzing/regression_tests
./run_all_regression_tests.sh [BASE_URL]
```

### Run Individual Test
```bash
cd fuzzing/regression_tests
./rt_xss_create_user_login.sh [BASE_URL]
```

### Default Base URL
If no BASE_URL is provided, tests will use `http://localhost:5000`

## Test Results

All tests should pass if security fixes are properly implemented.
A test passes if:
- Malicious payloads are blocked
- No sensitive information is disclosed
- Rate limiting triggers as expected
- Error messages don't contain stack traces

## Total Tests: 17
