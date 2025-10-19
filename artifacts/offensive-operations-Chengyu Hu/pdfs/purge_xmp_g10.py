#!/usr/bin/env python3
import pikepdf
from pathlib import Path

TARGETS = [b"secret_digest", b"p0_salt", b"p0_mac"]

def looks_sensitive(b: bytes) -> bool:
    s = b.lower()
    return any(t in s for t in TARGETS)

src = Path("Group_10.pdf")
out = Path("Group_10_clean2.pdf")

with pikepdf.open(src) as pdf:
    # 1️⃣ 删除文档级 Metadata 引用
    root = getattr(pdf, "Root", None) or pdf.trailer.get("/Root")
    if root and "/Metadata" in root:
        print("🧹 删除 /Metadata 引用...")
        del root["/Metadata"]

    # 2️⃣ 遍历所有对象
    for objnum, obj in enumerate(pdf.objects):
        if isinstance(obj, pikepdf.Stream):
            try:
                data = obj.read_bytes()
                if looks_sensitive(data):
                    print(f"🧽 清空对象 #{objnum} 中的敏感流")
                    obj.write(b"")
            except Exception as e:
                print(f"⚠️  处理对象 #{objnum} 出错: {e}")

    pdf.save(out)

print("✅ 完成！输出文件：", out)
