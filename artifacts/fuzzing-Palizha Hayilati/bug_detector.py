#!/usr/bin/env python3
"""
Bug Detector and Classifier
============================
This module analyzes fuzzing results to detect, classify, and prioritize bugs.
It provides detailed analysis of security vulnerabilities and robustness issues.

Author: Group 18
Date: 2025-10-17
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BugDetector:
    """Detects and classifies bugs from fuzzing results."""
    
    # Severity levels
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    def __init__(self):
        """Initialize the bug detector."""
        self.bugs = []
        self.classifications = {
            'sql_injection': [],
            'command_injection': [],
            'path_traversal': [],
            'xss': [],
            'xxe': [],
            'information_disclosure': [],
            'authentication_bypass': [],
            'authorization_failure': [],
            'server_error': [],
            'performance_issue': [],
            'timeout': [],
            'exception': [],
            'other': []
        }
        
    def analyze_bugs(self, bugs: List[Dict]) -> Dict:
        """Analyze and classify a list of bugs."""
        logger.info(f"🔍 Analyzing {len(bugs)} potential bugs...")
        
        for bug in bugs:
            classified_bug = self._classify_bug(bug)
            self.bugs.append(classified_bug)
            
            bug_type = classified_bug['type']
            if bug_type in self.classifications:
                self.classifications[bug_type].append(classified_bug)
            else:
                self.classifications['other'].append(classified_bug)
                
        return self._generate_report()
        
    def _classify_bug(self, bug: Dict) -> Dict:
        """Classify a bug and add additional metadata."""
        classified = bug.copy()
        
        # Add CVE-like identifiers
        classified['bug_id'] = self._generate_bug_id(bug)
        
        # Enhance severity assessment
        classified['severity'] = self._assess_severity(bug)
        
        # Add OWASP classification
        classified['owasp_category'] = self._get_owasp_category(bug['type'])
        
        # Add CWE references
        classified['cwe'] = self._get_cwe_reference(bug['type'])
        
        # Add exploitability score
        classified['exploitability'] = self._calculate_exploitability(bug)
        
        # Add remediation advice
        classified['remediation'] = self._get_remediation_advice(bug['type'])
        
        # Add affected endpoints
        classified['affected_endpoint'] = bug.get('endpoint', 'unknown')
        
        return classified
        
    def _generate_bug_id(self, bug: Dict) -> str:
        """Generate a unique bug identifier."""
        timestamp = bug.get('timestamp', datetime.now().isoformat())
        bug_type = bug.get('type', 'unknown')
        endpoint = bug.get('endpoint', 'unknown')
        
        # Create hash from key components
        import hashlib
        content = f"{timestamp}-{bug_type}-{endpoint}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:8]
        
        return f"TATOU-{bug_type.upper()}-{hash_val}"
        
    def _assess_severity(self, bug: Dict) -> str:
        """Assess bug severity based on type and impact."""
        bug_type = bug.get('type', '')
        
        # Critical vulnerabilities
        if bug_type in ['sql_injection', 'command_injection', 'authentication_bypass']:
            return self.CRITICAL
            
        # High severity
        if bug_type in ['path_traversal', 'xxe', 'authorization_failure', 'information_disclosure']:
            return self.HIGH
            
        # Medium severity
        if bug_type in ['xss', 'server_error', 'timeout']:
            return self.MEDIUM
            
        # Low severity
        if bug_type in ['performance_issue']:
            return self.LOW
            
        # Default to medium for unknown types
        return self.MEDIUM
        
    def _get_owasp_category(self, bug_type: str) -> str:
        """Get OWASP Top 10 category for the bug type."""
        owasp_mapping = {
            'sql_injection': 'A03:2021 - Injection',
            'command_injection': 'A03:2021 - Injection',
            'authentication_bypass': 'A07:2021 - Identification and Authentication Failures',
            'authorization_failure': 'A01:2021 - Broken Access Control',
            'path_traversal': 'A01:2021 - Broken Access Control',
            'xss': 'A03:2021 - Injection',
            'xxe': 'A05:2021 - Security Misconfiguration',
            'information_disclosure': 'A05:2021 - Security Misconfiguration',
            'server_error': 'A05:2021 - Security Misconfiguration',
            'performance_issue': 'A04:2021 - Insecure Design',
            'timeout': 'A04:2021 - Insecure Design'
        }
        return owasp_mapping.get(bug_type, 'N/A')
        
    def _get_cwe_reference(self, bug_type: str) -> str:
        """Get CWE (Common Weakness Enumeration) reference."""
        cwe_mapping = {
            'sql_injection': 'CWE-89: SQL Injection',
            'command_injection': 'CWE-77: Command Injection',
            'path_traversal': 'CWE-22: Path Traversal',
            'xss': 'CWE-79: Cross-site Scripting',
            'xxe': 'CWE-611: XML External Entity',
            'authentication_bypass': 'CWE-287: Improper Authentication',
            'authorization_failure': 'CWE-862: Missing Authorization',
            'information_disclosure': 'CWE-200: Information Exposure',
            'server_error': 'CWE-754: Improper Check for Unusual Conditions',
            'performance_issue': 'CWE-400: Uncontrolled Resource Consumption',
            'timeout': 'CWE-400: Uncontrolled Resource Consumption'
        }
        return cwe_mapping.get(bug_type, 'N/A')
        
    def _calculate_exploitability(self, bug: Dict) -> str:
        """Calculate exploitability score (Low/Medium/High)."""
        bug_type = bug.get('type', '')
        
        # Easily exploitable
        if bug_type in ['sql_injection', 'command_injection', 'path_traversal']:
            return 'High'
            
        # Moderately exploitable
        if bug_type in ['xss', 'xxe', 'authentication_bypass', 'authorization_failure']:
            return 'Medium'
            
        # Low exploitability
        return 'Low'
        
    def _get_remediation_advice(self, bug_type: str) -> str:
        """Get remediation advice for a bug type."""
        remediation_map = {
            'sql_injection': 'Use parameterized queries and prepared statements. Never concatenate user input into SQL queries.',
            'command_injection': 'Avoid executing system commands with user input. Use safe APIs instead. If necessary, use strict input validation and whitelist allowed commands.',
            'path_traversal': 'Validate and sanitize file paths. Use path canonicalization and check that resolved paths stay within allowed directories.',
            'xss': 'Encode output and use context-appropriate escaping. Implement Content Security Policy (CSP).',
            'xxe': 'Disable external entity processing in XML parsers. Use safe XML parsing libraries.',
            'authentication_bypass': 'Implement proper authentication checks. Use secure session management and token validation.',
            'authorization_failure': 'Implement proper access control checks. Verify user permissions before allowing resource access.',
            'information_disclosure': 'Remove sensitive information from error messages. Implement proper error handling.',
            'server_error': 'Add proper error handling and input validation. Log errors securely without exposing internal details.',
            'performance_issue': 'Implement rate limiting, request throttling, and resource limits.',
            'timeout': 'Add request timeouts and implement proper resource cleanup.',
            'exception': 'Add try-catch blocks and proper error handling. Validate inputs before processing.'
        }
        return remediation_map.get(bug_type, 'Review and fix the underlying issue.')
        
    def _generate_report(self) -> Dict:
        """Generate a comprehensive bug report."""
        total_bugs = len(self.bugs)
        
        # Count by severity
        severity_counts = {
            self.CRITICAL: 0,
            self.HIGH: 0,
            self.MEDIUM: 0,
            self.LOW: 0,
            self.INFO: 0
        }
        
        for bug in self.bugs:
            severity = bug.get('severity', self.MEDIUM)
            if severity in severity_counts:
                severity_counts[severity] += 1
                
        # Count by type
        type_counts = {}
        for bug_type, bugs_list in self.classifications.items():
            if bugs_list:
                type_counts[bug_type] = len(bugs_list)
                
        # Most affected endpoints
        endpoint_counts = {}
        for bug in self.bugs:
            endpoint = bug.get('affected_endpoint', 'unknown')
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
        report = {
            'summary': {
                'total_bugs': total_bugs,
                'by_severity': severity_counts,
                'by_type': type_counts,
                'critical_count': severity_counts[self.CRITICAL],
                'high_count': severity_counts[self.HIGH],
                'medium_count': severity_counts[self.MEDIUM],
                'low_count': severity_counts[self.LOW]
            },
            'most_affected_endpoints': dict(sorted(
                endpoint_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            'bugs': self.bugs,
            'classifications': {
                k: v for k, v in self.classifications.items() if v
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    def save_report(self, report: Dict, output_file: str):
        """Save the bug report to a JSON file."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📄 Bug report saved to: {output_file}")
        
    def print_summary(self, report: Dict):
        """Print a summary of the bug analysis."""
        summary = report['summary']
        
        print("\n" + "=" * 70)
        print("🐛 BUG ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"\nTotal Bugs Found: {summary['total_bugs']}")
        
        print("\n📊 By Severity:")
        for severity, count in summary['by_severity'].items():
            if count > 0:
                emoji = {
                    self.CRITICAL: '🔴',
                    self.HIGH: '🟠',
                    self.MEDIUM: '🟡',
                    self.LOW: '🟢',
                    self.INFO: '🔵'
                }.get(severity, '⚪')
                print(f"  {emoji} {severity.upper():<10}: {count}")
                
        print("\n🏷️  By Type:")
        for bug_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {bug_type:<25}: {count}")
            
        print("\n🎯 Most Affected Endpoints:")
        for endpoint, count in list(report['most_affected_endpoints'].items())[:5]:
            print(f"  - {endpoint:<30}: {count} issues")
            
        print("\n" + "=" * 70)


def main():
    """Main entry point for bug detection."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bug_detector.py <bugs_file.json>")
        sys.exit(1)
        
    bugs_file = sys.argv[1]
    
    try:
        with open(bugs_file, 'r') as f:
            bugs = json.load(f)
    except Exception as e:
        print(f"Error loading bugs file: {e}")
        sys.exit(1)
        
    detector = BugDetector()
    report = detector.analyze_bugs(bugs)
    
    # Save report
    output_file = bugs_file.replace('.json', '_analyzed.json')
    detector.save_report(report, output_file)
    
    # Print summary
    detector.print_summary(report)


if __name__ == "__main__":
    main()



