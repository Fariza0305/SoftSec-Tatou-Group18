#!/usr/bin/env python3
import re, sys, base64, binascii, hashlib, argparse, zlib
from pathlib import Path

IN_AES   = Path("aes_candidates.txt")     # 可选：来自 aes_probe 的候选
IN_BLOB  = Path("base64_blobs.txt")       # 可选：原始 b64 片段
OUT_REP  = Path("decode_probe_report.txt")
OUT_BEST = Path("best_flags.txt")

HEX40 = re.compile(r"\b[a-f0-9]{40}\b", re.I)
HEX64 = re.compile(r"\b[a-f0-9]{64}\b", re.I)
B64   = re.compile(r"[A-Za-z0-9+/=]{20,}")

def sha1_hex(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def try_hex_bytes(s: str):
    s = s.strip()
    try:
        return binascii.unhexlify(s)
    except Exception:
        return None

def try_b64_bytes(s: str):
    s = s.strip()
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s, validate=False)
    except Exception:
        return None

def gunzip_if_possible(b: bytes):
    # 常见 gzip 头 1f 8b
    if len(b) >= 2 and b[0] == 0x1f and b[1] == 0x8b:
        try:
            return zlib.decompress(b, zlib.MAX_WBITS | 16)
        except Exception:
            return None
    # 常见 zlib 头 78 01/9c/da/..
    if len(b) >= 2 and b[0] == 0x78:
        try:
            return zlib.decompress(b)
        except Exception:
            return None
    return None

def grab40(s: str):
    return {m.lower() for m in HEX40.findall(s)}

def parse_sections(path: Path):
    out = {}
    if not path.exists(): return out
    cur = None
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith("===") and line.endswith("==="):
            cur = line.strip("= ").strip()
            out.setdefault(cur, [])
            continue
        if cur is None: continue
        # value  # from: origin
        val = line.split("  # ")[0].strip()
        if val:
            out[cur].append(val)
    return out

def analyze_value(label: str, val: str):
    lines = []
    found = set()

    def log(s): lines.append(s)

    log(f"[value] {val}")

    # 1) 直接当 HEX 处理
    hb = try_hex_bytes(val)
    if hb:
        log(f"  - as HEX: {len(hb)} bytes")
        h1 = sha1_hex(hb); h256 = sha256_hex(hb)
        log(f"    sha1({len(hb)}B)  = {h1}")
        log(f"    sha256({len(hb)}B)= {h256}")
        found |= grab40(h1)
        found |= grab40(h256)

        # 1.1) HEX->bytes 再尝试当 base64
        b64_from_hex = try_b64_bytes(hb.decode('latin1','ignore'))
        if b64_from_hex:
            txt = b64_from_hex.decode('latin1','ignore')
            log(f"    [hex->b64] len={len(b64_from_hex)} preview='{txt[:120]}'")
            found |= grab40(txt)

        # 1.2) HEX->bytes 再 gunzip/zlib
        decomp = gunzip_if_possible(hb)
        if decomp:
            txt = decomp.decode('latin1','ignore')
            log(f"    [hex->gunzip] len={len(decomp)} preview='{txt[:120]}'")
            found |= grab40(txt)

    # 2) 尝试当 Base64
    bb = try_b64_bytes(val)
    if bb:
        log(f"  - as Base64: {len(bb)} bytes")
        txt = bb.decode('latin1','ignore')
        log(f"    preview: '{txt[:120]}'")
        found |= grab40(txt)
        # b64->sha1/sha256
        h1b = sha1_hex(bb); h256b = sha256_hex(bb)
        log(f"    sha1(b64bytes)  = {h1b}")
        log(f"    sha256(b64bytes)= {h256b}")
        found |= grab40(h1b); found |= grab40(h256b)
        # b64->gunzip
        decomp = gunzip_if_possible(bb)
        if decomp:
            txt2 = decomp.decode('latin1','ignore')
            log(f"    [b64->gunzip] len={len(decomp)} preview='{txt2[:120]}'")
            found |= grab40(txt2)

    # 3) 原样文本也扫 40-hex
    found |= grab40(val)

    return lines, found

def main():
    ap = argparse.ArgumentParser(description="Secondary decoder for 64-hex / b64 candidates")
    ap.add_argument("--only-file", nargs="*", help="只处理指定分组名（例如 Group_13.pdf）")
    ap.add_argument("--add", nargs="*", help="直接附加手动候选值进行尝试（支持HEX或Base64）")
    args = ap.parse_args()

    OUT_REP.write_text("", encoding="utf-8")
    OUT_BEST.write_text("", encoding="utf-8")

    # 读取来源文件
    aes_map  = parse_sections(IN_AES)
    blob_map = parse_sections(IN_BLOB)

    wanted = set(args.only_file) if args.only_file else None

    all_found = set()

    def process_bucket(label, values):
        nonlocal all_found
        with OUT_REP.open("a", encoding="utf-8") as rep:
            rep.write(f"\n=== {label} ===\n")
            bucket_found = set()
            checked = set()
            for v in values:
                if v in checked: continue
                checked.add(v)
                lines, found = analyze_value(label, v)
                for ln in lines: rep.write(ln + "\n")
                bucket_found |= found
            if bucket_found:
                with OUT_BEST.open("a", encoding="utf-8") as best:
                    best.write(f"=== {label} ===\n")
                    for f in sorted(bucket_found):
                        best.write(f"{f}\n")
                    best.write("\n")
            all_found |= bucket_found

    # 跑 aes_candidates.txt
    for label, vals in aes_map.items():
        if wanted and label not in wanted: continue
        process_bucket(label + " [aes_candidates]", vals)

    # 跑 base64_blobs.txt（有时 flag 会直接藏在 b64 文本里）
    for label, vals in blob_map.items():
        if wanted and label not in wanted: continue
        # 仅提取可疑 B64/HEX token
        toks = []
        for raw in vals:
            toks += HEX64.findall(raw)
            toks += B64.findall(raw)
        toks = [t if isinstance(t,str) else t for t in toks]
        process_bucket(label + " [base64_blobs]", toks)

    # 手动附加
    if args.add:
        process_bucket("manual_add", args.add)

    print(f"✅ decode done.\n - report: {OUT_REP}\n - best flags: {OUT_BEST}")
    if all_found:
        print("🎯 possible 40-hex flags found:")
        for f in sorted(all_found):
            print("  ", f)
    else:
        print("ℹ️ no 40-hex found; check report for clues.")
if __name__ == "__main__":
    main()
