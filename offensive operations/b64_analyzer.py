#!/usr/bin/env python3
import re
import base64
import binascii
from pathlib import Path

# 你可以改成 filtered_flags.txt 或 base64_blobs.txt 等文件
INPUT_FILE = Path("base64_blobs.txt")

HEX40 = re.compile(r"\b[a-f0-9]{40}\b")
HEX64 = re.compile(r"\b[a-f0-9]{64}\b")
B64   = re.compile(r"[A-Za-z0-9+/=]{20,}")

def decode_b64(s: str):
    s = s.strip()
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s)
    except Exception:
        return None

def analyze_blob(label, blob):
    raw = decode_b64(blob)
    if raw is None:
        print(f"[!] Skipping invalid base64 for {label}")
        return
    print("="*80)
    print(f"[{label}]")
    print(f"Length: {len(raw)} bytes")
    hex_view = binascii.hexlify(raw).decode()
    print(f"Hex preview (first 100 chars): {hex_view[:100]}")

    # 检查是否含有40或64位哈希
    found40 = HEX40.findall(hex_view)
    found64 = HEX64.findall(hex_view)
    if found40 or found64:
        print("\n[+] Possible hashes found:")
        for f in set(found40 + found64):
            print(f"   - {f}")
    else:
        print("[!] No obvious SHA1/SHA256 patterns found.")

def main():
    if not INPUT_FILE.exists():
        print(f"❌ Cannot find {INPUT_FILE}, make sure it exists.")
        return

    current_label = None
    with open(INPUT_FILE, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("===") and line.endswith("==="):
                current_label = line.strip("= ").strip()
                continue
            if current_label and B64.search(line):
                blob = B64.search(line).group(0)
                analyze_blob(current_label, blob)

if __name__ == "__main__":
    main()
