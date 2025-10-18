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
