#!/usr/bin/env python3
import sys, re
from pathlib import Path
import pikepdf
from pikepdf import Name

def sanitize(inp, outp):
    with pikepdf.open(inp) as pdf:
        # 1) 文档信息与 XMP
        try: pdf.docinfo.clear()
        except: pass
        for k in ("/Metadata","/PieceInfo","/MarkInfo","/OCProperties","/Lang"):
            if k in pdf.root: del pdf.root[k]
        # 2) Trailer ID
        try:
            if "/ID" in pdf.trailer: del pdf.trailer["/ID"]
        except: pass
        # 3) 页注解：常见水印类去除（Watermark/Stamp/FreeText；或包含关键字的注解）
        removed = 0
        keywords = ("Watermark","Do not distribute","Axel-Watermark","Tatou","fingerprint")
        for page in pdf.pages:
            ann = page.get("/Annots", None)
            if not ann: continue
            kept=[]
            for a in ann:
                st = a.get("/Subtype", None)
                txt = str(a.get("/Contents",""))
                nm  = str(a.get("/NM",""))
                is_wm = (st in [Name("/Watermark"), Name("/Stamp"), Name("/FreeText")]) \
                        or any(k in txt or k in nm for k in keywords)
                if is_wm: removed += 1
                else: kept.append(a)
            if kept: page["/Annots"] = kept
            elif "/Annots" in page: del page["/Annots"]
        # 4) 删除未引用资源（减小泄露面）
        try: pdf.remove_unreferenced_resources()
        except: pass
        pdf.save(outp)
    return removed

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print("Usage: pdf_sanitize.py input.pdf output.pdf")
        sys.exit(2)
    rm = sanitize(sys.argv[1], sys.argv[2])
    print(f"[sanitize] removed_annots={rm}")
