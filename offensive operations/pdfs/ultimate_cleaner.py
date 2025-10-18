#!/usr/bin/env python3
# v7.1: 兼容 pikepdf 无 page.owner；写流统一用 Stream(pdf, ...)
import re
from pathlib import Path
import pikepdf
from pikepdf import Name, Dictionary, Stream
import fitz  # PyMuPDF

WATERMARK_KEYWORDS = [
    "Watermark", "Axel-Watermark", "Do not distribute", "Tatou",
    "Group", "FLAG", "Flag"
]
HEX_RE = re.compile(rb"\b[a-f0-9]{20,64}\b", re.I)
TJ_TEXT = re.compile(rb"\((.*?)\)\s*TJ?", re.S)
ARRAY_TJ_TEXT = re.compile(rb"\[\s*(\((?:.*?)\)\s*)+\]\s*TJ", re.S)

def strip_doclevel(pdf: pikepdf.Pdf) -> int:
    removed = 0
    root = getattr(pdf, "Root", None) or pdf.trailer.get("/Root")
    if root:
        for k in ("/Metadata","/OCProperties","/PieceInfo","/Lang","/MarkInfo","/XMP","/AcroForm","/OpenAction"):
            if k in root:
                try: del root[k]; removed += 1
                except: pass
    try:
        if pdf.docinfo: pdf.docinfo.clear(); removed += 1
    except: pass
    try:
        if "/ID" in pdf.trailer: del pdf.trailer["/ID"]; removed += 1
    except: pass
    return removed

def _read_stream_bytes(obj) -> bytes:
    if isinstance(obj, pikepdf.Stream):
        try: return obj.read_bytes()
        except: return b""
    if hasattr(obj, "get_stream_buffer"):
        try: return bytes(obj.get_stream_buffer())
        except: return b""
    return b""

def _clean_one_contents_blob(raw: bytes) -> tuple[bytes,int]:
    removed = 0
    def tj_replacer(m):
        nonlocal removed
        text = m.group(1)
        low = text.lower()
        if any(k.lower().encode() in low for k in WATERMARK_KEYWORDS) or HEX_RE.search(text):
            removed += 1
            return b""
        return m.group(0)
    def array_tj_replacer(m):
        nonlocal removed
        block = m.group(0)
        low = block.lower()
        if any(k.lower().encode() in low for k in WATERMARK_KEYWORDS) or HEX_RE.search(block):
            removed += 1
            return b" "
        return block
    new = TJ_TEXT.sub(tj_replacer, raw)
    new = ARRAY_TJ_TEXT.sub(array_tj_replacer, new)
    for m in list(HEX_RE.finditer(new)):
        s,e = m.span()
        new = new[:s] + b" "*(e-s) + new[e:]
        removed += 1
    return new, removed

def strip_page_annots_and_xobjects(page: Dictionary) -> int:
    removed = 0
    ann = page.get("/Annots", None)
    if ann:
        kept=[]
        for a in ann:
            subtype = a.get("/Subtype", None)
            nm  = str(a.get("/NM",""))
            cnt = str(a.get("/Contents",""))
            is_wm = (subtype in [Name("/Watermark"), Name("/Stamp"), Name("/FreeText")]) or \
                    any(k.lower() in nm.lower() or k.lower() in cnt.lower() for k in WATERMARK_KEYWORDS)
            if is_wm: removed += 1
            else: kept.append(a)
        if kept: page["/Annots"]=kept
        elif "/Annots" in page: del page["/Annots"]
    res = page.get("/Resources", None)
    if res and "/XObject" in res:
        xo = res["/XObject"]; todel=[]
        for name,_ in xo.items():
            if any(k.lower() in str(name).lower() for k in WATERMARK_KEYWORDS):
                todel.append(name)
        for name in todel:
            try: del xo[name]; removed += 1
            except: pass
        if isinstance(xo, Dictionary) and len(xo.keys())==0:
            try: del res["/XObject"]
            except: pass
    return removed

def strip_content_stream_keywords(page: Dictionary, pdf: pikepdf.Pdf) -> int:
    removed = 0
    cs = page.get("/Contents", None)
    if not cs: return 0

    # 多流
    if isinstance(cs, pikepdf.Array):
        blobs=[]; changed=False
        for obj in cs:
            raw = _read_stream_bytes(obj)
            if not raw:
                blobs.append(obj); continue
            new_raw, rm = _clean_one_contents_blob(raw)
            removed += rm
            if rm>0:
                blobs.append(Stream(pdf, new_raw)); changed=True
            else:
                blobs.append(obj)
        if changed:
            page[Name("/Contents")] = pikepdf.Array(blobs)
        return removed

    # 单流
    raw = _read_stream_bytes(cs)
    if not raw: return 0
    new_raw, rm = _clean_one_contents_blob(raw)
    removed += rm
    if rm>0:
        page[Name("/Contents")] = Stream(pdf, new_raw)
    return removed

def sanitize_single(input_pdf: Path, output_pdf: Path) -> dict:
    stats = {"doclevel_removed":0, "annots_xobj_removed":0, "content_removed":0}
    with pikepdf.open(input_pdf) as pdf:
        stats["doclevel_removed"] = strip_doclevel(pdf)
        for page in pdf.pages:
            stats["annots_xobj_removed"] += strip_page_annots_and_xobjects(page)
            stats["content_removed"]     += strip_content_stream_keywords(page, pdf)
        try: pdf.remove_unreferenced_resources()
        except: pass
        pdf.save(output_pdf)
    return stats

def rasterize_pdf(input_pdf: Path, output_pdf: Path, dpi=300):
    src = fitz.open(str(input_pdf)); out = fitz.open()
    for i in range(len(src)):
        page = src[i]; pix = page.get_pixmap(dpi=dpi)
        img_doc = fitz.open()
        rect = fitz.Rect(0,0,pix.width,pix.height)
        p = img_doc.new_page(width=pix.width, height=pix.height)
        p.insert_image(rect, pixmap=pix)
        out.insert_pdf(img_doc)
    out.save(str(output_pdf))

def main():
    here = Path(".")
    pdfs = sorted([p for p in here.iterdir() if p.suffix.lower()==".pdf" and p.is_file()])
    if not pdfs:
        print("❌ 未找到 PDF，请把文件放在当前目录再运行。"); return
    struct_dir = Path("cleaned_struct"); struct_dir.mkdir(exist_ok=True)
    render_dir = Path("cleaned_render"); render_dir.mkdir(exist_ok=True)
    log_lines=[]
    for p in pdfs:
        print(f"🧹 [1] 结构清洗: {p.name}")
        struct_out = struct_dir / f"{p.stem}_struct_clean.pdf"
        stats = sanitize_single(p, struct_out)
        log_lines.append(f"{p.name}: doclevel={stats['doclevel_removed']}, annots_xobj={stats['annots_xobj_removed']}, contents={stats['content_removed']} -> {struct_out.name}")
        print(f"📸 [2] 渲染兜底: {p.name}")
        render_out = render_dir / f"{p.stem}_render_clean.pdf"
        rasterize_pdf(struct_out, render_out)
    (struct_dir/"clean_log.txt").write_text("\n".join(log_lines)+"\n", encoding="utf-8")
    print("\n✅ 完成：\n  • 结构清洗版：cleaned_struct/*_struct_clean.pdf\n  • 渲染兜底版：cleaned_render/*_render_clean.pdf\n  • 日志：cleaned_struct/clean_log.txt")

if __name__ == "__main__":
    main()
