# Non-Regression Test Suite Documentation

Generated: 2025-10-17T18:59:33.733037

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


### User Management Tests

- **nrt_create_user_valid**: Test valid user creation still works
- **nrt_login_valid**: Test valid user login still works
- **nrt_user_info**: Test getting user info still works

### Document Operations Tests

- **nrt_upload_document_valid**: Test valid document upload still works
- **nrt_list_documents**: Test listing documents still works

### RMAP Operations Tests

- **nrt_rmap_initiate_valid**: Test valid RMAP initiate still works
- **nrt_rmap_finalize_valid**: Test valid RMAP finalize still works

### Healthcheck Tests

- **nrt_healthz**: Test healthz endpoint
- **nrt_healthz_verbose**: Test verbose healthz endpoint


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

## Total Tests: 9
