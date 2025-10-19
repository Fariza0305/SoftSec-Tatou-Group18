#!/usr/bin/env python3
import re, base64, binascii, pathlib, textwrap
from PyPDF2 import PdfReader

PDF_DIR = "/home/lab/tatou/downloads"
OUT = "key_hints.txt"

# 基本模式
UUID_DASH   = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)
UUID_PLAIN  = re.compile(r"\b[0-9a-f]{32}\b", re.I)
HEX16       = re.compile(r"\b[0-9a-f]{32}\b", re.I)   # 16 B key
HEX20       = re.compile(r"\b[0-9a-f]{40}\b", re.I)   # 20 B (SHA1 digest)
HEX24       = re.compile(r"\b[0-9a-f]{48}\b", re.I)   # 24 B key
HEX32       = re.compile(r"\b[0-9a-f]{64}\b", re.I)   # 32 B key / SHA256
B64         = re.compile(r"[A-Za-z0-9+/=]{28,}")      # 宽松：>=28 chars
URL_RE      = re.compile(r"https?://[^\s<>()\"']+", re.I)
URI_RE      = re.compile(r"/URI\s*\(([^)]+)\)")
EMAIL_RE    = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE    = re.compile(r"\b(?:\+?\d{1,3}[- ]?)?(?:\d{3,4}[- ]?){2,4}\d{2,4}\b")
STU_RE      = re.compile(r"\b(20\d{2}[01]\d[0-3]\d|[A-Za-z]{2}\d{6,10})\b")  # 简单学号/日期串
KEYWORDS    = re.compile(r"(key|secret|salt|iv|nonce|token|passwd|password|digest|mac|sign|tw-|tatou)", re.I)

def surround(text, start, end, width=90):
    s = max(0, start - 50)
    e = min(len(text), end + 50)
    snippet = text[s:e].replace("\n"," ")
    if len(snippet) > width:
        snippet = snippet[:width] + " ..."
    return snippet

def write_block(lines, header, items):
    lines.append(header)
    if not items:
        lines.append("  (none)")
        lines.append("")
        return
    for lab, val, ctx in items:
        lines.append(f"  - {lab}: {val}")
        if ctx:
            lines.append("    context: " + ctx)
    lines.append("")

