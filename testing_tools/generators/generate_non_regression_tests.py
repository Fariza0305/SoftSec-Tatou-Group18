#!/usr/bin/env python3
"""
Non-Regression Test Generator for Tatou API

This script generates non-regression tests to verify that legitimate
functionality still works after security fixes have been applied.
"""

import os
import json
from datetime import datetime
from pathlib import Path

class NonRegressionTestGenerator:
    def __init__(self, output_dir="fuzzing/non_regression_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tests_generated = []
        
    def generate_user_management_tests(self):
        """Generate tests for normal user management operations"""
        tests = [
            {
                'name': 'nrt_create_user_valid',
                'description': 'Test valid user creation still works',
                'endpoint': '/api/create-user',
                'test_type': 'valid_user_creation'
            },
            {
                'name': 'nrt_login_valid',
                'description': 'Test valid user login still works',
                'endpoint': '/api/login',
                'test_type': 'valid_login'
            },
            {
                'name': 'nrt_user_info',
                'description': 'Test getting user info still works',
                'endpoint': '/api/user/info',
                'test_type': 'user_info'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_document_tests(self):
        """Generate tests for normal document operations"""
        tests = [
            {
                'name': 'nrt_upload_document_valid',
                'description': 'Test valid document upload still works',
                'endpoint': '/api/upload-document',
                'test_type': 'valid_upload'
            },
            {
                'name': 'nrt_list_documents',
                'description': 'Test listing documents still works',
                'endpoint': '/api/documents',
                'test_type': 'list_documents'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_rmap_tests(self):
        """Generate tests for normal RMAP operations"""
        tests = [
            {
                'name': 'nrt_rmap_initiate_valid',
                'description': 'Test valid RMAP initiate still works',
                'endpoint': '/api/rmap-initiate',
                'test_type': 'rmap_initiate'
            },
            {
                'name': 'nrt_rmap_finalize_valid',
                'description': 'Test valid RMAP finalize still works',
                'endpoint': '/api/rmap-finalize',
                'test_type': 'rmap_finalize'
            }
        ]
        
        for test in tests:
            self._generate_bash_test(test)
        
        return tests
    
    def generate_healthcheck_tests(self):
        """Generate tests for healthcheck endpoints"""
        tests = [
            {
                'name': 'nrt_healthz',
                'description': 'Test healthz endpoint',
                'endpoint': '/healthz',
                'test_type': 'healthcheck'
            },
            {
                'name': 'nrt_healthz_verbose',
                'description': 'Test verbose healthz endpoint',
                'endpoint': '/healthz-verbose',
                'test_type': 'healthcheck_verbose'
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
        test_type = test.get('test_type')
        
        script = f"""#!/bin/bash
# Non-Regression Test: {name}
# Description: {description}
# Generated: {datetime.now().isoformat()}

BASE_URL="${{1:-http://localhost:5000}}"
TEST_NAME="{name}"

echo "Running non-regression test: $TEST_NAME"
echo "Description: {description}"
echo ""

"""
        
        if test_type == 'valid_user_creation':
            script += """# Test valid user creation
TIMESTAMP=$(date +%s)
USER_EMAIL="validuser_${TIMESTAMP}@test.com"
USER_LOGIN="validuser_${TIMESTAMP}"

RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
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
"""
        
        elif test_type == 'valid_login':
            script += """# Test valid user login
# First create a user
TIMESTAMP=$(date +%s)
USER_EMAIL="logintest_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
    -d '{"login":"logintest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

# Now try to login
RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$BASE_URL/api/login" \\
    -H "Content-Type: application/json" \\
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "token"; then
    echo "✓ PASS: Valid login works"
    echo "Got token successfully"
    exit 0
else
    echo "✗ FAIL: Valid login failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
"""
        
        elif test_type == 'user_info':
            script += """# Test getting user info
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="userinfo_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
    -d '{"login":"userinfotest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \\
    -H "Content-Type: application/json" \\
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for user info test"
    exit 1
fi

# Get user info
RESPONSE=$(curl -s -w "\\n%{http_code}" -X GET "$BASE_URL/api/user/info" \\
    -H "Authorization: Bearer $TOKEN" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: User info retrieval works"
    exit 0
else
    echo "✗ FAIL: User info retrieval failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
"""
        
        elif test_type == 'valid_upload':
            script += """# Test valid document upload
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="upload_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
    -d '{"login":"uploadtest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \\
    -H "Content-Type: application/json" \\
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for upload test"
    exit 1
fi

# Create a valid test file
echo "This is a test document" > /tmp/test_doc_${TIMESTAMP}.txt

# Upload the document
RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$BASE_URL/api/upload-document" \\
    -H "Authorization: Bearer $TOKEN" \\
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
"""
        
        elif test_type == 'list_documents':
            script += """# Test listing documents
# First create and login
TIMESTAMP=$(date +%s)
USER_EMAIL="listdocs_${TIMESTAMP}@test.com"

curl -s -X POST "$BASE_URL/api/create-user" \\
    -H "Content-Type: application/json" \\
    -d '{"login":"listdocstest","email":"'"$USER_EMAIL"'","password":"TestPass123!"}' > /dev/null

sleep 1

TOKEN=$(curl -s -X POST "$BASE_URL/api/login" \\
    -H "Content-Type: application/json" \\
    -d '{"email":"'"$USER_EMAIL"'","password":"TestPass123!"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "✗ FAIL: Could not authenticate for list documents test"
    exit 1
fi

# List documents
RESPONSE=$(curl -s -w "\\n%{http_code}" -X GET "$BASE_URL/api/documents" \\
    -H "Authorization: Bearer $TOKEN" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: List documents works"
    exit 0
else
    echo "✗ FAIL: List documents failed with code $HTTP_CODE"
    exit 1
fi
"""
        
        elif test_type == 'rmap_initiate':
            script += """# Test RMAP initiate with valid data
VALID_XML='<?xml version="1.0" encoding="UTF-8"?>
<rmap>
  <identity>test@example.com</identity>
  <document>test-document</document>
</rmap>'

RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$BASE_URL/api/rmap-initiate" \\
    -H "Content-Type: application/xml" \\
    -d "$VALID_XML" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✓ PASS: RMAP initiate endpoint responds (may return error for unknown identity, which is expected)"
    exit 0
else
    echo "✗ FAIL: RMAP initiate failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
"""
        
        elif test_type == 'rmap_finalize':
            script += """# Test RMAP finalize with valid data
VALID_XML='<?xml version="1.0" encoding="UTF-8"?>
<rmap>
  <session>test-session</session>
  <status>complete</status>
</rmap>'

RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$BASE_URL/api/rmap-finalize" \\
    -H "Content-Type: application/xml" \\
    -d "$VALID_XML" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✓ PASS: RMAP finalize endpoint responds (may return error for unknown session, which is expected)"
    exit 0
else
    echo "✗ FAIL: RMAP finalize failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
"""
        
        elif test_type == 'healthcheck':
            script += """# Test healthz endpoint
RESPONSE=$(curl -s -w "\\n%{http_code}" -X GET "$BASE_URL/healthz" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "ok"; then
    echo "✓ PASS: Healthz endpoint works"
    exit 0
else
    echo "✗ FAIL: Healthz endpoint failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
"""
        
        elif test_type == 'healthcheck_verbose':
            script += """# Test healthz-verbose endpoint
RESPONSE=$(curl -s -w "\\n%{http_code}" -X GET "$BASE_URL/healthz-verbose" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ PASS: Healthz-verbose endpoint works"
    exit 0
else
    echo "✗ FAIL: Healthz-verbose endpoint failed with code $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
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
        """Generate all non-regression tests"""
        print("=" * 60)
        print("Generating Non-Regression Tests")
        print("=" * 60)
        print()
        
        print("Generating user management tests...")
        self.generate_user_management_tests()
        print()
        
        print("Generating document operation tests...")
        self.generate_document_tests()
        print()
        
        print("Generating RMAP operation tests...")
        self.generate_rmap_tests()
        print()
        
        print("Generating healthcheck tests...")
        self.generate_healthcheck_tests()
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
# Master Non-Regression Test Runner
# Generated: {datetime.now().isoformat()}

BASE_URL="${{1:-http://localhost:5000}}"
PASSED=0
FAILED=0
TOTAL=0

echo "========================================="
echo "  Running All Non-Regression Tests"
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
sleep 1  # Add delay to avoid rate limiting
echo ""
"""
        
        script += """
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
"""
        
        runner_file = self.output_dir / "run_all_non_regression_tests.sh"
        with open(runner_file, 'w') as f:
            f.write(script)
        
        os.chmod(runner_file, 0o755)
        print(f"✓ Generated master runner: {runner_file}")
    
    def _generate_test_documentation(self):
        """Generate test documentation"""
        doc = f"""# Non-Regression Test Suite Documentation

Generated: {datetime.now().isoformat()}

## Overview

This non-regression test suite verifies that legitimate functionality
still works correctly after security fixes have been applied to the Tatou API.

## Purpose

Security fixes should not break legitimate functionality. These tests ensure:
- Valid users can still be created
- Valid logins still work
- Document operations still function
- RMAP operations are still accessible
- Healthcheck endpoints still respond

## Test Categories

### User Management Tests
Tests that verify user creation, login, and info retrieval still work properly.

"""
        
        # Group tests by category
        categories = {
            'User Management': [],
            'Document Operations': [],
            'RMAP Operations': [],
            'Healthcheck': []
        }
        
        for test in self.tests_generated:
            name = test['name']
            if 'user' in name or 'login' in name:
                categories['User Management'].append(test)
            elif 'document' in name or 'upload' in name:
                categories['Document Operations'].append(test)
            elif 'rmap' in name:
                categories['RMAP Operations'].append(test)
            elif 'healthz' in name:
                categories['Healthcheck'].append(test)
        
        for category, tests in categories.items():
            if tests:
                doc += f"\n### {category} Tests\n\n"
                for test in tests:
                    doc += f"- **{test['name']}**: {test['description']}\n"
        
        doc += f"""

## Running the Tests

### Run All Tests
```bash
cd fuzzing/non_regression_tests
./run_all_non_regression_tests.sh [BASE_URL]
```

### Run Individual Test
```bash
cd fuzzing/non_regression_tests
./nrt_create_user_valid.sh [BASE_URL]
```

### Default Base URL
If no BASE_URL is provided, tests will use `http://localhost:5000`

## Expected Results

All non-regression tests should pass, indicating that:
- Security fixes have not broken legitimate functionality
- The API still handles valid requests correctly
- All core features remain operational

## Total Tests: {len(self.tests_generated)}
"""
        
        doc_file = self.output_dir / "NON_REGRESSION_TESTS_README.md"
        with open(doc_file, 'w') as f:
            f.write(doc)
        
        print(f"✓ Generated documentation: {doc_file}")

def main():
    generator = NonRegressionTestGenerator()
    generator.generate_all_tests()

if __name__ == "__main__":
    main()

