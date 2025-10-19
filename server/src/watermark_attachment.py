"""
Attachment watermark
- 将 {secret, intended_for, flag1...} 打成 JSON，作为嵌入附件写入 PDF
- 类接口：AttachmentWatermark.description / .add_watermark(...) / .read_secret(...)
- 兼容 watermarking_method.py 里对类的引用；同时导出 WATERMARK_METHODS / METHODS 供统一注册
- 不从项目内其他模块导入，避免循环
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Iterable, Tuple
import io
import json
import time

from pypdf import PdfReader, PdfWriter

METHOD_NAME = "attachment"
METHOD_DESC = "Embed secret (JSON) as an attached file inside the PDF (EmbeddedFiles)."
ATTACH_NAME = "tatou_info.json"  # 我们写入/读取的附件文件名


# ----------------------- 内部工具 -----------------------
def _copy_pages(reader: PdfReader) -> PdfWriter:
    w = PdfWriter()
    for p in reader.pages:
        w.add_page(p)
    return w


def _iter_embedded_files(reader: PdfReader) -> Iterable[Tuple[str, bytes]]:
    """
    遍历 PDF 中的嵌入文件，yield (name, data)。
    兼容 pypdf 3.x：优先 reader.attachments（如有），否则回退 Names/EmbeddedFiles。
    """
    # pypdf 新版提供 reader.attachments（dict[str, bytes]）
    try:
        atts = getattr(reader, "attachments", None)
        if isinstance(atts, dict):
            for k, v in atts.items():
                if isinstance(k, str) and isinstance(v, (bytes, bytearray)):
                    yield k, bytes(v)
            return
    except Exception:
        pass

    # 回退走 Names → EmbeddedFiles → Names
    try:
        root = reader.trailer.get("/Root", {})
        names = root.get("/Names")
        if not names:
            return
        ef_tree = names.get("/EmbeddedFiles")
        if not ef_tree:
            return
        arr = ef_tree.get("/Names")
        if not isinstance(arr, list):
            return
        # 结构：[name1, fileSpec1, name2, fileSpec2, ...]
        for i in range(0, len(arr), 2):
            try:
                name_obj = arr[i]
                filespec = arr[i + 1].get_object()
                name = str(name_obj)
                ef = filespec.get("/EF")
                if not ef:
                    continue
                f_stream = ef.get("/F")
                if not f_stream:
                    continue
                data = f_stream.get_object().get_data()
                yield name, data
            except Exception:
                continue
    except Exception:
        return


# ----------------------- 类接口（兼容旧代码） -----------------------
class AttachmentWatermark:
    """与现有 watermarking_method.py 兼容的类接口"""
    description = METHOD_DESC

    def add_watermark(
        self,
        pdf: bytes,
        secret: str = "",
        *,
        intended_for: str = "",
        key: Optional[str] = None,
        position: Optional[str] = None,
        flag1: Optional[str] = None,
    ) -> bytes:
        """
        将信息写入 PDF 附件（JSON）。
        返回新的 PDF bytes。
        """
        import io, json, time, warnings
        from PyPDF2 import PdfReader, PdfWriter

        payload: Dict[str, Any] = {
            "secret": secret or "",
            "intended_for": intended_for or "",
            "flag1": flag1 or "",
            "key": key or "",
            "position": position or "",
            "method": METHOD_NAME,
            "version": "v1",
            "timestamp": int(time.time()),
        }
        payload_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

        try:
            reader = PdfReader(io.BytesIO(pdf))
            writer = _copy_pages(reader)
            if len(reader.pages) == 0:
                warnings.warn("[attachment] ⚠️ Input PDF has no pages — adding a blank page.")
                writer.add_blank_page(width=595, height=842)
        except Exception as e:
            print(f"[attachment] ⚠️ Failed to read input PDF: {e}")
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)

        # ✅ 把 JSON 附件加入 PDF
        writer.add_attachment(ATTACH_NAME, payload_bytes)

        out = io.BytesIO()
        writer.write(out)
        result = out.getvalue()

        print(f"[attachment] ✅ Watermark embedded ({len(result)} bytes, method={METHOD_NAME})")
        return result

    def read_secret(
        self,
        pdf: bytes,
        *,
        key: Optional[str] = None,
        position: Optional[str] = None,
    ) -> Dict[str, Any] | str:
        """
        从 PDF 读取我们写入的附件；解析 JSON 成 dict，失败则返回原文本，未找到返回空字符串。
        """
        reader = PdfReader(io.BytesIO(pdf))
        for name, data in _iter_embedded_files(reader):
            try:
                if name == ATTACH_NAME:
                    txt = data.decode("utf-8", errors="ignore")
                    try:
                        return json.loads(txt)
                    except Exception:
                        return txt
            except Exception:
                continue
        return ""


# ----------------------- 同时提供函数式 API（可选） -----------------------
def add_attachment_watermark(
    pdf: bytes,
    secret: str = "",
    *,
    intended_for: str = "",
    key: Optional[str] = None,
    position: Optional[str] = None,
    flag1: Optional[str] = None,
) -> bytes:
    """函数式封装（便于别处直接调用）"""
    return AttachmentWatermark().add_watermark(
        pdf,
        secret=secret,
        intended_for=intended_for,
        key=key,
        position=position,
        flag1=flag1,
    )


def extract_attachment_secret(
    pdf: bytes,
    *,
    key: Optional[str] = None,
    position: Optional[str] = None,
) -> Dict[str, Any] | str:
    """函数式封装"""
    return AttachmentWatermark().read_secret(pdf, key=key, position=position)


# ----------------------- 注册到统一表 -----------------------
WATERMARK_METHODS: Dict[str, Dict[str, Any]] = {
    METHOD_NAME: {
        "description": METHOD_DESC,
        "add": add_attachment_watermark,
        "extract": extract_attachment_secret,
    }
}
# 兼容别名
METHODS = WATERMARK_METHODS

print(f"[attachment] Registered watermark method: {list(WATERMARK_METHODS.keys())}")
