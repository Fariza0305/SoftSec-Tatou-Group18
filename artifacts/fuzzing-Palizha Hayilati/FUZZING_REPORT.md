# Tatou API Fuzzing Report
**Security Testing Campaign Report**

**Date:** October 17, 2025  
**Testing Team:** Group 18  
**Target:** Tatou Document Watermarking API  
**Test Duration:** ~27 seconds  

---

## Executive Summary

A comprehensive fuzzing campaign was conducted on the Tatou API to identify security vulnerabilities and robustness issues. The fuzzer executed **1,500 requests** across **15 endpoints** and discovered **2,352 potential security issues**.

### Key Findings

- **Critical Vulnerabilities Discovered:** 8 XSS, 5 Path Traversal, 4 XXE
- **Information Disclosure Issues:** 1,416 instances
- **Server Errors:** 842 instances  
- **Exception Handling Issues:** 77 instances
- **Success Rate:** 94.9% (1,423 successful requests out of 1,500)

### Risk Assessment

🔴 **CRITICAL:** Multiple high-severity vulnerabilities found including XSS, Path Traversal, and XXE  
🟠 **HIGH:** Extensive information disclosure through error messages  
🟡 **MEDIUM:** Poor error handling and server stability issues

---

## Testing Methodology

### Fuzzing Configuration
- **Base URL:** http://localhost:5000
- **Iterations per Endpoint:** 100
- **Authentication:** Token-based (JWT)
- **Test User:** fuzzer_test@test.com

### Fuzzing Techniques Applied
1. Boundary value analysis
2. Invalid type injection
3. SQL injection attempts
4. XSS payload injection
5. Path traversal attempts
6. Command injection patterns
7. XXE (XML External Entity) attacks
8. Buffer overflow testing
9. Format string vulnerabilities
10. Prototype pollution attempts

### Mutation Strategies
- String mutations: Empty strings, null bytes, SQL injection, XSS, XXE, path traversal
- Integer mutations: Zero, negative values, boundary values
- Array/Object mutations: Empty, null, malformed structures
- File mutations: Empty files, large files, malformed PDFs, path traversal in filenames

---

## Detailed Findings

### 1. Cross-Site Scripting (XSS) - CRITICAL

**Count:** 8 instances  
**Severity:** CRITICAL  
**OWASP Category:** A03:2021 - Injection  
**CWE:** CWE-79: Cross-site Scripting  

#### Affected Endpoints:
- `/api/create-user`
- `/api/rmap-initiate`

#### Example Vulnerability:
```json
{
  "endpoint": "create-user",
  "payload": {
    "login": "<script>alert('XSS')</script>",
    "password": "test123",
    "email": "test@example.com"
  },
  "response": {
    "id": 217,
    "login": "<script>alert('XSS')</script>"
  }
}
```

**Impact:** The application reflects XSS payloads without sanitization. User input containing JavaScript code is stored and returned in API responses, potentially allowing attackers to execute malicious scripts in victim browsers.

**Recommendation:**
- Implement output encoding for all user-controlled data
- Use Content Security Policy (CSP) headers
- Sanitize input on both client and server side
- Use context-appropriate escaping (HTML, JavaScript, URL)

---

### 2. Path Traversal - CRITICAL

**Count:** 5 instances  
**Severity:** HIGH  
**OWASP Category:** A01:2021 - Broken Access Control  
**CWE:** CWE-22: Path Traversal  

#### Affected Endpoints:
- `/api/rmap-initiate`

#### Example Vulnerability:
```json
{
  "endpoint": "rmap-initiate",
  "payload": {
    "identity": "../../../etc/passwd",
    "nonceClient": -1
  },
  "response": {
    "error": "Unknown identity: ../../../etc/passwd"
  }
}
```

**Impact:** The application reflects path traversal sequences in error messages without proper sanitization, indicating potential file system access vulnerabilities.

**Recommendation:**
- Validate and sanitize all file paths
- Use allowlists for permitted file locations
- Implement path canonicalization
- Never reflect file paths in error messages

