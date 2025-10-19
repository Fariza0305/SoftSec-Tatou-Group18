#!/usr/bin/env python3
import os, re, base64, pathlib, subprocess, zlib, shutil
from PyPDF2 import PdfReader

# 目录与输出
PDF_DIR = "/home/lab/tatou/downloads"
WORK_DIR = "/tmp/pdf_deep_scan"
IMG_DIR  = os.path.join(WORK_DIR, "images")
OUT_REPORT      = "scan_report.txt"        # 详细步骤日志
OUT_CANDIDATES  = "candidates.txt"         # 统一候选（含来源）
OUT_URLS        = "urls_found.txt"         # 提取到的 URL/URI 线索
OUT_BASE64      = "base64_blobs.txt"       # 提取到的长 Base64 段

# 正则
HEX40   = re.compile(r"\b[a-f0-9]{40}\b")
HEX64   = re.compile(r"\b[a-f0-9]{64}\b")
B64     = re.compile(r"[A-Za-z0-9+/=]{20,}")  # 20+ 字符的粗匹配
URL_RE  = re.compile(r"(https?://[^\s<>()\"']+|/URI\s*\(([^)]+)\))", re.IGNORECASE)

# 运行外部命令
def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None

def has_tool(name):
    p = shutil.which(name)
    return p is not None

def decode_b64_if_possible(s: str):
    s = s.strip()
    if not s:
        return None
    # 宽松容错：去掉非B64常见字符
    if not re.fullmatch(r"[A-Za-z0-9+/=]+", s):
        return None
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s, validate=False)
    except Exception:
        return None

def write_line(path, line):
    with open(path, "a") as f:
        f.write(line.rstrip() + "\n")

def add_candidate(bag: list, val: str, origin: str):
    bag.append((val, origin))

def extract_urls(raw_text: str):
    urls = []
    for m in URL_RE.finditer(raw_text):
        if m.group(1):
            urls.append(m.group(1))
        elif m.group(2): # URI(name)
            urls.append(m.group(2))
    return urls

