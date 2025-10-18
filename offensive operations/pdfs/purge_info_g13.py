import pikepdf
from pathlib import Path

src = Path("Group_13.pdf"); out = Path("Group_13_clean2.pdf")
with pikepdf.open(src) as pdf:
    # 1) 清空 Info 字典（Title/Subject/Keywords/Producer/Creator 等）
    try:
        if pdf.docinfo:
            pdf.docinfo.clear()
    except Exception:
        pass
    # 2) 去掉文档级 Metadata（若有）
    root = getattr(pdf, "Root", None) or pdf.trailer.get("/Root")
    try:
        if root and "/Metadata" in root:
            del root["/Metadata"]
    except Exception:
        pass
    pdf.save(out)
print("✅ done:", out)