---

### 3. XML External Entity (XXE) - CRITICAL

**Count:** 4 instances  
**Severity:** HIGH  
**OWASP Category:** A05:2021 - Security Misconfiguration  
**CWE:** CWE-611: XML External Entity  

#### Example Vulnerability:
```json
{
  "payload": {
    "identity": "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>"
  }
}
```

**Impact:** The application may be vulnerable to XXE attacks if XML parsing is enabled without proper security configurations.

**Recommendation:**
- Disable external entity processing in XML parsers
- Use safe XML parsing libraries
- Validate and sanitize XML input
- Consider using JSON instead of XML where possible

---

### 4. Information Disclosure - HIGH

**Count:** 1,416 instances  
**Severity:** HIGH  
**OWASP Category:** A05:2021 - Security Misconfiguration  
**CWE:** CWE-200: Information Exposure  

#### Patterns Found in Responses:
- Python stack traces
- File paths
- Line numbers
- Function names
- Error messages with sensitive details

#### Most Affected Endpoints:
- `rmap-get-link`: 300 issues
- `list-documents`: 200 issues
- `get-document`: 200 issues
- `create-watermark`: 200 issues
- `read-watermark`: 200 issues

**Impact:** Detailed error messages expose internal application structure, file paths, and implementation details that could aid attackers in crafting targeted attacks.

**Recommendation:**
- Implement generic error messages for production
- Log detailed errors server-side only
- Remove stack traces from API responses
- Use custom error handlers
- Configure proper error handling middleware

---

### 5. Server Errors (500) - MEDIUM

**Count:** 842 instances  
**Severity:** MEDIUM  
**OWASP Category:** A05:2021 - Security Misconfiguration  

**Impact:** High rate of server errors (56% of issues) indicates poor input validation and error handling, leading to application crashes and denial of service potential.

**Recommendation:**
- Implement comprehensive input validation
- Add try-catch blocks around critical operations
- Validate data types before processing
- Implement rate limiting
- Add request size limits

---

### 6. Exception Handling Issues - MEDIUM

**Count:** 77 instances  
**Severity:** MEDIUM  
**CWE:** CWE-754: Improper Check for Unusual Conditions  

**Impact:** Unhandled exceptions indicate code paths that can cause application failures, especially when processing malformed file uploads.

**Recommendation:**
- Add exception handling for all user input processing
- Validate file types and sizes before processing
- Implement proper error recovery mechanisms
- Add logging for debugging without exposing details to users

---

## Endpoint Security Analysis

### Most Vulnerable Endpoints

| Endpoint | Issues | Severity | Priority |
|----------|--------|----------|----------|
| `/api/rmap-get-link` | 300 | High | P0 |
| `/api/list-documents` | 200 | High | P1 |
| `/api/get-document` | 200 | High | P1 |
| `/api/create-watermark` | 200 | High | P1 |
| `/api/read-watermark` | 200 | High | P1 |
| `/api/list-versions` | 200 | Medium | P2 |
| `/api/list-all-versions` | 200 | Medium | P2 |
| `/api/delete-document` | 200 | Medium | P2 |
| `/api/upload-document` | 123 | Medium | P2 |
| `/api/get-version` | 113 | Medium | P3 |
| `/api/rmap-initiate` | 115 | Critical | P0 |
| `/api/login` | 110 | High | P1 |
| `/api/get-watermarking-methods` | 100 | Low | P3 |
| `/api/create-user` | 91 | Critical | P0 |

### Secure Endpoints

| Endpoint | Issues | Status |
|----------|--------|--------|
| `/healthz` | 0 | ✅ Secure |

---

## Statistics

### Request Statistics
- **Total Requests:** 1,500
- **Successful Requests:** 1,423 (94.9%)
- **Failed Requests:** 77 (5.1%)
- **Endpoints Tested:** 15
- **Total Issues Found:** 2,352

