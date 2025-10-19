#!/usr/bin/env python3
import pikepdf
from pathlib import Path

src = Path("Group_13.pdf")
out = Path("Group_13_clean3.pdf")

with pikepdf.open(src) as pdf:
    # 1. 清空 Info 字典
    try:
        if pdf.docinfo:
            pdf.docinfo.clear()
            print("🧹 Cleared docinfo.")
    except Exception:
        pass

    # 2. 删除文档级 Metadata 引用
    root = getattr(pdf, "Root", None) or pdf.trailer.get("/Root")
    try:
        if root and "/Metadata" in root:
            del root["/Metadata"]
            print("🧹 Deleted /Metadata reference.")
    except Exception:
        pass

    # 3. 删除常见敏感键（可选）
    for k in ("/OCProperties", "/PieceInfo", "/XMP", "/Lang", "/MarkInfo", "/OpenAction"):
        try:
            if root and k in root:
                del root[k]
                print(f"🧹 Deleted {k}.")
        except Exception:
            pass

    # ✅ 4. 保存时强制“重建文件”来替代 incremental=False
    # 用 save() 再 open() 再 save() 的“两次保存法”清掉旧对象引用
    temp = out.with_suffix(".tmp.pdf")
    pdf.save(temp, linearize=False, compress_streams=True)

# 重新打开一次并再次保存，彻底丢弃增量历史
with pikepdf.open(temp) as final_pdf:
    final_pdf.save(out, linearize=False, compress_streams=True)

temp.unlink(missing_ok=True)
print("✅ Done. Clean PDF saved as:", out)
