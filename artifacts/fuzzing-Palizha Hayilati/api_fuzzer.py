#!/usr/bin/env python3
"""
Tatou API Fuzzer - Main Fuzzing Engine
=======================================
This module implements a comprehensive fuzzing framework for the Tatou API.
It performs intelligent mutation-based fuzzing to discover security vulnerabilities
and robustness issues.

Author: Group 18
Date: 2025-10-17
"""

import os
import sys
import yaml
import json
import time
import random
import string
import hashlib
import logging
import requests
import traceback
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configure logging
import os
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'fuzzer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class APIFuzzer:
    """Main fuzzing engine for the Tatou API."""
    
    def __init__(self, config_path: str = "fuzzer_config.yaml"):
        """Initialize the fuzzer with configuration."""
        self.config = self._load_config(config_path)
        self.base_url = self.config['api']['base_url']
        self.timeout = self.config['api']['timeout']
        self.session = requests.Session()
        self.token = None
        self.test_document_id = None
        
        # Results storage
        self.bugs_found = []
        self.test_cases = []
        self.statistics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'bugs_found': 0,
            'endpoints_tested': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Create output directories
        self._create_output_dirs()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load fuzzer configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
            
    def _create_output_dirs(self):
        """Create directories for output files."""
        dirs = [
            'results',
            'logs',
            'regression_tests',
            'payloads'
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
            
    def authenticate(self) -> bool:
        """Authenticate to get a token."""
        logger.info("🔐 Authenticating...")
        
        auth_config = self.config['auth']
        login_data = {
            "email": auth_config['email'],
            "password": auth_config['password']
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/login",
                json=login_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                logger.info(f"✅ Authentication successful")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
            
    def create_test_pdf(self) -> bytes:
        """Create a test PDF file for upload testing."""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Fuzzing Test Document")
        c.drawString(100, 700, f"Generated at: {datetime.now()}")
        c.drawString(100, 650, "This document is used for API fuzzing tests.")
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    def setup_test_data(self) -> bool:
        """Setup test data (upload a document)."""
        logger.info("📄 Setting up test data...")
        
        try:
            pdf_bytes = self.create_test_pdf()
            files = {'file': ('test_fuzzing.pdf', pdf_bytes, 'application/pdf')}
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            
            response = self.session.post(
                f"{self.base_url}/api/upload-document",
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.test_document_id = result.get('id')
                logger.info(f"✅ Test document uploaded (ID: {self.test_document_id})")
                return True
            else:
                logger.warning(f"⚠️ Failed to upload test document: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting up test data: {e}")
            return False
            
    def generate_fuzz_values(self, param_type: str) -> List[Any]:
        """Generate fuzz values based on parameter type."""
        mutations = self.config['fuzzing']['mutations']
        
        if param_type == 'string':
            return mutations.get('string', [])
        elif param_type == 'integer':
            return mutations.get('integer', [])
        elif param_type == 'array':
            return mutations.get('array', [])
        elif param_type == 'object':
            return mutations.get('object', [])
        elif param_type == 'file':
            return self._generate_file_fuzzes()
        else:
            return mutations.get('string', [])
            
    def _generate_file_fuzzes(self) -> List[Tuple[str, bytes, str]]:
        """Generate fuzzing payloads for file uploads."""
        fuzzes = []
        
        # Empty file
        fuzzes.append(('empty.pdf', b'', 'application/pdf'))
        
        # Large file
        fuzzes.append(('large.pdf', b'A' * 10000000, 'application/pdf'))
        
        # Malformed PDF
        fuzzes.append(('malformed.pdf', b'%PDF-1.4\n%%EOF', 'application/pdf'))
        
        # Non-PDF file
        fuzzes.append(('text.txt', b'This is not a PDF', 'text/plain'))
        
        # Binary garbage
        fuzzes.append(('garbage.pdf', os.urandom(1000), 'application/pdf'))
        
        # Path traversal in filename
        fuzzes.append(('../../../etc/passwd.pdf', self.create_test_pdf(), 'application/pdf'))
        
        return fuzzes
        
    def fuzz_endpoint(self, endpoint: Dict) -> List[Dict]:
        """Fuzz a single endpoint with various payloads."""
        logger.info(f"🎯 Fuzzing endpoint: {endpoint['name']}")
        
        bugs_found = []
        iterations = self.config['fuzzing']['iterations']
        
        for i in range(iterations):
            # Generate fuzzy payload
            fuzz_payload = self._generate_fuzz_payload(endpoint)
            
            # Execute request
            result = self._execute_fuzz_request(endpoint, fuzz_payload)
            
            # Analyze response for bugs
            if result:
                bugs = self._analyze_response(endpoint, fuzz_payload, result)
                bugs_found.extend(bugs)
                
            # Rate limiting
            time.sleep(0.01)
            
        return bugs_found
        
    def _generate_fuzz_payload(self, endpoint: Dict) -> Dict:
        """Generate a fuzzy payload for an endpoint."""
        payload = {}
        parameters = endpoint.get('parameters', {})
        
        for param_name, param_type in parameters.items():
            # Randomly choose between valid and fuzz values
            if random.random() < 0.7:  # 70% fuzz, 30% valid
                fuzz_values = self.generate_fuzz_values(param_type)
                if fuzz_values:
                    payload[param_name] = random.choice(fuzz_values)
            else:
                payload[param_name] = self._generate_valid_value(param_type)
                
        return payload
        
    def _generate_valid_value(self, param_type: str) -> Any:
        """Generate a valid value for a parameter type."""
        if param_type == 'string':
            return ''.join(random.choices(string.ascii_letters, k=10))
        elif param_type == 'integer':
            return random.randint(1, 100)
        elif param_type == 'array':
            return ['item1', 'item2']
        elif param_type == 'object':
            return {'key': 'value'}
        elif param_type == 'file':
            return self.create_test_pdf()
        else:
            return 'test_value'
            
    def _execute_fuzz_request(self, endpoint: Dict, payload: Dict) -> Optional[Dict]:
        """Execute a fuzz request and return the response details."""
        self.statistics['total_requests'] += 1
        
        try:
            # Build URL
            url = f"{self.base_url}{endpoint['path']}"
            
            # Replace path parameters
            if '{document_id}' in url:
                url = url.replace('{document_id}', str(self.test_document_id or 1))
            if '{link}' in url:
                url = url.replace('{link}', payload.get('link', 'test_link'))
                
            # Setup headers
            headers = {}
            if endpoint.get('auth_required') and self.token:
                headers['Authorization'] = f'Bearer {self.token}'
                
            # Execute request
            start_time = time.time()
            
            method = endpoint['method'].upper()
            if method == 'GET':
                response = self.session.get(url, params=payload, headers=headers, timeout=self.timeout)
            elif method == 'POST':
                if endpoint.get('content_type') == 'multipart/form-data':
                    # File upload
                    files = {}
                    data = {}
                    for k, v in payload.items():
                        if k == 'file':
                            # Support either bytes or (filename, bytes, mimetype)
                            if isinstance(v, tuple) and len(v) == 3:
                                files['file'] = v
                            elif isinstance(v, (bytes, bytearray)):
                                files['file'] = ('test.pdf', v, 'application/pdf')
                            else:
                                # Fallback to generated PDF if format unexpected
                                files['file'] = ('test.pdf', self.create_test_pdf(), 'application/pdf')
                        else:
                            data[k] = v
                    response = self.session.post(url, files=files, data=data, headers=headers, timeout=self.timeout)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
            elif method == 'DELETE':
                response = self.session.delete(url, json=payload, headers=headers, timeout=self.timeout)
            else:
                logger.warning(f"Unsupported method: {method}")
                return None
                
            end_time = time.time()
            response_time = end_time - start_time
            
            self.statistics['successful_requests'] += 1
            
            return {
                'url': url,
                'method': method,
                'payload': payload,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_text': response.text[:1000],  # Limit response size
                'response_headers': dict(response.headers),
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.Timeout:
            self.statistics['failed_requests'] += 1
            logger.warning(f"⏱️ Timeout for {endpoint['name']}")
            return {
                'url': url,
                'method': endpoint['method'],
                'payload': payload,
                'error': 'timeout',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.statistics['failed_requests'] += 1
            logger.error(f"❌ Error executing request: {e}")
            return {
                'url': url,
                'method': endpoint['method'],
                'payload': payload,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
            
    def _analyze_response(self, endpoint: Dict, payload: Dict, result: Dict) -> List[Dict]:
        """Analyze response for bugs and vulnerabilities."""
        bugs = []
        bug_detection = self.config['bug_detection']
        
        # Check for error status codes
        status_code = result.get('status_code')
        if status_code in bug_detection['error_codes']:
            bugs.append({
                'type': 'server_error',
                'severity': 'high',
                'endpoint': endpoint['name'],
                'status_code': status_code,
                'payload': payload,
                'response': result.get('response_text', ''),
                'timestamp': result['timestamp']
            })
            
        # Check for slow responses
        response_time = result.get('response_time', 0)
        if response_time > bug_detection['slow_response']:
            bugs.append({
                'type': 'performance_issue',
                'severity': 'medium',
                'endpoint': endpoint['name'],
                'response_time': response_time,
                'payload': payload,
                'timestamp': result['timestamp']
            })
            
        # Check for vulnerability patterns
        response_text = result.get('response_text', '')
        for vuln_type, patterns in bug_detection['vulnerability_patterns'].items():
            for pattern in patterns:
                if pattern.lower() in response_text.lower():
                    bugs.append({
                        'type': vuln_type,
                        'severity': 'critical',
                        'endpoint': endpoint['name'],
                        'pattern': pattern,
                        'payload': payload,
                        'response': response_text,
                        'timestamp': result['timestamp']
                    })
                    
        # Check for timeout
        if result.get('error') == 'timeout':
            bugs.append({
                'type': 'timeout',
                'severity': 'high',
                'endpoint': endpoint['name'],
                'payload': payload,
                'timestamp': result['timestamp']
            })
            
        # Check for unexpected exceptions
        if 'traceback' in result:
            bugs.append({
                'type': 'exception',
                'severity': 'high',
                'endpoint': endpoint['name'],
                'payload': payload,
                'traceback': result['traceback'],
                'timestamp': result['timestamp']
            })
            
        return bugs
        
    def run(self):
        """Run the complete fuzzing campaign."""
        logger.info("=" * 60)
        logger.info("🚀 Starting Tatou API Fuzzing Campaign")
        logger.info("=" * 60)
        
        self.statistics['start_time'] = datetime.now().isoformat()
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Failed to authenticate. Exiting.")
            return
            
        # Setup test data
        self.setup_test_data()
        
        # Fuzz each endpoint
        endpoints = self.config['endpoints']
        for endpoint in endpoints:
            self.statistics['endpoints_tested'] += 1
            bugs = self.fuzz_endpoint(endpoint)
            
            if bugs:
                self.bugs_found.extend(bugs)
                self.statistics['bugs_found'] += len(bugs)
                logger.info(f"  🐛 Found {len(bugs)} issues")
            else:
                logger.info(f"  ✅ No issues found")
                
        self.statistics['end_time'] = datetime.now().isoformat()
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
        
    def _sanitize_for_json(self, obj):
        """Recursively sanitize object for JSON serialization."""
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')[:1000]
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)[:1000]
    
    def _save_results(self):
        """Save fuzzing results to files."""
        logger.info("💾 Saving results...")
        
        # Sanitize bugs for JSON
        sanitized_bugs = self._sanitize_for_json(self.bugs_found)
        
        # Save bugs
        bugs_file = 'results/bugs_found.json'
        with open(bugs_file, 'w') as f:
            json.dump(sanitized_bugs, f, indent=2)
        logger.info(f"  📄 Bugs saved to: {bugs_file}")
        
        # Save statistics
        stats_file = 'results/statistics.json'
        with open(stats_file, 'w') as f:
            json.dump(self.statistics, f, indent=2)
        logger.info(f"  📊 Statistics saved to: {stats_file}")
        
    def _print_summary(self):
        """Print fuzzing campaign summary."""
        logger.info("=" * 60)
        logger.info("📊 Fuzzing Campaign Summary")
        logger.info("=" * 60)
        logger.info(f"Total Requests:      {self.statistics['total_requests']}")
        logger.info(f"Successful:          {self.statistics['successful_requests']}")
        logger.info(f"Failed:              {self.statistics['failed_requests']}")
        logger.info(f"Endpoints Tested:    {self.statistics['endpoints_tested']}")
        logger.info(f"Bugs Found:          {self.statistics['bugs_found']}")
        
        if self.bugs_found:
            logger.info("\n🐛 Bug Summary by Type:")
            bug_types = {}
            for bug in self.bugs_found:
                bug_type = bug['type']
                bug_types[bug_type] = bug_types.get(bug_type, 0) + 1
            for bug_type, count in sorted(bug_types.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  - {bug_type}: {count}")
                
        logger.info("=" * 60)


def main():
    """Main entry point."""
    fuzzer = APIFuzzer()
    fuzzer.run()


if __name__ == "__main__":
    main()

