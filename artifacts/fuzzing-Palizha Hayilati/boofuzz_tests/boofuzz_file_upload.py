#!/usr/bin/env python3
"""
boofuzz Test Script for Tatou File Upload Endpoint
===================================================
This script fuzzes the POST /files/upload endpoint using boofuzz framework.
Tests file upload validation, path traversal, and MIME type handling.
"""

from boofuzz import *
import sys


def main():
    """Main fuzzing function for file upload endpoint"""
    
    # Define target
    session = Session(
        target=Target(
            connection=SocketConnection("localhost", 5000, proto='tcp')
        ),
        crash_threshold_request=15,
        crash_threshold_element=5,
    )
    
    # Initialize request template for POST /files/upload
    s_initialize("file_upload")
    
    # HTTP POST request line
    with s_block("request-line"):
        s_static("POST /files/upload HTTP/1.1\r\n")
    
    # HTTP Headers
    with s_block("headers"):
        s_static("Host: localhost:5000\r\n")
        s_static("Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW\r\n")
        s_static("Authorization: Bearer test_token_placeholder\r\n")
        
        # Content-Length
        s_static("Content-Length: ")
        s_size("body", output_format="ascii", fuzzable=False)
        s_static("\r\n")
        
        s_static("\r\n")
    
    # HTTP Body - Multipart form data
    with s_block("body"):
        s_static("------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n")
        s_static('Content-Disposition: form-data; name="file"; filename="')
        
        # Fuzzable filename - test path traversal
        s_string("document.pdf", name="filename", max_len=200)
        
        s_static('"\r\n')
        s_static("Content-Type: ")
        
        # Fuzzable MIME type
        s_string("application/pdf", name="mime_type", max_len=100)
        
        s_static("\r\n\r\n")
        
        # File content
        s_string("PDF_CONTENT_PLACEHOLDER", name="file_content", max_len=1000)
        
        s_static("\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n")
    
    # Define test cases
    session.connect(s_get("file_upload"))
    
    # Run the fuzzing session
    print("[*] Starting boofuzz fuzzing session for /files/upload")
    print("[*] Target: localhost:5000")
    print("[*] Request template: file_upload")
    print("[*] Testing: filename validation, MIME type checks, path traversal")
    print("[*] Crash threshold: 15 requests, 5 elements")
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

