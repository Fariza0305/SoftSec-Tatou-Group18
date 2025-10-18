#!/usr/bin/env python3
import re, sys, base64, binascii, hashlib, argparse
from pathlib import Path
from typing import List, Tuple, Dict, Iterable
from Crypto.Cipher import AES

# 输入文件（来自你之前脚本的产物）
B64_FILE = Path("base64_blobs.txt")
HINTS_FILE = Path("key_hints.txt")

# 输出
REPORT = Path("aes_probe_report.txt")
CANDS  = Path("aes_candidates.txt")

HEX40 = re.compile(r"\b[a-f0-9]{40}\b", re.I)
HEX64 = re.compile(r"\b[a-f0-9]{64}\b", re.I)
B64   = re.compile(r"[A-Za-z0-9+/=]{20,}")
UUID_DASH  = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)
UUID_PLAIN = re.compile(r"\b[0-9a-f]{32}\b", re.I)

def to_bytes_hex(s: str) -> bytes | None:
    s = s.strip()
    try:
        return binascii.unhexlify(s)
    except Exception:
        return None

def try_b64(s: str) -> bytes | None:
    s = s.strip()
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s, validate=False)
    except Exception:
        return None

def sha1_bytes(x: bytes) -> bytes:
    return hashlib.sha1(x).digest()

