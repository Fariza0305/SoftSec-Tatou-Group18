#!/usr/bin/env python3
"""
Smart Fuzzing Campaign - Respects rate limits and tests systematically
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

class SmartFuzzer:
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
            'email': f'smart_fuzzer_{random.randint(1000,9999)}@test.com',
            'password': 'SmartFuzzer123!',
            'login': f'smart_fuzzer_{random.randint(1000,9999)}'
        }
        
    def wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset"""
        print("⏳ Waiting for rate limit to reset (60 seconds)...")
        time.sleep(60)
        
    def setup_auth(self):
        """Setup authentication for testing"""
        try:
            # Wait a bit to avoid rate limiting
            time.sleep(2)
            
            # Create test user
            create_resp = self.session.post(
                f"{self.base_url}/api/create-user",
                json=self.test_user,
                timeout=10
            )
            
            if create_resp.status_code == 429:
                print("🚫 Rate limited on user creation, waiting...")
                self.wait_for_rate_limit_reset()
                create_resp = self.session.post(
                    f"{self.base_url}/api/create-user",
                    json=self.test_user,
                    timeout=10
                )
            
            # Wait a bit before login
            time.sleep(2)
            
            # Login to get token
            login_resp = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': self.test_user['email'], 'password': self.test_user['password']},
                timeout=10
            )
            
            if login_resp.status_code == 429:
                print("🚫 Rate limited on login, waiting...")
                self.wait_for_rate_limit_reset()
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
                print(f"Response: {login_resp.text}")
                return False
                
        except Exception as e:
            print(f"❌ Auth setup failed: {e}")
            return False
    
    def test_xss_protection(self):
        """Test XSS protection in various endpoints"""
        print("🔍 Testing XSS Protection...")
        vulnerabilities = []
        
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '"><script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")',
            '<svg onload=alert("XSS")>',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>'
        ]
        
        # Test create-user endpoint
        for payload in xss_payloads:
            time.sleep(1)  # Rate limiting protection
            
            result = self.session.post(
                f"{self.base_url}/api/create-user",
                json={
                    'login': payload,
                    'email': f'test_{random.randint(1000,9999)}@test.com',
                    'password': 'test123'
                },
                timeout=10
            )
            
            if result.status_code == 429:
                print("  ⏳ Rate limited, waiting...")
                time.sleep(60)
                continue
            
            # Check if payload is reflected in response
            if payload in result.text:
                vulnerabilities.append({
                    'type': 'XSS',
                    'severity': 'CRITICAL',
                    'endpoint': '/api/create-user',
                    'payload': payload,
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 XSS vulnerability found!")
            else:
                print(f"  ✅ XSS payload blocked: {payload[:30]}...")
        
        return vulnerabilities
    
    def test_path_traversal(self):
        """Test path traversal protection"""
        print("🔍 Testing Path Traversal Protection...")
        vulnerabilities = []
        
        path_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '..%252f..%252f..%252fetc%252fpasswd'
        ]
        
        if not self.token:
            print("  ⚠️ No token available for authenticated tests")
            return vulnerabilities
        
        for payload in path_payloads:
            time.sleep(1)  # Rate limiting protection
            
            # Test in upload-document
            files = {'file': (payload, 'test content', 'application/pdf')}
            result = self.session.post(
                f"{self.base_url}/api/upload-document",
                headers={'Authorization': f'Bearer {self.token}'},
                files=files,
                timeout=10
            )
            
            if result.status_code == 429:
                print("  ⏳ Rate limited, waiting...")
                time.sleep(60)
                continue
            
            # Check for path traversal indicators
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
            else:
                print(f"  ✅ Path traversal blocked: {payload[:30]}...")
        
        return vulnerabilities
    
    def test_sql_injection(self):
        """Test SQL injection protection"""
        print("🔍 Testing SQL Injection Protection...")
        vulnerabilities = []
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
            "1' OR 1=1 --"
        ]
        
        for payload in sql_payloads:
            time.sleep(1)  # Rate limiting protection
            
            result = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': payload, 'password': 'test123'},
                timeout=10
            )
            
            if result.status_code == 429:
                print("  ⏳ Rate limited, waiting...")
                time.sleep(60)
                continue
            
            # Check for SQL error indicators
            sql_indicators = ['mysql', 'sqlite', 'postgresql', 'ora-', 'sql syntax', 'database error']
            if any(indicator in result.text.lower() for indicator in sql_indicators):
                vulnerabilities.append({
                    'type': 'SQL_INJECTION',
                    'severity': 'HIGH',
                    'endpoint': '/api/login',
                    'payload': payload,
                    'response': result.text[:200],
                    'status_code': result.status_code
                })
                print(f"  🚨 SQL injection vulnerability found!")
            else:
                print(f"  ✅ SQL injection blocked: {payload[:30]}...")
        
        return vulnerabilities
    
    def test_information_disclosure(self):
        """Test information disclosure protection"""
        print("🔍 Testing Information Disclosure Protection...")
        vulnerabilities = []
        
        # Test various error conditions
        test_cases = [
            {'name': 'Empty request', 'data': None},
            {'name': 'Invalid JSON', 'data': '{"invalid": json}'},
            {'name': 'Null values', 'data': {'email': None, 'password': None}},
            {'name': 'Empty strings', 'data': {'email': '', 'password': ''}},
            {'name': 'Very long strings', 'data': {'email': 'A' * 1000, 'password': 'B' * 1000}},
        ]
        
        for test_case in test_cases:
            time.sleep(1)  # Rate limiting protection
            
            try:
                if test_case['data'] is None:
                    result = self.session.post(f"{self.base_url}/api/login", timeout=10)
                elif isinstance(test_case['data'], str):
                    result = self.session.post(
                        f"{self.base_url}/api/login",
                        data=test_case['data'],
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                else:
                    result = self.session.post(
                        f"{self.base_url}/api/login",
                        json=test_case['data'],
                        timeout=10
                    )
                
                if result.status_code == 429:
                    print("  ⏳ Rate limited, waiting...")
                    time.sleep(60)
                    continue
                
                # Check for information disclosure
                info_indicators = ['Traceback', 'File "', 'line ', 'Exception:', 'Error:', 'stack trace']
                if any(indicator in result.text for indicator in info_indicators):
                    vulnerabilities.append({
                        'type': 'INFORMATION_DISCLOSURE',
                        'severity': 'HIGH',
                        'endpoint': '/api/login',
                        'test_case': test_case['name'],
                        'response': result.text[:200],
                        'status_code': result.status_code
                    })
                    print(f"  🚨 Information disclosure found: {test_case['name']}")
                else:
                    print(f"  ✅ Information disclosure blocked: {test_case['name']}")
                    
            except Exception as e:
                print(f"  ⚠️ Test case failed: {test_case['name']} - {e}")
        
        return vulnerabilities
    
    def test_rate_limiting(self):
        """Test rate limiting implementation"""
        print("🔍 Testing Rate Limiting...")
        vulnerabilities = []
        
        # Test rapid requests to login endpoint
        print("  Testing login rate limiting...")
        rate_limit_hit = False
        
        for i in range(10):
            result = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': f'test{i}@test.com', 'password': 'test123'},
                timeout=5
            )
            
            if result.status_code == 429:
                rate_limit_hit = True
                print(f"  ✅ Rate limiting triggered after {i+1} requests")
                break
            elif i > 5 and result.status_code != 429:
                print(f"  ⚠️ No rate limiting detected after {i+1} requests")
        
        if not rate_limit_hit:
            vulnerabilities.append({
                'type': 'RATE_LIMITING_BYPASS',
                'severity': 'MEDIUM',
                'endpoint': '/api/login',
                'description': 'No rate limiting detected after 10 requests',
                'status_code': 200
            })
            print("  🚨 Rate limiting vulnerability found!")
        
        return vulnerabilities
    
    def run_smart_fuzzing(self):
        """Run smart fuzzing campaign"""
        print("🚀 Starting Smart Tatou API Fuzzing Campaign")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Cannot proceed without authentication")
            return None
        
        all_vulnerabilities = []
        
        # Test specific vulnerabilities
        vulns = self.test_xss_protection()
        all_vulnerabilities.extend(vulns)
        
        vulns = self.test_path_traversal()
        all_vulnerabilities.extend(vulns)
        
        vulns = self.test_sql_injection()
        all_vulnerabilities.extend(vulns)
        
        vulns = self.test_information_disclosure()
        all_vulnerabilities.extend(vulns)
        
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
        
        print(f"\n📊 Smart Fuzzing Complete!")
        print(f"Total vulnerabilities found: {len(all_vulnerabilities)}")
        
        return self.results
    
    def save_results(self, filename=None):
        """Save fuzzing results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"smart_fuzzing_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📁 Results saved to: {filename}")
        return filename

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    fuzzer = SmartFuzzer(base_url)
    results = fuzzer.run_smart_fuzzing()
    
    if results is None:
        print("❌ Fuzzing failed - cannot proceed")
        return
    
    fuzzer.save_results()
    
    # Print summary
    print("\n" + "=" * 60)
    print("SMART FUZZING CAMPAIGN SUMMARY")
    print("=" * 60)
    
    if results and results.get('vulnerabilities'):
        for vuln_type, count in results['statistics']['vulnerability_types'].items():
            print(f"{vuln_type}: {count} instances")
    else:
        print("✅ No vulnerabilities found!")
    
    print(f"\nTotal vulnerabilities: {len(results.get('vulnerabilities', []))}")

if __name__ == "__main__":
    main()

