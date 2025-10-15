from typing import Optional
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import os

METHOD_NAME = "metadata"
METHOD_DESC = "Embed the secret and flag1 in PDF Document Info fields (plaintext)."

INFO_SECRET_KEY   = "/TatouSecret"
INFO_INTENDED_FOR = "/TatouIntendedFor"
INFO_METHOD       = "/TatouMethod"
INFO_TIMESTAMP    = "/TatouTimestamp"
INFO_VERSION      = "/TatouVersion"
INFO_FLAG1        = "/TatouFlag1"

def _resolve_flag1(flag1_param: Optional[str]) -> str:
    # 优先使用传入参数；否则使用环境变量 FLAG1；都没有则为空字符串
    if flag1_param is not None and flag1_param != "":
        return flag1_param
    return os.getenv("FLAG1", "")

def embed(input_pdf_path: str, output_pdf_path: str, *,
          secret: str,
          intended_for: str,
          key: Optional[str] = None,
          position: Optional[str] = None,
          flag1: Optional[str] = None) -> None:
    """
    将 secret、intended_for、flag1 等以明文写入 PDF 的 Info metadata。
    """
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    meta = {k: v for k, v in (reader.metadata or {}).items() if isinstance(k, str)}

    meta[INFO_SECRET_KEY]   = secret
    meta[INFO_INTENDED_FOR] = intended_for or ""
    meta[INFO_METHOD]       = METHOD_NAME
    meta[INFO_VERSION]      = "v1"
    meta[INFO_TIMESTAMP]    = datetime.utcnow().isoformat() + "Z"
    meta[INFO_FLAG1]        = _resolve_flag1(flag1)

    writer.add_metadata(meta)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

def read(input_pdf_path: str) -> dict:
    """
    从 PDF metadata 读取 secret 与 flag1（明文）。
    注意：此函数返回明文，路由层必须负责是否泄露（路由层会做掩码/控制）。
    """
    reader = PdfReader(input_pdf_path)
    meta = reader.metadata or {}
    return {
        "secret":        meta.get(INFO_SECRET_KEY),
        "intended_for":  meta.get(INFO_INTENDED_FOR),
        "method":        meta.get(INFO_METHOD) or METHOD_NAME,
        "version":       meta.get(INFO_VERSION) or "v1",
        "timestamp":     meta.get(INFO_TIMESTAMP),
        "flag1":         meta.get(INFO_FLAG1) or "",
    }

def describe() -> dict:
    return {"name": METHOD_NAME, "description": METHOD_DESC}

# ======== 兼容服务器调用的包装函数（bytes <-> 文件路径）========
from typing import Optional, Dict, Any
import tempfile

def add_metadata_watermark(pdf: bytes,
                           secret: str = "",
                           *,
                           intended_for: str = "",
                           key: Optional[str] = None,
                           position: Optional[str] = None,
                           flag1: Optional[str] = None) -> bytes:
    """
    服务器期望的接口：输入/输出都是 bytes
    这里用临时文件落地 -> 复用现有 embed()
    """
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.pdf")
        outp = os.path.join(td, "out.pdf")
        with open(inp, "wb") as f:
            f.write(pdf)
        # 复用你现有的文件路径版本
        embed(
            input_pdf_path=inp,
            output_pdf_path=outp,
            secret=secret,
            intended_for=intended_for,
            key=key,
            position=position,
            flag1=flag1,
        )
        with open(outp, "rb") as f:
            return f.read()

def extract_metadata_secret(pdf: bytes,
                            *,
                            key: Optional[str] = None,
                            position: Optional[str] = None) -> Dict[str, Any] | str:
    """
    服务器期望的接口：输入 bytes，返回 dict/str（都可 JSON 序列化）
    """
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.pdf")
        with open(inp, "wb") as f:
            f.write(pdf)
        return read(inp)

# ======== 向统一注册表注册（供 /api/get-watermarking-methods 使用）========

WATERMARK_METHODS = {
    "metadata": {
        "description": "Embed secret and flag1 in PDF Document Info fields (plaintext).",
        "add": add_metadata_watermark,
        "extract": extract_metadata_secret,
    }
}

print(f"[metadata] Registered watermark method: {list(WATERMARK_METHODS.keys())}")