def sha256_bytes(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()

def parse_sections(path: Path) -> Dict[str, List[Tuple[str,str]]]:
    """
    解析类似：
      === Group_13.pdf ===
      base64blob...   # from: origin
    返回 { "Group_13.pdf": [(value, origin), ...], ... }
    """
    out: Dict[str, List[Tuple[str,str]]] = {}
    cur = None
    if not path.exists(): return out
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith("===") and line.endswith("==="):
            cur = line.strip("= ").strip()
            out.setdefault(cur, [])
            continue
        if cur is None: continue
        val, origin = line, ""
        if "  # " in line:
            val, origin = line.split("  # ", 1)
        out[cur].append((val.strip(), origin.strip()))
    return out

def collect_cipher_blobs(secs: Dict[str, List[Tuple[str,str]]], only: set[str] | None) -> Dict[str, List[Tuple[bytes,str,str]]]:
    """
    从 base64_blobs.txt 里收集可解码的密文块（bytes），过滤只保留长度像分组的（16/24/32/48/64/… 或其它）
    返回 { label: [(cipher_bytes, kind, origin), ...] }
    """
    out: Dict[str, List[Tuple[bytes,str,str]]] = {}
    for label, pairs in secs.items():
        if only and label not in only: continue
        for raw, origin in pairs:
            m = B64.search(raw)
            if not m: continue
            dec = try_b64(m.group(0))
            if not dec: continue
            L = len(dec)
            kind = f"b64_decoded_len={L}"
            # 优先保留 >=16 的块
            out.setdefault(label, []).append((dec, kind, origin))
    return out

def collect_key_materials(hints: Dict[str, List[Tuple[str,str]]], only: set[str] | None) -> Dict[str, Dict[str, set[str]]]:
    """
    从 key_hints.txt 收集可能的 key/iv/salt 线索：
      - uuids（带/不带横杠）
      - hex keys (32/40/48/64 hex)
      - 关键字命中行附近的片段（作为口令材料）
      - base64 大段（用于派生）
    返回 { label: { 'uuid': set(), 'hex': set(), 'b64': set(), 'words': set() } }
    """
    out: Dict[str, Dict[str, set[str]]] = {}
    for label, pairs in hints.items():
        if only and label not in only: continue
        bag = out.setdefault(label, {'uuid': set(), 'hex': set(), 'b64': set(), 'words': set()})
        for line, origin in pairs:
            # UUID
            for u in UUID_DASH.findall(line): bag['uuid'].add(u)
            for u in UUID_PLAIN.findall(line): bag['uuid'].add(u)
            # HEX candidates
            for h in HEX64.findall(line): bag['hex'].add(h)
            for h in re.findall(r"\b[a-f0-9]{48}\b", line, flags=re.I): bag['hex'].add(h)
            for h in re.findall(r"\b[a-f0-9]{40}\b", line, flags=re.I): bag['hex'].add(h)
            for h in re.findall(r"\b[a-f0-9]{32}\b", line, flags=re.I): bag['hex'].add(h)
            # B64
            for b in B64.findall(line): bag['b64'].add(b)
            # 词材料（可能用于派生）
            # 只收较干净的 token
            tokens = re.findall(r"[A-Za-z0-9._\-]{4,}", line)
            for t in tokens:
                if re.fullmatch(r"[A-Fa-f0-9]{8,}", t):  # 纯hex在hex里已收集
                    continue
                if len(t) > 40: 
                    continue
                bag['words'].add(t)
    return out

def derive_keys_from_material(material: Dict[str, set[str]]) -> Tuple[List[bytes], List[bytes]]:
    """
    根据 uuid/hex/b64/words 生成候选 key 与 iv：
      - 直接使用 16/24/32 字节 hex -> key
      - uuid 去掉 '-' 变 16B；也做 sha1/sha256 截断 16/24/32
      - words / b64 解码后做 sha1/sha256 截断
      - 常用 IV：全零；sha1/sha256 截断 16；来自 hex16 候选
    """
    key_cands: set[bytes] = set()
    iv_cands: set[bytes]  = set()

    # helpers
    def add_key_variants(x: bytes):
        for L in (16, 24, 32):
            if len(x) >= L:
                key_cands.add(x[:L])

    def add_iv_variants(x: bytes):
        if len(x) >= 16:
            iv_cands.add(x[:16])

    # HEX
    for h in material.get('hex', set()):
        hb = to_bytes_hex(h)
        if hb:
            if len(hb) in (16,24,32): key_cands.add(hb)
            add_key_variants(sha1_bytes(hb))
            add_key_variants(sha256_bytes(hb))
            add_iv_variants(hb)
            add_iv_variants(sha1_bytes(hb))
            add_iv_variants(sha256_bytes(hb))

    # UUIDs
    for u in material.get('uuid', set()):
        clean = u.replace("-", "")
        ub = to_bytes_hex(clean) or clean.encode()
        add_key_variants(ub)
        add_key_variants(sha1_bytes(ub))
        add_key_variants(sha256_bytes(ub))
        add_iv_variants(ub)
        add_iv_variants(sha1_bytes(ub))
        add_iv_variants(sha256_bytes(ub))

    # words
    for w in material.get('words', set()):
        wb = w.encode()
        add_key_variants(sha1_bytes(wb))
        add_key_variants(sha256_bytes(wb))
        add_iv_variants(sha1_bytes(wb))
        add_iv_variants(sha256_bytes(wb))

    # b64
    for b in material.get('b64', set()):
        dec = try_b64(b)
        if not dec: continue
        add_key_variants(dec)
        add_key_variants(sha1_bytes(dec))
        add_key_variants(sha256_bytes(dec))
        add_iv_variants(dec)
        add_iv_variants(sha1_bytes(dec))
        add_iv_variants(sha256_bytes(dec))

    # 常用 IV：16字节全零
    iv_cands.add(b"\x00"*16)

    # 限制规模，防止组合爆炸（足够实战了）
    key_list = list(sorted(key_cands))[:400]
    iv_list  = list(sorted(iv_cands))[:200]
    return key_list, iv_list

def aes_try_all(cipher: bytes, keys: List[bytes], ivs: List[bytes]) -> List[Tuple[str, bytes]]:
    """
    尝试 AES-ECB 和 AES-CBC 的解密组合
    返回 [("AES-ECB key=...", plaintext), ("AES-CBC key=.. iv=..", plaintext), ...]
    """
    outs: List[Tuple[str, bytes]] = []

    # 只尝试分组边界对齐的（多数密文如此）
    # 也允许非对齐：部分组也可能带额外标识，解出来的尾部忽略
    for k in keys:
        # ECB
        try:
            cipher_ecb = AES.new(k, AES.MODE_ECB)
            if len(cipher) % 16 == 0:
                pt = cipher_ecb.decrypt(cipher)
                outs.append((f"AES-ECB key={binascii.hexlify(k).decode()}", pt))
        except Exception:
            pass

        # CBC
        for iv in ivs:
            try:
                if len(cipher) >= 16:
                    trim = cipher[:len(cipher) - (len(cipher) % 16)]
                    if trim:
                        cipher_cbc = AES.new(k, AES.MODE_CBC, iv=iv)
                        pt = cipher_cbc.decrypt(trim)
                        outs.append((f"AES-CBC key={binascii.hexlify(k).decode()} iv={binascii.hexlify(iv).decode()}", pt))
            except Exception:
                continue
    return outs

def score_plaintext(pt: bytes) -> int:
    """
    粗评分：包含 40-hex / 出现可打印字符占比 / JSON/URL 片段等 → 分高
    """
    s = pt.decode("latin1","ignore")
    score = 0
    if HEX40.search(s): score += 100
    if re.search(r"https?://", s): score += 30
    printable = sum(32 <= c < 127 for c in pt)
    ratio = printable / max(1,len(pt))
    score += int(50*ratio)
    # 发现明显的英文单词/JSON括号
    if re.search(r"[{}:\[\]\"]", s): score += 10
    if re.search(r"[A-Za-z]{4,}", s): score += 10
    return score

def find_flags(s: str) -> List[str]:
    return HEX40.findall(s)

def main():
    ap = argparse.ArgumentParser(description="AES probe for PDF watermark blobs")
    ap.add_argument("--only", nargs="*", help="只跑指定文件名（如: Group_13.pdf）")
    args = ap.parse_args()
    only = set(args.only) if args.only else None

    if not B64_FILE.exists() or not HINTS_FILE.exists():
        print("❌ 缺少 base64_blobs.txt 或 key_hints.txt，请先运行前面的扫描脚本。")
        sys.exit(1)

    secs_b64  = parse_sections(B64_FILE)
    secs_hint = parse_sections(HINTS_FILE)

    blobs_map = collect_cipher_blobs(secs_b64, only)
    mats_map  = collect_key_materials(secs_hint, only)

    REPORT.write_text("", encoding="utf-8")
    CANDS.write_text("", encoding="utf-8")

    for label, blobs in blobs_map.items():
        with REPORT.open("a", encoding="utf-8") as rep, CANDS.open("a", encoding="utf-8") as cand:
            rep.write(f"=== {label} ===\n")
            cand.write(f"=== {label} ===\n")

            mats = mats_map.get(label, {'uuid':set(),'hex':set(),'b64':set(),'words':set()})
            keys, ivs = derive_keys_from_material(mats)

            rep.write(f"[info] blobs={len(blobs)}  keys={len(keys)}  ivs={len(ivs)}\n")

            seen_flags = set()
            for idx, (cipher, kind, origin) in enumerate(blobs, 1):
                rep.write(f"\n[b64_blob #{idx}] {kind} | from: {origin}\n")
                tries = aes_try_all(cipher, keys, ivs)

                scored: List[Tuple[int,str,bytes]] = []
                for tag, pt in tries:
                    scored.append((score_plaintext(pt), tag, pt))

                # 取前若干分数较高的结果写报告
                top = sorted(scored, key=lambda x: -x[0])[:10]
                for sc, tag, pt in top:
                    s = pt.decode("latin1","ignore")
                    rep.write(f"  [hit score={sc}] {tag}\n")
                    preview = s[:200].replace("\n"," ")
                    rep.write(f"    preview: {preview}\n")
                    # 抓 flag 形态
                    fgs = find_flags(s)
                    for f in fgs:
                        if f.lower() not in seen_flags:
                            cand.write(f"{f.lower()}  # from: {label} via {tag}; blob={idx}\n")
                            seen_flags.add(f.lower())

            rep.write("\n")

    print(f"✅ Probe finished.\n - report: {REPORT}\n - candidates: {CANDS}")

if __name__ == "__main__":
    main()
