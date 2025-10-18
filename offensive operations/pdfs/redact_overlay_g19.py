import fitz  # PyMuPDF
from pathlib import Path
import re

src = Path("Group_19.pdf"); out = Path("Group_19_redacted.pdf")
# 要遮盖的短语/模式（你可按需增加）
PATTERNS = [
    r"Watermarked with Axel-?Watermark",
    r"Do\s+not\s+distribute",
    r"Fingerprint:\s*[a-fA-F0-9]{64}",
    r"gAAAAA[0-9A-Za-z_\-+/=]{10,}"  # 类似 Fernet/GCM 的密文片段
]
REGEXES = [re.compile(p, re.I) for p in PATTERNS]

doc = fitz.open(src.as_posix())
for page in doc:
    text_instances = page.get_text("blocks")  # [(x0,y0,x1,y1,"text",...)]
    for x0,y0,x1,y1,txt,*_ in text_instances:
        if any(rx.search(txt) for rx in REGEXES):
            # 在该块区域画不透明白底矩形
            r = fitz.Rect(x0, y0, x1, y1)
            shape = page.new_shape()
            shape.draw_rect(r)
            shape.finish(color=(1,1,1), fill=(1,1,1))  # 白底
            shape.commit()
doc.save(out, deflate=True, clean=True)
print("✅ done:", out)
