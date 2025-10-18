#!/usr/bin/env python3
"""
Advanced Fuzzing Campaign - Focus on edge cases and remaining vulnerabilities
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

class AdvancedFuzzer:
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
            'email': 'advanced_fuzzer@test.com',
            'password': 'AdvancedFuzzer123!',
            'login': 'advanced_fuzzer'
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
    
    def test_specific_vulnerabilities(self):
        """Test for specific vulnerability patterns"""
        vulnerabilities = []
        
        # Test 1: XSS in create-user endpoint
        print("🔍 Testing XSS in create-user...")
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '"><script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")'
        ]
        
        for payload in xss_payloads:
            result = self.session.post(
                f"{self.base_url}/api/create-user",
                json={
                    'login': payload,
                    'email': f'test_{random.randint(1000,9999)}@test.com',
                    'password': 'test123'
                },
                timeout=10
            )
            
            if payload in result.text:
                vulnerabilities.append({
                    'type': 'XSS',
                    'severity': 'CRITICAL',
                    'endpoint': '/api/create-user',
                    'payload': payload,
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 XSS vulnerability found with payload: {payload[:30]}...")
        
        # Test 2: Path Traversal in file operations
        print("🔍 Testing Path Traversal...")
        path_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ]
        
        if self.token:
            for payload in path_payloads:
                # Test in upload-document
                files = {'file': (payload, 'test content', 'application/pdf')}
                result = self.session.post(
                    f"{self.base_url}/api/upload-document",
                    headers={'Authorization': f'Bearer {self.token}'},
                    files=files,
                    timeout=10
                )
                
                if '/etc/passwd' in result.text or 'root:' in result.text:
                    vulnerabilities.append({
                        'type': 'PATH_TRAVERSAL',
                        'severity': 'HIGH',
                        'endpoint': '/api/upload-document',
                        'payload': payload,
                        'response': result.text[:200],
                        'status_code': result.status_code
                    })
                    print(f"  🚨 Path traversal vulnerability found!")
        
        # Test 3: SQL Injection
        print("🔍 Testing SQL Injection...")
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--"
        ]
        
        for payload in sql_payloads:
            result = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': payload, 'password': 'test123'},
                timeout=10
            )
            
            if any(sql_indicator in result.text.lower() for sql_indicator in ['mysql', 'sqlite', 'postgresql', 'ora-', 'sql syntax']):
                vulnerabilities.append({
                    'type': 'SQL_INJECTION',
                    'severity': 'HIGH',
                    'endpoint': '/api/login',
                    'payload': payload,
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 SQL injection vulnerability found!")
        
        # Test 4: Information Disclosure
        print("🔍 Testing Information Disclosure...")
        error_payloads = [
            None,  # Empty request
            {'invalid': 'data'},  # Invalid JSON structure
            {'email': None, 'password': None},  # Null values
        ]
        
        for payload in error_payloads:
            result = self.session.post(
                f"{self.base_url}/api/login",
                json=payload,
                timeout=10
            )
            
            if any(info in result.text for info in ['Traceback', 'File "', 'line ', 'Exception:', 'Error:']):
                vulnerabilities.append({
                    'type': 'INFORMATION_DISCLOSURE',
                    'severity': 'HIGH',
                    'endpoint': '/api/login',
                    'payload': str(payload),
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 Information disclosure vulnerability found!")
        
        # Test 5: Authentication Bypass
        print("🔍 Testing Authentication Bypass...")
        bypass_payloads = [
            {'email': '', 'password': ''},
            {'email': 'admin', 'password': 'admin'},
            {'email': 'admin@admin.com', 'password': 'admin'},
            {'email': 'root', 'password': 'root'},
        ]
        
        for payload in bypass_payloads:
            result = self.session.post(
                f"{self.base_url}/api/login",
                json=payload,
                timeout=10
            )
            
            if result.status_code == 200 and 'token' in result.text:
                vulnerabilities.append({
                    'type': 'AUTHENTICATION_BYPASS',
                    'severity': 'CRITICAL',
                    'endpoint': '/api/login',
                    'payload': payload,
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 Authentication bypass vulnerability found!")
        
        # Test 6: File Upload Vulnerabilities
        print("🔍 Testing File Upload Vulnerabilities...")
        if self.token:
            malicious_files = [
                ('shell.php', '<?php system($_GET["cmd"]); ?>', 'application/php'),
                ('shell.jsp', '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>', 'application/jsp'),
                ('shell.asp', '<% eval request("cmd") %>', 'application/asp'),
                ('large_file.pdf', 'A' * 10000000, 'application/pdf'),  # Large file
                ('empty.pdf', '', 'application/pdf'),  # Empty file
            ]
            
            for filename, content, content_type in malicious_files:
                files = {'file': (filename, content, content_type)}
                result = self.session.post(
                    f"{self.base_url}/api/upload-document",
                    headers={'Authorization': f'Bearer {self.token}'},
                    files=files,
                    timeout=30
                )
                
                if result.status_code == 200 and 'uploaded' in result.text.lower():
                    vulnerabilities.append({
                        'type': 'FILE_UPLOAD_VULNERABILITY',
                        'severity': 'HIGH',
                        'endpoint': '/api/upload-document',
                        'payload': f'filename: {filename}',
                        'response': result.text[:200],
                        'status_code': result.status_code
                    })
                    print(f"  🚨 File upload vulnerability found: {filename}")
        
        return vulnerabilities
    
    def test_rate_limiting(self):
        """Test for rate limiting vulnerabilities"""
        print("🔍 Testing Rate Limiting...")
        vulnerabilities = []
        
        # Rapid requests to login endpoint
        for i in range(100):
            result = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': f'test{i}@test.com', 'password': 'test123'},
                timeout=5
            )
            
            if i > 10 and result.status_code != 429:  # Should be rate limited after 10 requests
                vulnerabilities.append({
                    'type': 'RATE_LIMITING_BYPASS',
                    'severity': 'MEDIUM',
                    'endpoint': '/api/login',
                    'description': f'No rate limiting detected after {i+1} requests',
                    'status_code': result.status_code
                })
                break
        
        if vulnerabilities:
            print(f"  🚨 Rate limiting vulnerability found!")
        
        return vulnerabilities
    
    def run_advanced_fuzzing(self):
        """Run advanced fuzzing campaign"""
        print("🚀 Starting Advanced Tatou API Fuzzing Campaign")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Cannot proceed without authentication")
            return
        
        all_vulnerabilities = []
        
        # Test specific vulnerabilities
        vulns = self.test_specific_vulnerabilities()
        all_vulnerabilities.extend(vulns)
        
        # Test rate limiting
        vulns = self.test_rate_limiting()
        all_vulnerabilities.extend(vulns)
        
        self.results['vulnerabilities'] = all_vulnerabilities
        self.results['statistics'] = {
            'total_vulnerabilities': len(all_vulnerabilities),
            'timestamp': datetime.now().isoformat(),
            'vulnerability_types': {}
        }
        
        # Count vulnerability types
        for vuln in all_vulnerabilities:
            vuln_type = vuln['type']
            self.results['statistics']['vulnerability_types'][vuln_type] = \
                self.results['statistics']['vulnerability_types'].get(vuln_type, 0) + 1
        
        print(f"\n📊 Advanced Fuzzing Complete!")
        print(f"Total vulnerabilities found: {len(all_vulnerabilities)}")
        
        return self.results
    
    def save_results(self, filename=None):
        """Save fuzzing results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_fuzzing_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📁 Results saved to: {filename}")
        return filename

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    fuzzer = AdvancedFuzzer(base_url)
    results = fuzzer.run_advanced_fuzzing()
    
    if results is None:
        print("❌ Fuzzing failed - cannot proceed")
        return
    
    fuzzer.save_results()
    
    # Print summary
    print("\n" + "=" * 60)
    print("ADVANCED FUZZING CAMPAIGN SUMMARY")
    print("=" * 60)
    
    if results and results.get('vulnerabilities'):
        for vuln_type, count in results['statistics']['vulnerability_types'].items():
            print(f"{vuln_type}: {count} instances")
    else:
        print("✅ No vulnerabilities found!")
    
    print(f"\nTotal vulnerabilities: {len(results.get('vulnerabilities', []))}")

if __name__ == "__main__":
    main()
