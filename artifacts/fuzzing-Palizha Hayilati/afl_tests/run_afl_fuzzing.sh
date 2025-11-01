#!/bin/bash
# AFL++ Fuzzing Campaign Runner for XML Parser
# =============================================
# This script orchestrates the AFL++ fuzzing campaign with multiple workers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$SCRIPT_DIR/harness"
SEEDS_DIR="$SCRIPT_DIR/seeds"
DICT_FILE="$SCRIPT_DIR/dictionaries/xml.dict"
OUTPUT_DIR="$SCRIPT_DIR/results"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "  AFL++ XML Parser Fuzzing Campaign"
echo "=========================================="
echo ""

# Check if AFL++ is installed
if ! command -v afl-fuzz &> /dev/null; then
    echo -e "${RED}[!] AFL++ not found. Please install AFL++${NC}"
    exit 1
fi

# Build harness
echo "[*] Building fuzzing harness..."
cd "$HARNESS_DIR"
make clean
make all
echo -e "${GREEN}[✓] Harness built successfully${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# AFL++ configuration
export AFL_SKIP_CPUFREQ=1
export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
export AFL_FAST_CAL=1

# Number of parallel workers
WORKERS=8

echo "=========================================="
echo "  Fuzzing Configuration"
echo "=========================================="
echo "  Harness: xml_parser_harness_asan"
echo "  Seeds: $SEEDS_DIR"
echo "  Dictionary: $DICT_FILE"
echo "  Workers: $WORKERS"
echo "  Timeout: 2000ms per test case"
echo "  Output: $OUTPUT_DIR"
echo ""

# Launch main fuzzer instance
echo "[*] Launching main fuzzer instance (master)..."
afl-fuzz -i "$SEEDS_DIR" -o "$OUTPUT_DIR" -M fuzzer01 \
    -x "$DICT_FILE" -t 2000 -m none \
    "$HARNESS_DIR/xml_parser_harness_asan" @@ \
    > /dev/null 2>&1 &

MAIN_PID=$!
sleep 2

# Launch secondary fuzzer instances
echo "[*] Launching secondary fuzzer instances..."
for i in $(seq 2 $WORKERS); do
    FUZZER_NAME=$(printf "fuzzer%02d" $i)
    
    afl-fuzz -i "$SEEDS_DIR" -o "$OUTPUT_DIR" -S "$FUZZER_NAME" \
        -x "$DICT_FILE" -t 2000 -m none \
        "$HARNESS_DIR/xml_parser_harness_asan" @@ \
        > /dev/null 2>&1 &
    
    echo "  - $FUZZER_NAME launched (PID: $!)"
    sleep 1
done

echo ""
echo -e "${GREEN}[✓] All $WORKERS fuzzer instances launched${NC}"
echo ""
echo "=========================================="
echo "  Fuzzing Campaign Started"
echo "=========================================="
echo ""
echo "Fuzzing in progress. Press Ctrl+C to stop."
echo "Monitor progress with: afl-whatsup $OUTPUT_DIR"
echo ""
echo "Expected runtime: 8-12 hours per endpoint"
echo ""

# Wait for main fuzzer
wait $MAIN_PID

echo ""
echo -e "${GREEN}[✓] Fuzzing campaign completed${NC}"
echo "[*] Results saved to: $OUTPUT_DIR"
echo ""
echo "To view crashes:"
echo "  ls $OUTPUT_DIR/*/crashes/"
echo ""
echo "To minimize crashes:"
echo "  afl-tmin -i crash_file -o minimized_file -- $HARNESS_DIR/xml_parser_harness_asan @@"

