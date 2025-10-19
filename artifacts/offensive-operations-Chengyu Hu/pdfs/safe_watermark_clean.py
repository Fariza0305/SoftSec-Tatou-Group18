#!/usr/bin/env python3
# 保守去水印 v1.0（不改 Contents，只清理元数据/注释/水印 XObject）
import sys, re
from pathlib import Path
import pikepdf
from pikepdf import Name, Dictionary, Stream

WM_KEYWORDS = [
    "watermark", "axel-watermark", "tatou",
    "do not distribute", "flag", "group "
]

def has_wm_keyword(s: str) -> bool:
    ls = s.lower()
    return any(k in ls for k in WM_KEYWORDS)

def strip_doclevel(pdf: pikepdf.Pdf) -> int:
    removed = 0
    root = getattr(pdf, "Root", None) or pdf.trailer.get("/Root")
    for k in ("/Metadata","/OCProperties","/PieceInfo","/Lang","/MarkInfo","/XMP","/OpenAction"):
        try:
            if root and k in root:
                del root[k]; removed += 1
        except: pass
    try:
        if pdf.docinfo:
            pdf.docinfo.clear(); removed += 1
    except: pass
    try:
        if "/ID" in pdf.trailer:
            del pdf.trailer["/ID"]; removed += 1
    except: pass
    return removed

def read_bytes(obj) -> bytes:
    if isinstance(obj, pikepdf.Stream):
        try: return obj.read_bytes()
        except: return b""
    if hasattr(obj, "get_stream_buffer"):
        try: return bytes(obj.get_stream_buffer())
        except: return b""
    return b""

def strip_page_annots(page: Dictionary) -> int:
    """移除水印/印章/自由文本注释或带水印关键词的注释"""
    removed = 0
    ann = page.get("/Annots", None)
    if not ann:
        return 0
    keep = []
    for a in ann:
        subtype = a.get("/Subtype", None)
        nm  = str(a.get("/NM",""))
        cnt = str(a.get("/Contents",""))
        ap  = a.get("/AP", None)
        ap_bytes = b""
        if ap and "/N" in ap:
            try:
                ap_n = ap["/N"]
                if isinstance(ap_n, pikepdf.Stream):
                    ap_bytes = read_bytes(ap_n)
            except: pass
        is_wm = False
        if subtype in [Name("/Watermark"), Name("/Stamp"), Name("/FreeText")]:
            is_wm = True
        if (nm and has_wm_keyword(nm)) or (cnt and has_wm_keyword(cnt)):
            is_wm = True
        if ap_bytes and has_wm_keyword(ap_bytes.decode("latin-1","ignore")):
            is_wm = True

        if is_wm:
            removed += 1
        else:
            keep.append(a)

    if keep:
        page["/Annots"] = keep
    elif "/Annots" in page:
        del page["/Annots"]
    return removed

def strip_watermark_xobjects(page: Dictionary, pdf: pikepdf.Pdf) -> int:
    """删除资源表里命名/内容带水印特征的 XObject（不改 Contents 引用）"""
    removed = 0
    res = page.get("/Resources", None)
    if not res or "/XObject" not in res:
        return 0
    xo = res["/XObject"]
    to_del = []
    for name, obj in list(xo.items()):
        # 1) 名称里含关键词
        if has_wm_keyword(str(name)):
            to_del.append(name); continue
        # 2) 尝试读流，看看是否有关键词
        try:
            if isinstance(obj, pikepdf.Stream):
                b = read_bytes(obj)
                if b and has_wm_keyword(b.decode("latin-1","ignore")):
                    to_del.append(name)
        except: pass

    for n in to_del:
        try:
            del xo[n]; removed += 1
        except: pass

    # 如果删空了 XObject，顺手清掉键
    try:
        if isinstance(xo, Dictionary) and len(xo.keys())==0:
            del res["/XObject"]
    except: pass

    return removed

def clean_one(in_pdf: Path, out_pdf: Path) -> dict:
    stats = {"doclevel":0, "annots":0, "xobj":0}
    with pikepdf.open(in_pdf) as pdf:
        stats["doclevel"] = strip_doclevel(pdf)
        for page in pdf.pages:
            stats["annots"] += strip_page_annots(page)
            stats["xobj"]   += strip_watermark_xobjects(page, pdf)
        # 不动 Contents，尽量不破坏版式
        pdf.save(out_pdf)
    return stats

def main():
    files = [Path(f) for f in sys.argv[1:]] if len(sys.argv)>1 else sorted(Path(".").glob("*.pdf"))
    if not files:
        print("没有找到 PDF。把要处理的 PDF 放到当前目录或传参指定。")
        return
    outdir = Path("cleaned_safe")
    outdir.mkdir(exist_ok=True)
    log = []
    for f in files:
        outp = outdir / f"{f.stem}_safe.pdf"
        print(f"🧹 清理: {f.name} -> {outp.name}")
        st = clean_one(f, outp)
        log.append(f"{f.name}: doc={st['doclevel']} annots={st['annots']} xobj={st['xobj']} => {outp.name}")
    (outdir/"clean_log.txt").write_text("\n".join(log)+"\n", encoding="utf-8")
    print("✅ 完成。输出在 cleaned_safe/ ，统计见 cleaned_safe/clean_log.txt")

if __name__ == "__main__":
    main()
