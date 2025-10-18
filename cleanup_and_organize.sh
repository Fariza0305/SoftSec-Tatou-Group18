#!/bin/bash
# Cleanup and Organize Testing Files
# This script organizes test files and removes temporary/redundant files

echo "========================================="
echo "  Cleanup and Organization Script"
echo "========================================="
echo ""

# Create organized directory structure
echo "Creating organized directory structure..."
mkdir -p testing_tools
mkdir -p testing_tools/fuzzers
mkdir -p testing_tools/generators
mkdir -p testing_tools/validators
mkdir -p testing_results
mkdir -p testing_results/archived

# Move fuzzer tools
echo "Organizing fuzzer tools..."
mv -f advanced_fuzzer.py testing_tools/fuzzers/ 2>/dev/null
mv -f smart_fuzzer.py testing_tools/fuzzers/ 2>/dev/null
mv -f comprehensive_fuzzer.py testing_tools/fuzzers/ 2>/dev/null
mv -f api_test.py testing_tools/fuzzers/ 2>/dev/null

# Move generators
echo "Organizing test generators..."
mv -f generate_regression_tests.py testing_tools/generators/ 2>/dev/null
mv -f generate_non_regression_tests.py testing_tools/generators/ 2>/dev/null

# Move validator scripts
echo "Organizing validation scripts..."
mv -f test_security_fixes.sh testing_tools/validators/ 2>/dev/null
mv -f test_http_methods_fix.sh testing_tools/validators/ 2>/dev/null
mv -f test_server.sh testing_tools/validators/ 2>/dev/null
mv -f better_fuzzing.sh testing_tools/validators/ 2>/dev/null
mv -f detailed_fuzzing.sh testing_tools/validators/ 2>/dev/null
mv -f advanced_fuzzing.sh testing_tools/validators/ 2>/dev/null

# Archive fuzzing results
echo "Archiving fuzzing results..."
mv -f fuzzing_results_*.json testing_results/archived/ 2>/dev/null
mv -f advanced_fuzzing_results_*.json testing_results/archived/ 2>/dev/null
mv -f smart_fuzzing_results_*.json testing_results/archived/ 2>/dev/null

# Create a README for the testing tools directory
cat > testing_tools/README.md << 'EOF'
# Testing Tools Directory

This directory contains all security testing tools used in the Tatou API security assessment.

## Directory Structure

### fuzzers/
Contains fuzzing tools for discovering vulnerabilities:
- `advanced_fuzzer.py` - Comprehensive vulnerability scanning
- `smart_fuzzer.py` - Rate-limit-aware intelligent fuzzing
- `comprehensive_fuzzer.py` - Full-spectrum security testing
- `api_test.py` - Basic API functionality testing

### generators/
Contains test generation tools:
- `generate_regression_tests.py` - Generates regression test suite
- `generate_non_regression_tests.py` - Generates functionality validation tests

### validators/
Contains validation and verification scripts:
- `test_security_fixes.sh` - Quick validation of security fixes
- `test_http_methods_fix.sh` - HTTP method security validation
- `test_server.sh` - Basic server functionality test
- `better_fuzzing.sh` - Enhanced fuzzing campaign
- `detailed_fuzzing.sh` - Detailed vulnerability scanning
- `advanced_fuzzing.sh` - Advanced fuzzing scenarios

## Usage

### Running Fuzzers
```bash
cd testing_tools/fuzzers
python3 advanced_fuzzer.py http://localhost:5000
python3 smart_fuzzer.py http://localhost:5000
```

### Generating Tests
```bash
cd testing_tools/generators
python3 generate_regression_tests.py
python3 generate_non_regression_tests.py
```

### Running Validators
```bash
cd testing_tools/validators
./test_security_fixes.sh
./better_fuzzing.sh
```

## Test Suites

The actual test suites are located in:
- `../fuzzing/regression_tests/` - Regression test suite (17 tests)
- `../fuzzing/non_regression_tests/` - Non-regression test suite (9 tests)

## Results

Test results are archived in:
- `../testing_results/archived/` - Historical fuzzing results
EOF

# Create a README for testing results
cat > testing_results/README.md << 'EOF'
# Testing Results Directory