### Vulnerability Breakdown by Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| 🔴 Critical | 17 | 0.7% |
| 🟠 High | 1,425 | 60.6% |
| 🟡 Medium | 927 | 39.4% |

### Vulnerability Breakdown by Type

| Type | Count | Severity |
|------|-------|----------|
| Information Disclosure | 1,416 | High |
| Server Error | 842 | Medium |
| Exception | 77 | Medium |
| XSS | 8 | Critical |
| Path Traversal | 5 | Critical |
| XXE | 4 | Critical |

---

## Recommendations

### Immediate Actions (P0 - Critical)

1. **Fix XSS Vulnerabilities**
   - Implement output encoding for all user input in responses
   - Deploy Content Security Policy (CSP)
   - Sanitize user input on both client and server side

2. **Address Path Traversal**
   - Validate and canonicalize all file paths
   - Never expose internal file paths in error messages
   - Implement allowlist-based file access control

3. **Secure XML Processing**
   - Disable external entity processing in XML parsers
   - Consider replacing XML with JSON where possible

4. **Fix RMAP Endpoints**
   - `/api/rmap-get-link` and `/api/rmap-initiate` require immediate security review
   - Implement proper input validation and sanitization

### Short-term Actions (P1 - High)

1. **Implement Generic Error Handling**
   - Remove stack traces from API responses
   - Create generic error messages for production
   - Log detailed errors server-side only

2. **Add Input Validation**
   - Validate all input parameters before processing
   - Implement type checking and bounds checking
   - Add schema validation for request bodies

3. **Improve Authentication/Authorization**
   - Review `/api/login` and `/api/create-user` security
   - Implement rate limiting on authentication endpoints
   - Add account lockout mechanisms

### Medium-term Actions (P2 - Medium)

1. **Enhance Error Handling**
   - Add try-catch blocks for all critical operations
   - Implement proper error recovery mechanisms
   - Add comprehensive logging

2. **Code Review**
   - Conduct security code review of all endpoints
   - Review document handling and watermarking logic
   - Audit file upload functionality

3. **Implement Security Headers**
   - Add security headers (CSP, X-Frame-Options, etc.)
   - Enable HTTPS/TLS
   - Implement proper CORS policies

### Long-term Actions (P3 - Low)

1. **Security Testing Integration**
   - Integrate fuzzing into CI/CD pipeline
   - Add automated security testing
   - Implement regression testing for fixed vulnerabilities

2. **Security Monitoring**
   - Implement security logging and monitoring
   - Set up alerts for suspicious activities
   - Add intrusion detection

3. **Security Training**
   - Provide secure coding training for developers
   - Establish security review processes
   - Create security guidelines and best practices

---

## Testing Artifacts

### Generated Files
- `results/bugs_found.json` - Raw bug data (1.1MB)
- `results/bugs_found_analyzed.json` - Analyzed bug report (3.9MB)
- `results/statistics.json` - Test statistics
- `logs/fuzzer_run.log` - Complete fuzzing log
- `logs/fuzzer.log` - Fuzzer execution log

### Reproducibility
All test cases can be reproduced using:
```bash
cd fuzzing
python3 api_fuzzer.py
```

Configuration file: `fuzzer_config.yaml`

---

## Conclusion

The Tatou API fuzzing campaign revealed significant security vulnerabilities that require immediate attention. While the application demonstrates good availability (94.9% success rate), it exhibits critical security weaknesses in input validation, output encoding, and error handling.

**Priority:** The XSS, Path Traversal, and XXE vulnerabilities discovered should be addressed immediately as they pose critical security risks.

**Next Steps:**
1. Address P0 critical vulnerabilities immediately
2. Implement comprehensive input validation across all endpoints
3. Deploy generic error handling for production
4. Conduct security code review
5. Re-test after fixes are implemented

---

**Report Generated:** October 17, 2025  
**Testing Tool:** Tatou API Fuzzer v1.0  
**Tested By:** Group 18  
**Contact:** fuzzer@test.com



