#!/bin/bash
# boofuzz Test Runner Script
# ==========================
# Executes boofuzz fuzzing tests against Tatou API endpoints

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/boofuzz_results"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "  Tatou API - boofuzz Test Runner"
echo "======================================"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if target is accessible
echo "[*] Checking target availability..."
if ! curl -s -o /dev/null http://localhost:5000/healthz; then
    echo -e "${RED}[!] Target API is not accessible at localhost:5000${NC}"
    echo "[!] Please start the Tatou API server first"
    exit 1
fi
echo -e "${GREEN}[✓] Target is accessible${NC}"
echo ""

# Run authentication login fuzzing
echo "======================================"
echo "[*] Test 1: Authentication Login Fuzzing"
echo "======================================"
echo "[*] Endpoint: POST /auth/login"
echo "[*] Test cases: SQL injection, XSS, overflow, null bytes"
echo ""

python3 "$SCRIPT_DIR/boofuzz_auth_login.py" 2>&1 | tee "$RESULTS_DIR/auth_login_fuzzing.log"

echo ""
echo -e "${GREEN}[✓] Authentication login fuzzing completed${NC}"
echo "[*] Results saved to: $RESULTS_DIR/auth_login_fuzzing.log"
echo ""
sleep 2

# Run file upload fuzzing
echo "======================================"
echo "[*] Test 2: File Upload Fuzzing"
echo "======================================"
echo "[*] Endpoint: POST /files/upload"
echo "[*] Test cases: Path traversal, MIME type mismatch, malformed files"
echo ""

python3 "$SCRIPT_DIR/boofuzz_file_upload.py" 2>&1 | tee "$RESULTS_DIR/file_upload_fuzzing.log"

echo ""
echo -e "${GREEN}[✓] File upload fuzzing completed${NC}"
echo "[*] Results saved to: $RESULTS_DIR/file_upload_fuzzing.log"
echo ""

# Summary
echo "======================================"
echo "  Fuzzing Summary"
echo "======================================"
echo "[*] All boofuzz tests completed"
echo "[*] Results directory: $RESULTS_DIR"
echo ""
echo "Files generated:"
ls -lh "$RESULTS_DIR/"
echo ""
echo -e "${GREEN}[✓] boofuzz fuzzing campaign completed successfully${NC}"