This directory contains results from security testing campaigns.

## Directory Structure

### archived/
Historical fuzzing results from security assessment campaigns.

## Results Summary

All security vulnerabilities discovered during testing have been fixed and validated.

See the main project documentation for detailed reports:
- `../FINAL_SECURITY_REPORT.md` - Comprehensive security report
- `../SECURITY_FIXES_APPLIED.md` - Detailed fix documentation
- `../fuzzing/FUZZING_REPORT.md` - Fuzzing campaign results
EOF

# Make validator scripts executable
echo "Setting permissions..."
chmod +x testing_tools/validators/*.sh 2>/dev/null

# Create a master tool index
cat > TESTING_TOOLS_INDEX.md << 'EOF'
# Testing Tools Index

Quick reference guide for all security testing tools.

## Quick Start

### 1. Run Security Validation
```bash
cd testing_tools/validators
./test_security_fixes.sh
```

### 2. Run Regression Tests
```bash
cd fuzzing/regression_tests
./run_all_regression_tests.sh
```

### 3. Run Non-Regression Tests
```bash
cd fuzzing/non_regression_tests
./run_all_non_regression_tests.sh
```

### 4. Generate New Tests
```bash
cd testing_tools/generators
python3 generate_regression_tests.py
python3 generate_non_regression_tests.py
```

### 5. Run Full Fuzzing Campaign
```bash
cd testing_tools/fuzzers
python3 smart_fuzzer.py http://localhost:5000
```

## Tool Categories

### Security Validators (Quick Check)
- `testing_tools/validators/test_security_fixes.sh` ⚡ Fast validation
- `testing_tools/validators/test_http_methods_fix.sh` 🔒 HTTP method check

### Regression Tests (Prevent Regressions)
- `fuzzing/regression_tests/run_all_regression_tests.sh` 🛡️ 17 tests
- Individual tests in `fuzzing/regression_tests/rt_*.sh`

### Non-Regression Tests (Verify Functionality)
- `fuzzing/non_regression_tests/run_all_non_regression_tests.sh` ✅ 9 tests
- Individual tests in `fuzzing/non_regression_tests/nrt_*.sh`

### Fuzzers (Discovery)
- `testing_tools/fuzzers/advanced_fuzzer.py` 🔍 Comprehensive scan
- `testing_tools/fuzzers/smart_fuzzer.py` 🧠 Intelligent testing

### Test Generators
- `testing_tools/generators/generate_regression_tests.py` 📝 Create regression tests
- `testing_tools/generators/generate_non_regression_tests.py` 📝 Create functionality tests

## Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| XSS Protection | 4 | ✅ 100% |
| Path Traversal | 4 | ✅ 100% |
| SQL Injection | 3 | ✅ 100% |
| XXE Protection | 2 | ✅ 100% |
| Rate Limiting | 2 | ✅ 100% |
| Info Disclosure | 2 | ✅ 100% |
| User Management | 3 | ✅ 100% |
| Document Operations | 2 | ✅ 100% |
| RMAP Operations | 2 | ✅ 100% |
| Healthcheck | 2 | ✅ 100% |

## Documentation

- 📋 `FINAL_SECURITY_REPORT.md` - Complete security assessment report
- 🔧 `SECURITY_FIXES_APPLIED.md` - Detailed fix documentation
- 🎯 `fuzzing/FUZZING_REPORT.md` - Fuzzing methodology and results
- 📖 `fuzzing/regression_tests/REGRESSION_TESTS_README.md` - Regression test guide
- 📖 `fuzzing/non_regression_tests/NON_REGRESSION_TESTS_README.md` - Functionality test guide
- 🛠️ `testing_tools/README.md` - Testing tools documentation

EOF

echo ""
echo "✓ Testing tools organized in: testing_tools/"
echo "✓ Test results archived in: testing_results/archived/"
echo "✓ Created documentation:"
echo "  - testing_tools/README.md"
echo "  - testing_results/README.md"
echo "  - TESTING_TOOLS_INDEX.md"
echo ""
echo "========================================="
echo "  Cleanup Complete"
echo "========================================="