def scan_pdf(path: pathlib.Path):
    results = {
        "metadata": [],
        "xmp": [],
        "uuid": [],
        "hex_keys": [],
        "urls": [],
        "emails": [],
        "phones": [],
        "ids": [],
        "b64": [],
        "keywords": [],
    }

    # 原始字节与宽松文本视图
    raw = path.read_bytes()
    txt = raw.decode("latin1", "ignore")

    # 1) Metadata
    try:
        r = PdfReader(str(path))
        meta = r.metadata or {}
        for k, v in meta.items():
            vs = "" if v is None else str(v)
            if vs.strip():
                results["metadata"].append((k, vs, ""))
                # 顺带扫描 metadata 中的 B64/HEX/URL
                for m in HEX16.findall(vs): results["hex_keys"].append(("hex16(meta)", m, ""))
                for m in HEX20.findall(vs): results["hex_keys"].append(("hex20(meta)", m, ""))
                for m in HEX24.findall(vs): results["hex_keys"].append(("hex24(meta)", m, ""))
                for m in HEX32.findall(vs): results["hex_keys"].append(("hex32(meta)", m, ""))
                for m in B64.findall(vs):   results["b64"].append(("b64(meta)", m, ""))
                for m in URL_RE.findall(vs):results["urls"].append(("url(meta)", m, ""))
    except Exception as e:
        results["metadata"].append(("error", f"{e}", ""))

    # 2) XMP（简单截取）
    for xm in re.finditer(r"<x:xmpmeta\b.*?</x:xmpmeta>", txt, re.S|re.I):
        frag = xm.group(0)
        short = frag[:200].replace("\n"," ") + (" ..." if len(frag)>200 else "")
        results["xmp"].append(("xmp", short, ""))
        # 也在 XMP 里找可疑元素
        for m in KEYWORDS.finditer(frag):
            results["keywords"].append(("keyword(xmp)", m.group(0), surround(txt, m.start(), m.end())))
        for m in URL_RE.findall(frag):
            results["urls"].append(("url(xmp)", m, ""))
        for m in EMAIL_RE.findall(frag):
            results["emails"].append(("email(xmp)", m, ""))
        for m in HEX16.findall(frag): results["hex_keys"].append(("hex16(xmp)", m, ""))
        for m in HEX20.findall(frag): results["hex_keys"].append(("hex20(xmp)", m, ""))
        for m in HEX24.findall(frag): results["hex_keys"].append(("hex24(xmp)", m, ""))
        for m in HEX32.findall(frag): results["hex_keys"].append(("hex32(xmp)", m, ""))
        for m in B64.findall(frag):   results["b64"].append(("b64(xmp)", m, ""))

    # 3) URI/URL/Email/Phone/ID 在线索附近标注上下文
    for m in URL_RE.finditer(txt):
        results["urls"].append(("url", m.group(0), surround(txt, m.start(), m.end())))
    for m in URI_RE.finditer(txt):
        results["urls"].append(("URI", m.group(1), surround(txt, m.start(), m.end())))
    for m in EMAIL_RE.finditer(txt):
        results["emails"].append(("email", m.group(0), surround(txt, m.start(), m.end())))
    for m in PHONE_RE.finditer(txt):
        results["phones"].append(("phone", m.group(0), surround(txt, m.start(), m.end())))
    for m in STU_RE.finditer(txt):
        results["ids"].append(("id", m.group(0), surround(txt, m.start(), m.end())))

    # 4) UUID / HEX keys（字节视图）
    for m in UUID_DASH.finditer(txt):
        results["uuid"].append(("uuid", m.group(0), surround(txt, m.start(), m.end())))
    # 无连字符的 32hex 既可能是uuid也可能是16B key，去重时保留标签区分
    for m in UUID_PLAIN.finditer(txt):
        results["uuid"].append(("uuid_plain", m.group(0), surround(txt, m.start(), m.end())))

    for m in HEX16.finditer(txt): results["hex_keys"].append(("hex16", m.group(0), surround(txt, m.start(), m.end())))
    for m in HEX20.finditer(txt): results["hex_keys"].append(("hex20", m.group(0), surround(txt, m.start(), m.end())))
    for m in HEX24.finditer(txt): results["hex_keys"].append(("hex24", m.group(0), surround(txt, m.start(), m.end())))
    for m in HEX32.finditer(txt): results["hex_keys"].append(("hex32", m.group(0), surround(txt, m.start(), m.end())))

    # 5) Base64 大段（字节视图）
    for m in B64.finditer(txt):
        blob = m.group(0)
        # 简单判断是否可解码且长度像AES块/摘要
        dec = None
        try:
            padded = blob + "=" * (-len(blob) % 4)
            dec = base64.b64decode(padded)
        except Exception:
            dec = None
        note = ""
        if dec:
            L = len(dec)
            # 标注典型长度
            if L in (16,24,32,48,64,20,21):
                note = f"(decoded_len={L})"
        results["b64"].append(("b64", blob, (note or "")))

    # 6) keyword anchor（在全文中定位 key/salt/iv 关键字）
    for m in KEYWORDS.finditer(txt):
        results["keywords"].append(("keyword", m.group(0), surround(txt, m.start(), m.end())))

    # 去重与合并
    def dedup(seq):
        seen = set(); out=[]
        for lab, val, ctx in seq:
            key = (lab.lower(), val)
            if key in seen: continue
            seen.add(key); out.append((lab, val, ctx))
        return out

    for k in results:
        results[k] = dedup(results[k])
    return results

def main():
    out_lines = []
    pdfs = sorted([p for p in pathlib.Path(PDF_DIR).iterdir() if p.suffix.lower()==".pdf"])
    if not pdfs:
        print(f"❌ no PDFs in {PDF_DIR}"); return

    for pdf in pdfs:
        out_lines.append(f"=== {pdf.name} ===")
        res = scan_pdf(pdf)
        write_block(out_lines, "[metadata]",     res["metadata"])
        write_block(out_lines, "[xmp_snippets]", res["xmp"])
        write_block(out_lines, "[keywords_hits]",res["keywords"])
        write_block(out_lines, "[urls/uris]",    res["urls"])
        write_block(out_lines, "[emails]",       res["emails"])
        write_block(out_lines, "[phones]",       res["phones"])
        write_block(out_lines, "[ids_like]",     res["ids"])
        write_block(out_lines, "[uuids]",        res["uuid"])
        write_block(out_lines, "[hex_keys]",     res["hex_keys"])
        write_block(out_lines, "[base64_blobs]", res["b64"])

    pathlib.Path(OUT).write_text("\n".join(out_lines), encoding="utf-8")
    print(f"✅ wrote {OUT}")

if __name__ == "__main__":
    main()
