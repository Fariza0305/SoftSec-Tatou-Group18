#!/usr/bin/env python3
"""
Regression Test Generator for Tatou API Security Fixes

This script generates comprehensive regression tests for all security
vulnerabilities that have been fixed in the Tatou API.
"""

import os
import json
from datetime import datetime
from pathlib import Path

class RegressionTestGenerator:
    def __init__(self, output_dir="fuzzing/regression_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tests_generated = []
        
    def generate_xss_tests(self):
        """Generate XSS regression tests"""
        tests = [
            {
                'name': 'rt_xss_create_user_login',
                'description': 'Test XSS protection in create-user login field',
                'endpoint': '/api/create-user',
                'payload': '<script>alert("XSS")</script>',
                'field': 'login',
                'expected': 'blocked'
            },
            {
                'name': 'rt_xss_create_user_email',
                'description': 'Test XSS protection in create-user email field',
                'endpoint': '/api/create-user',
                'payload': '"><script>alert("XSS")</script>',
                'field': 'email',
                'expected': 'blocked'
            },
            {
                'name': 'rt_xss_img_onerror',
                'description': 'Test XSS protection against img onerror attack',
                'endpoint': '/api/create-user',
                'payload': '<img src=x onerror=alert("XSS")>',
                'field': 'login',
                'expected': 'blocked'
            },
            {
                'name': 'rt_xss_svg_onload',
                'description': 'Test XSS protection against SVG onload attack',
                'endpoint': '/api/create-user',
                'payload': '<svg onload=alert("XSS")>',
                'field': 'login',
                'expected': 'blocked'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_path_traversal_tests(self):
        """Generate path traversal regression tests"""
        tests = [
            {
                'name': 'rt_path_traversal_upload_basic',
                'description': 'Test path traversal protection in upload (../ attack)',
                'endpoint': '/api/upload-document',
                'payload': '../../../etc/passwd',
                'expected': 'blocked'
            },
            {
                'name': 'rt_path_traversal_upload_windows',
                'description': 'Test path traversal protection (Windows style)',
                'endpoint': '/api/upload-document',
                'payload': '..\\..\\..\\windows\\system32',
                'expected': 'blocked'
            },
            {
                'name': 'rt_path_traversal_rmap',
                'description': 'Test path traversal protection in rmap-initiate',
                'endpoint': '/api/rmap-initiate',
                'payload': '../../../etc/passwd',
                'expected': 'blocked'
            },
            {
                'name': 'rt_path_traversal_encoded',
                'description': 'Test path traversal protection (URL encoded)',
                'endpoint': '/api/upload-document',
                'payload': '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
                'expected': 'blocked'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_sql_injection_tests(self):
        """Generate SQL injection regression tests"""
        tests = [
            {
                'name': 'rt_sql_injection_login_or',
                'description': 'Test SQL injection protection (OR 1=1)',
                'endpoint': '/api/login',
                'payload': "' OR '1'='1",
                'field': 'email',
                'expected': 'blocked'
            },
            {
                'name': 'rt_sql_injection_login_union',
                'description': 'Test SQL injection protection (UNION SELECT)',
                'endpoint': '/api/login',
                'payload': "' UNION SELECT * FROM users --",
                'field': 'email',
                'expected': 'blocked'
            },
            {
                'name': 'rt_sql_injection_create_user',
                'description': 'Test SQL injection protection in create-user',
                'endpoint': '/api/create-user',
                'payload': "admin'--",
                'field': 'login',
                'expected': 'blocked'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_xxe_tests(self):
        """Generate XXE regression tests"""
        tests = [
            {
                'name': 'rt_xxe_rmap_basic',
                'description': 'Test XXE protection in rmap-initiate',
                'endpoint': '/api/rmap-initiate',
                'payload': '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
                'expected': 'blocked'
            },
            {
                'name': 'rt_xxe_rmap_external',
                'description': 'Test XXE protection (external entity)',
                'endpoint': '/api/rmap-initiate',
                'payload': '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/steal">]><root>&xxe;</root>',
                'expected': 'blocked'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_rate_limiting_tests(self):
        """Generate rate limiting regression tests"""
        tests = [
            {
                'name': 'rt_rate_limit_login',
                'description': 'Test rate limiting on login endpoint',
                'endpoint': '/api/login',
                'test_type': 'rate_limit',
                'expected': '429 after 5 requests'
            },
            {
                'name': 'rt_rate_limit_create_user',
                'description': 'Test rate limiting on create-user endpoint',
                'endpoint': '/api/create-user',
                'test_type': 'rate_limit',
                'expected': '429 after 5 requests'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_information_disclosure_tests(self):
        """Generate information disclosure regression tests"""
        tests = [
            {
                'name': 'rt_info_disclosure_invalid_json',
                'description': 'Test no stack traces on invalid JSON',
                'endpoint': '/api/login',
                'payload': '{"invalid": json}',
                'test_type': 'info_disclosure',
                'expected': 'no stack trace'
            },
            {
                'name': 'rt_info_disclosure_null_values',
                'description': 'Test no stack traces on null values',
                'endpoint': '/api/login',
                'payload': 'null',
                'test_type': 'info_disclosure',
                'expected': 'no stack trace'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def _generate_bash_test(self, test):
        """Generate a bash test script"""
        name = test['name']
        description = test['description']
        endpoint = test['endpoint']
        
        script = f"""#!/bin/bash
# Regression Test: {name}
# Description: {description}
# Generated: {datetime.now().isoformat()}

BASE_URL="${{1:-http://localhost:5000}}"
TEST_NAME="{name}"

echo "Running regression test: $TEST_NAME"
echo "Description: {description}"
echo ""

"""
        
        if test.get('test_type') == 'rate_limit':
            # Rate limiting test
            script += f"""# Test rate limiting
echo "Testing rate limiting on {endpoint}..."
COUNT=0
for i in {{1..10}}; do
    RESPONSE=$(curl -s -w "\\n%{{http_code}}" -X POST "$BASE_URL{endpoint}" \\
        -H "Content-Type: application/json" \\
        -d '{{"email":"test$i@test.com","password":"test123"}}' 2>/dev/null)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    
    if [ "$HTTP_CODE" = "429" ]; then
        echo "✓ Rate limit triggered after $i requests"
        exit 0
    fi
done

echo "✗ FAIL: No rate limiting detected after 10 requests"
exit 1
"""
        
        elif test.get('test_type') == 'info_disclosure':
            # Information disclosure test
            payload = test['payload'].replace('"', '\\"')
            script += f"""# Test information disclosure protection
RESPONSE=$(curl -s -X POST "$BASE_URL{endpoint}" \\
    -H "Content-Type: application/json" \\
    -d '{payload}' 2>/dev/null)

if echo "$RESPONSE" | grep -qE "(Traceback|File \\"|line [0-9]+|Exception:|stack trace)"; then
    echo "✗ FAIL: Stack trace found in response"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: No stack trace in response"
    exit 0
fi
"""
        
        elif 'field' in test:
            # Field-based payload test (XSS, SQL injection)
            payload = test['payload'].replace('"', '\\"').replace("'", "\\'")
            field = test['field']
            
            if endpoint == '/api/login':
                script += f"""# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL{endpoint}" \\
    -H "Content-Type: application/json" \\
    -d '{{{{"email":"{payload}","password":"test123"}}}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '{test['payload']}'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
"""
            else:
                script += f"""# Test payload injection
RESPONSE=$(curl -s -X POST "$BASE_URL{endpoint}" \\
    -H "Content-Type: application/json" \\
    -d '{{{{"login":"{payload}","email":"test@test.com","password":"test123"}}}}' 2>/dev/null)

# Check if payload was blocked (not reflected in response)
if echo "$RESPONSE" | grep -qF '{test['payload']}'; then
    echo "✗ FAIL: Payload was not blocked"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Payload was blocked"
    exit 0
fi
"""
        
        else:
            # Path-based payload test (path traversal, XXE)
            payload = test['payload'].replace('"', '\\"')
            
            if endpoint == '/api/upload-document':
                script += f"""# Test path traversal in file upload
# First create a test user and login
USER_EMAIL="test_$(date +%s)@test.com"
curl -s -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
    -d '{{"login":"testuser","email":"'$USER_EMAIL'","password":"test123"}}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \\
    -H "Content-Type: application/json" \\
    -d '{{"email":"'$USER_EMAIL'","password":"test123"}}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate"
    exit 1
fi

# Test malicious filename
RESPONSE=$(curl -s -X POST "$BASE_URL{endpoint}" \\
    -H "Authorization: Bearer $TOKEN" \\
    -F "file=@/dev/null;filename={payload}" 2>/dev/null)

# Check if path traversal was blocked
if echo "$RESPONSE" | grep -qE "(error|invalid|forbidden|denied)"; then
    echo "✓ PASS: Path traversal was blocked"
    exit 0
else
    echo "✗ FAIL: Path traversal may not be blocked"
    echo "$RESPONSE"
    exit 1
fi
"""
            else:
                # RMAP endpoint
                script += f"""# Test payload injection in RMAP
RESPONSE=$(curl -s -X POST "$BASE_URL{endpoint}" \\
    -H "Content-Type: application/xml" \\
    -d '{payload}' 2>/dev/null)

# Check for indicators of successful attack
if echo "$RESPONSE" | grep -qE "(root:|/etc/passwd|file:///|ENTITY)"; then
    echo "✗ FAIL: Attack may have succeeded"
    echo "$RESPONSE"
    exit 1
else
    echo "✓ PASS: Attack was blocked"
    exit 0
fi
"""
        
        # Write the test file
        test_file = self.output_dir / f"{name}.sh"
        with open(test_file, 'w') as f:
            f.write(script)
        
        # Make executable
        os.chmod(test_file, 0o755)
        
        self.tests_generated.append({
            'name': name,
            'description': description,
            'file': str(test_file)
        })
        
        print(f"✓ Generated: {name}.sh")
    
    def generate_all_tests(self):
        """Generate all regression tests"""
        print("=" * 60)
        print("Generating Regression Tests")
        print("=" * 60)
        print()
        
        print("Generating XSS tests...")
        self.generate_xss_tests()
        print()
        
        print("Generating path traversal tests...")
        self.generate_path_traversal_tests()
        print()
        
        print("Generating SQL injection tests...")
        self.generate_sql_injection_tests()
        print()
        
        print("Generating XXE tests...")
        self.generate_xxe_tests()
        print()
        
        print("Generating rate limiting tests...")
        self.generate_rate_limiting_tests()
        print()
        
        print("Generating information disclosure tests...")
        self.generate_information_disclosure_tests()
        print()
        
        print("=" * 60)
        print(f"Total tests generated: {len(self.tests_generated)}")
        print("=" * 60)
        
        # Generate a master test runner
        self._generate_master_runner()
        
        # Generate test documentation
        self._generate_test_documentation()
    
    def _generate_master_runner(self):
        """Generate master test runner script"""
        script = f"""#!/bin/bash
# Master Regression Test Runner
# Generated: {datetime.now().isoformat()}

BASE_URL="${{1:-http://localhost:5000}}"
PASSED=0
FAILED=0
TOTAL=0

echo "========================================="
echo "  Running All Regression Tests"
echo "========================================="
echo ""

"""
        
        for test in self.tests_generated:
            script += f"""
echo "Running: {test['name']}..."
if bash "{test['file']}" "$BASE_URL" > /dev/null 2>&1; then
    echo "✓ PASS: {test['name']}"
    ((PASSED++))
else
    echo "✗ FAIL: {test['name']}"
    ((FAILED++))
fi
((TOTAL++))
echo ""
"""
        
        script += """
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
"""
        
        runner_file = self.output_dir / "run_all_regression_tests.sh"
        with open(runner_file, 'w') as f:
            f.write(script)
        
        os.chmod(runner_file, 0o755)
        print(f"✓ Generated master runner: {runner_file}")
    
    def _generate_test_documentation(self):
        """Generate test documentation"""
        doc = f"""# Regression Test Suite Documentation

Generated: {datetime.now().isoformat()}

## Overview

This regression test suite verifies that all security vulnerabilities
that have been fixed in the Tatou API remain fixed.

## Test Categories

### XSS Protection Tests
Tests that verify Cross-Site Scripting (XSS) attacks are properly blocked.

"""
        
        # Group tests by category
        categories = {
            'XSS': [],
            'Path Traversal': [],
            'SQL Injection': [],
            'XXE': [],
            'Rate Limiting': [],
            'Information Disclosure': []
        }
        
        for test in self.tests_generated:
            name = test['name']
            if 'xss' in name:
                categories['XSS'].append(test)
            elif 'path_traversal' in name:
                categories['Path Traversal'].append(test)
            elif 'sql_injection' in name:
                categories['SQL Injection'].append(test)
            elif 'xxe' in name:
                categories['XXE'].append(test)
            elif 'rate_limit' in name:
                categories['Rate Limiting'].append(test)
            elif 'info_disclosure' in name:
                categories['Information Disclosure'].append(test)
        
        for category, tests in categories.items():
            if tests:
                doc += f"\n### {category} Tests\n\n"
                for test in tests:
                    doc += f"- **{test['name']}**: {test['description']}\n"
        
        doc += f"""

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

## Total Tests: {len(self.tests_generated)}
"""
        
        doc_file = self.output_dir / "REGRESSION_TESTS_README.md"
        with open(doc_file, 'w') as f:
            f.write(doc)
        
        print(f"✓ Generated documentation: {doc_file}")

def main():
    generator = RegressionTestGenerator()
    generator.generate_all_tests()

if __name__ == "__main__":
    main()

