#!/usr/bin/env python3
# 作用：用 PyMuPDF 逐页重建 PDF，丢弃一切旧对象/历史字节，并清空元数据
import fitz  # PyMuPDF
from pathlib import Path

src = Path("Group_13_clean3.pdf")  # 也可直接换成 Group_13.pdf
out = Path("Group_13_final.pdf")

orig = fitz.open(src.as_posix())
new  = fitz.open()
new.insert_pdf(orig, from_page=0, to_page=orig.page_count-1)  # 复制全部页面

# 清空/最小化元数据
try:
    new.set_metadata({})        # 清空标准元数据字典
    new.set_toc([])             # 没有目录就保持空
except Exception:
    pass

# 保存（开启清理与压缩）
new.save(out.as_posix(), deflate=True, clean=True)
new.close(); orig.close()
print("✅ rebuilt:", out)
