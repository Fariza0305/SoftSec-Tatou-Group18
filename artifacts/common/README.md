# Common Artifacts

This folder contains shared artifacts and resources used by all team members across different specializations.

## Contents

### Coverage Reports
Located in `coverage/` directory:
- Test coverage data and reports
- Code coverage metrics
- Coverage analysis results

### Unit Tests
Located in `tests/` directory:
- Shared unit test suite
- Common test utilities
- Test fixtures and helpers
- **conftest.py** - Pytest configuration and fixtures

#### Test Categories
- Authentication tests
- Watermarking functionality tests
- API endpoint tests
- Security feature tests
- Database interaction tests
- QR code generation tests
- RMAP integration tests

### Documentation
Located in `docs/` directory:

#### Project Specifications
- **Platform_specifications.md** - Complete platform specifications and requirements

#### Testing Documentation
- **TESTING_COMPLETE.txt** - Comprehensive testing documentation
  - Unit test descriptions
  - Integration test scenarios
  - Test coverage analysis
  - Testing methodology

#### Project Status
- **PROJECT_STATUS.txt** - Current project status and milestone tracking
  - Completed features
  - Security fixes implemented
  - Known issues
  - Future enhancements

## Test Suite Overview

The common test suite provides comprehensive coverage of:

### 1. Authentication & Authorization
- User registration and login
- Session management
- Password security
- Token validation

### 2. Watermarking Features
- Text watermark application
- QR code watermark generation
- Position and styling options
- PDF manipulation

### 3. API Security
- Input validation
- XSS prevention
- SQL injection protection
- Path traversal defense
- XXE protection
- Rate limiting

### 4. RMAP Integration
- RMAP initiation
- Data encryption/decryption
- Key management
- RMAP finalization

### 5. Database Operations
- User management
- Document storage
- Query security
- Transaction handling

## Running Tests

### Prerequisites
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test Categories
```bash
# Authentication tests
pytest tests/test_auth*.py

# Watermarking tests
pytest tests/test_watermark*.py

# Security tests
pytest tests/test_security*.py

# RMAP tests
pytest tests/test_rmap*.py
```

## Coverage Goals

Target coverage metrics:
- **Overall Coverage**: > 80%
- **Critical Security Functions**: 100%
- **API Endpoints**: > 90%
- **Core Business Logic**: > 85%

## Test Infrastructure

### Fixtures
Common test fixtures provided in `conftest.py`:
- Test database setup/teardown
- Mock user accounts
- Sample PDF files
- API client configuration

### Test Data
Standardized test data for:
- User credentials
- PDF documents
- Watermark configurations
- Security payloads

## Quality Assurance

### Continuous Integration
- Automated testing on every commit
- Coverage tracking over time
- Regression test suite
- Security test validation

### Test Maintenance
- Regular test review and updates
- Deprecated test removal
- New feature test coverage
- Bug reproduction tests

## Documentation Standards

All shared documentation follows:
- Markdown formatting
- Clear structure and headings
- Code examples where applicable
- Version tracking

## Collaboration

These common artifacts serve as:
- Shared testing baseline
- Integration point between specializations
- Quality assurance foundation
- Documentation reference

## Usage by Team Members

### Fuzzing Specialization (Palizha Hayilati)
- Uses test suite as baseline for fuzzing targets
- Validates fuzzing results against unit tests
- Contributes security test cases

### Operational Security (Wenyi Duan)
- Monitors test coverage metrics
- Analyzes test logs for security events
- Uses specs for threat modeling

### Offensive Operations (Chengyu Hu)
- Reviews tests for security gaps
- Identifies untested attack vectors
- Validates fixes with test suite

## Contributing

When adding to common artifacts:
1. Ensure compatibility with all specializations
2. Document thoroughly
3. Update this README
4. Maintain test quality standards
5. Follow project conventions

## Maintenance

Common artifacts are maintained by all team members:
- Tests: Updated when features change
- Coverage: Monitored continuously
- Documentation: Kept current with development
- Specifications: Version controlled

---

For specialization-specific artifacts, see the respective member folders:
- `fuzzing-Palizha Hayilati/`
- `operational-security-Wenyi Duan/`
- `offensive-operations-Chengyu Hu/`