def analyze_pdf(pdf_path: str, summary: list):
    fname = os.path.basename(pdf_path)
    summary.append(f"\n=== Analyzing: {pdf_path}\n" + "="*60)
    candidates = []  # (value, origin)
    urls_found  = []
    b64_snips   = []

    # 读取原始字节
    data_bytes = pathlib.Path(pdf_path).read_bytes()
    data_text  = data_bytes.decode("latin1", "ignore")

    # 0) 先抓 URL/URI 线索（外链水印）
    urls_in_text = extract_urls(data_text)
    for u in urls_in_text:
        urls_found.append((u, "raw_bytes/URI"))
    if has_tool("strings"):
        s = run(["strings", "-n", "6", pdf_path])
        if s and s.stdout:
            for u in extract_urls(s.stdout):
                urls_found.append((u, "strings"))

    # 1) 元数据 + Base64 尝试
    try:
        reader = PdfReader(pdf_path)
        meta = reader.metadata or {}
        for k, v in meta.items():
            v = "" if v is None else str(v)
            # 直接扫哈希
            for h in HEX40.findall(v): add_candidate(candidates, h, f"metadata:{k}")
            for h in HEX64.findall(v): add_candidate(candidates, h, f"metadata:{k}")
            # Base64 解码
            for b in B64.findall(v):
                raw = decode_b64_if_possible(b)
                if raw:
                    # 原始二进制中再找哈希
                    t = raw.decode("latin1","ignore")
                    for h in HEX40.findall(t): add_candidate(candidates, h, f"metadata:{k}_b64")
                    for h in HEX64.findall(t): add_candidate(candidates, h, f"metadata:{k}_b64")
                    b64_snips.append((b, f"metadata:{k}"))
    except Exception as e:
        summary.append(f"[!] metadata/text parse failed: {e}")

    # 2) 文本层（PyPDF2）
    try:
        pages_text = "\n".join([p.extract_text() or "" for p in reader.pages])
        for h in HEX40.findall(pages_text): add_candidate(candidates, h, "text_layer")
        for h in HEX64.findall(pages_text): add_candidate(candidates, h, "text_layer")
        # 文本中长 Base64
        for b in B64.findall(pages_text):
            raw = decode_b64_if_possible(b)
            if raw:
                t = raw.decode("latin1","ignore")
                for h in HEX40.findall(t): add_candidate(candidates, h, "text_layer_b64")
                for h in HEX64.findall(t): add_candidate(candidates, h, "text_layer_b64")
                b64_snips.append((b, "text_layer"))
    except Exception:
        pass

    # 3) 不可见文字（pdftotext）
    if has_tool("pdftotext"):
        pt = run(["pdftotext", pdf_path, "-"])
        if pt and pt.stdout:
            for h in HEX40.findall(pt.stdout): add_candidate(candidates, h, "pdftotext")
            for h in HEX64.findall(pt.stdout): add_candidate(candidates, h, "pdftotext")
            for b in B64.findall(pt.stdout):
                raw = decode_b64_if_possible(b)
                if raw:
                    t = raw.decode("latin1","ignore")
                    for h in HEX40.findall(t): add_candidate(candidates, h, "pdftotext_b64")
                    for h in HEX64.findall(t): add_candidate(candidates, h, "pdftotext_b64")
                    b64_snips.append((b, "pdftotext"))
    else:
        summary.append("[!] pdftotext not found")

    # 4) 原始字节暴力匹配 + 压缩流 zlib inflate
    for h in HEX40.findall(data_text): add_candidate(candidates, h, "raw_bytes")
    for h in HEX64.findall(data_text): add_candidate(candidates, h, "raw_bytes")
    # 从二进制中抓长 Base64
    for b in B64.findall(data_text):
        raw = decode_b64_if_possible(b)
        if raw:
            t = raw.decode("latin1","ignore")
            for h in HEX40.findall(t): add_candidate(candidates, h, "raw_b64")
            for h in HEX64.findall(t): add_candidate(candidates, h, "raw_b64")
            b64_snips.append((b, "raw_bytes"))
    # zlib 流尝试解压
    for m in re.finditer(rb'stream\s*(.*?)\s*endstream', data_bytes, re.S):
        chunk = m.group(1).strip()
        try:
            infl = zlib.decompress(chunk)
            t = infl.decode("latin1","ignore")
            for h in HEX40.findall(t): add_candidate(candidates, h, "zlib_stream")
            for h in HEX64.findall(t): add_candidate(candidates, h, "zlib_stream")
            for b in B64.findall(t):
                raw = decode_b64_if_possible(b)
                if raw:
                    tt = raw.decode("latin1","ignore")
                    for h in HEX40.findall(tt): add_candidate(candidates, h, "zlib_stream_b64")
                    for h in HEX64.findall(tt): add_candidate(candidates, h, "zlib_stream_b64")
                    b64_snips.append((b, "zlib_stream"))
        except Exception:
            continue

    # 5) strings 扫描
    if has_tool("strings"):
        st = run(["strings", "-n", "6", pdf_path])
        if st and st.stdout:
            for h in HEX40.findall(st.stdout): add_candidate(candidates, h, "strings")
            for h in HEX64.findall(st.stdout): add_candidate(candidates, h, "strings")
            for b in B64.findall(st.stdout):
                raw = decode_b64_if_possible(b)
                if raw:
                    t = raw.decode("latin1","ignore")
                    for h in HEX40.findall(t): add_candidate(candidates, h, "strings_b64")
                    for h in HEX64.findall(t): add_candidate(candidates, h, "strings_b64")
                    b64_snips.append((b, "strings"))
    else:
        summary.append("[!] strings not found")

    # 6) 图片提取 + 放大 + QR 扫描
    os.makedirs(IMG_DIR, exist_ok=True)
    base = os.path.join(IMG_DIR, fname.replace(".pdf",""))
    if has_tool("pdfimages"):
        run(["pdfimages", "-all", pdf_path, base])
        imgs = [os.path.join(IMG_DIR, f) for f in os.listdir(IMG_DIR) if f.startswith(fname.replace(".pdf",""))]
        for img in imgs:
            # 尝试放大扫描（多倍率尝试）
            for scale in (200, 300, 400, 600):
                big = img + f".x{scale}.png"
                if has_tool("convert"):
                    run(["convert", img, "-resize", f"{scale}%", big])
                else:
                    big = img  # 退化到原图
                if has_tool("zbarimg"):
                    zr = run(["zbarimg", big])
                    if zr and zr.stdout:
                        for line in zr.stdout.strip().splitlines():
                            if ":" in line:
                                qr_val = line.split(":",1)[1].strip()
                                add_candidate(candidates, qr_val, f"QR({os.path.basename(big)})")
    else:
        summary.append("[!] pdfimages not found")

    # 写 URL 与 Base64 线索文件
    if urls_found:
        write_line(OUT_URLS, f"=== {fname} ===")
        for u, src in urls_found:
            write_line(OUT_URLS, f"{u}  # from: {src}")
        write_line(OUT_URLS, "")

    if b64_snips:
        write_line(OUT_BASE64, f"=== {fname} ===")
        # 去重 + 只保留较长的片段
        seen = set()
        for b, src in b64_snips:
            if len(b) < 28:  # 过滤太短的
                continue
            key = (b, src)
            if key in seen: 
                continue
            seen.add(key)
            write_line(OUT_BASE64, f"{b}  # from: {src}")
        write_line(OUT_BASE64, "")

    # 整理候选（加上 SHA256 -> 40位截断变体）
    uniq = {}
    for val, origin in candidates:
        if val not in uniq:
            uniq[val] = origin

    # 返回：有序 (val, origin)
    out = []
    for val, origin in uniq.items():
        out.append((val, origin))
        if len(val) == 64:
            out.append((val[:40], f"(truncated SHA256) from {origin}"))
    return out
# ---- main ----
def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    for p in (OUT_REPORT, OUT_CANDIDATES, OUT_URLS, OUT_BASE64):
        if os.path.exists(p):
            os.remove(p)

    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"❌ No PDFs found in {PDF_DIR}")
        return

    summary = []
    all_results = {}

    for pdf in pdfs:
        res = analyze_pdf(pdf, summary)
        all_results[os.path.basename(pdf)] = res

    # 写报告
    with open(OUT_REPORT, "w") as f:
        f.write("\n".join(summary))

    # 写候选
    with open(OUT_CANDIDATES, "w") as f:
        for fname, items in all_results.items():
            f.write(f"=== {fname} ===\n")
            if not items:
                f.write("(No candidates found)\n\n")
                continue
            # 优先输出 40 位值
            items_sorted = sorted(items, key=lambda x: (len(x[0])!=40, x[1]))
            seen = set()
            for val, origin in items_sorted:
                if val in seen: 
                    continue
                seen.add(val)
                f.write(f"{val}  # from: {origin}\n")
            f.write("\n")

    print("\n✅ v4.5 deep scan finished.")
    print(f"   - candidates: {OUT_CANDIDATES}")
    print(f"   - urls:       {OUT_URLS}")
    print(f"   - base64:     {OUT_BASE64}")
    print(f"   - report:     {OUT_REPORT}")

if __name__ == "__main__":
    main()
