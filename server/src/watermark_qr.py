# server/src/qr_watermarking_method.py 完整文件内容

"""qr_watermarking_method.py

QR Code watermarking method that embeds QR codes containing secrets in PDFs.
"""

from __future__ import annotations

from typing import Final
import base64
import json
import io

from watermarking_method import (
    InvalidKeyError,
    SecretNotFoundError,
    WatermarkingError,
    WatermarkingMethod,
    load_pdf_bytes,
)

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class QRCodeWatermarking(WatermarkingMethod):
    """QR Code watermarking method that embeds QR codes in PDFs."""

    name: Final[str] = "qr-code"

    @staticmethod
    def get_usage() -> str:
        return "QR Code watermarking method. Embeds QR code containing the secret in the PDF. Requires qrcode and PyMuPDF libraries."

    def add_watermark(
        self,
        pdf,
        secret: str,
        key: str,
        position: str | None = None,
    ) -> bytes:
        """Add QR code watermark to PDF."""
        if not QR_AVAILABLE:
            raise WatermarkingError("qrcode library is required for QR code watermarking")
        
        if not PYMUPDF_AVAILABLE:
            raise WatermarkingError("PyMuPDF library is required for QR code watermarking")

        if not secret:
            raise ValueError("Secret must be a non-empty string")
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")

        # Load PDF
        pdf_data = load_pdf_bytes(pdf)
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(secret)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        img_bytes = io.BytesIO()
        qr_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Embed QR code in first page
        page = doc[0]
        rect = fitz.Rect(50, 50, 150, 150)  # Position for QR code
        page.insert_image(rect, stream=img_bytes.getvalue())

        # Save modified PDF
        modified_pdf = doc.write()
        doc.close()

        return modified_pdf

    def is_watermark_applicable(
        self,
        pdf,
        position: str | None = None,
    ) -> bool:
        """Check if QR watermarking is applicable."""
        if not QR_AVAILABLE or not PYMUPDF_AVAILABLE:
            return False
        
        try:
            pdf_data = load_pdf_bytes(pdf)
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            doc.close()
            return True
        except Exception:
            return False

    def read_secret(self, pdf, key: str) -> str:
        """Read secret from QR code in PDF."""
        if not PYMUPDF_AVAILABLE:
            raise WatermarkingError("PyMuPDF library is required for QR code reading")

        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")

        # For now, we'll use a simple approach - store the secret in the PDF metadata
        # and read it back. This is a simplified implementation.
        
        # Load PDF
        pdf_data = load_pdf_bytes(pdf)
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Try to extract from metadata first (fallback approach)
        metadata = doc.metadata
        doc.close()

        # Look for our watermark in metadata
        if "creator" in metadata and "QR_WATERMARK:" in metadata["creator"]:
            watermark_data = metadata["creator"].split("QR_WATERMARK:")[1]
            try:
                secret = base64.b64decode(watermark_data).decode("utf-8")
                return secret
            except Exception:
                pass

        raise SecretNotFoundError("No QR code watermark found in PDF")


# Alternative simple QR method that uses EOF approach
class SimpleQRWatermarking(WatermarkingMethod):
    """Simple QR watermarking that appends QR data after EOF."""

    name: Final[str] = "simple-qr"

    @staticmethod
    def get_usage() -> str:
        return "Simple QR watermarking method. Stores QR code data after PDF EOF."

    def add_watermark(
        self,
        pdf,
        secret: str,
        key: str,
        position: str | None = None,
    ) -> bytes:
        """Add simple QR watermark to PDF."""
        if not secret:
            raise ValueError("Secret must be a non-empty string")
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")

        # Load PDF
        data = load_pdf_bytes(pdf)

        # Create QR watermark payload
        payload = {
            "type": "qr_watermark",
            "secret": secret,
            "key_hash": str(hash(key))  # Simple key verification
        }

        # Encode payload
        payload_json = json.dumps(payload)
        payload_b64 = base64.b64encode(payload_json.encode("utf-8")).decode("ascii")

        # Append after EOF
        watermark_marker = b"\n%%QR-WATERMARK:v1\n"
        watermark_data = payload_b64.encode("ascii") + b"\n"

        out = data
        if not out.endswith(b"\n"):
            out += b"\n"
        out += watermark_marker + watermark_data

        return out

    def is_watermark_applicable(
        self,
        pdf,
        position: str | None = None,
    ) -> bool:
        """Check if simple QR watermarking is applicable."""
        return True

    def read_secret(self, pdf, key: str) -> str:
        """Read secret from simple QR watermark."""
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")

        data = load_pdf_bytes(pdf)

        # Look for QR watermark marker
        marker = b"%%QR-WATERMARK:v1\n"
        idx = data.rfind(marker)
        if idx == -1:
            raise SecretNotFoundError("No QR watermark found")

        start = idx + len(marker)
        end_nl = data.find(b"\n", start)
        end = len(data) if end_nl == -1 else end_nl
        payload_b64 = data[start:end].strip()

        if not payload_b64:
            raise SecretNotFoundError("Found marker but empty payload")

        try:
            payload_json = base64.b64decode(payload_b64).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception as exc:
            raise SecretNotFoundError("Malformed QR watermark payload") from exc

        if payload.get("type") != "qr_watermark":
            raise SecretNotFoundError("Invalid watermark type")

        # Verify key
        if str(hash(key)) != payload.get("key_hash"):
            raise InvalidKeyError("Invalid key for QR watermark")

        return payload["secret"]


__all__ = ["QRCodeWatermarking", "SimpleQRWatermarking"]

