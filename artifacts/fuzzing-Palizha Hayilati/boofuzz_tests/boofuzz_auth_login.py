#!/usr/bin/env python3
"""
boofuzz Test Script for Tatou Authentication Login Endpoint
============================================================
This script fuzzes the POST /auth/login endpoint using boofuzz framework.
Tests authentication logic, input validation, and error handling.
"""

from boofuzz import *
import sys


def main():
    """Main fuzzing function for login endpoint"""
    
    # Define target
    session = Session(
        target=Target(
            connection=SocketConnection("localhost", 5000, proto='tcp')
        ),
        crash_threshold_request=12,
        crash_threshold_element=3,
    )
    
    # Initialize request template for POST /auth/login
    s_initialize("auth_login")
    
    # HTTP POST request line
    with s_block("request-line"):
        s_static("POST /auth/login HTTP/1.1\r\n")
    
    # HTTP Headers
    with s_block("headers"):
        s_static("Host: localhost:5000\r\n")
        s_static("Content-Type: application/json\r\n")
        s_static("Accept: application/json\r\n")
        
        # Fuzzable Content-Length (calculated automatically)
        s_static("Content-Length: ")
        s_size("body", output_format="ascii", fuzzable=False)
        s_static("\r\n")
        
        s_static("\r\n")
    
    # HTTP Body - JSON payload
    with s_block("body"):
        s_static('{"username":"')
        s_string("admin", name="username", max_len=100)
        s_static('","password":"')
        s_string("password123", name="password", max_len=100)
        s_static('"}')
    
    # Define test cases with specific payloads
    session.connect(s_get("auth_login"))
    
    # Run the fuzzing session
    print("[*] Starting boofuzz fuzzing session for /auth/login")
    print("[*] Target: localhost:5000")
    print("[*] Request template: auth_login")
    print("[*] Crash threshold: 12 requests, 3 elements")
    print("")
    
    try:
        session.fuzz()
    except KeyboardInterrupt:
        print("\n[!] Fuzzing interrupted by user")
    except Exception as e:
        print(f"[!] Error during fuzzing: {e}")
    
    print("\n[*] Fuzzing session completed")
    print(f"[*] Total test cases executed: {session.num_cases()}")


if __name__ == "__main__":
    main()

