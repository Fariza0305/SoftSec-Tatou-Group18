"""
真实水印功能测试（精简版 - 不使用Mock）

测试真实的水印添加和提取功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import watermark_attachment
from server.src import watermark_metadata
from server.src import watermark_qr


def create_minimal_pdf():
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
xref
0 3
trailer
<< /Root 1 0 R >>
%%EOF"""


class TestAttachmentWatermarkReal:
    """测试真实的attachment水印功能"""
    
    def test_add_and_extract_with_key(self):
        """✅ 测试带密钥的水印"""
        pdf_in = create_minimal_pdf()
        secret = "MY_SECRET"
        key = "MY_KEY"
        
        pdf_out = watermark_attachment.add_attachment_watermark(
            pdf_in, secret=secret, key=key
        )
        
        assert pdf_out.startswith(b'%PDF')
        assert len(pdf_out) > len(pdf_in)
        
        extracted = watermark_attachment.extract_attachment_secret(pdf_out, key=key)
        assert extracted == secret


class TestMetadataWatermarkReal:
    """测试真实的metadata水印功能"""
    
    def test_metadata_add_and_extract(self):
        """✅ 测试metadata水印"""
        pdf_in = create_minimal_pdf()
        secret = "METADATA_SECRET"
        
        pdf_out = watermark_metadata.add_metadata_watermark(pdf_in, secret=secret)
        
        assert pdf_out.startswith(b'%PDF')
        
        extracted = watermark_metadata.extract_metadata_secret(pdf_out)
        assert isinstance(extracted, str)


class TestQRWatermarkReal:
    """测试真实的QR码水印功能"""
    
    def test_qr_add_and_extract(self):
        """✅ 测试QR水印"""
        pdf_in = create_minimal_pdf()
        secret = "QR_SECRET"
        
        pdf_out = watermark_qr.add_qr_watermark(pdf_in, secret=secret)
        
        assert pdf_out.startswith(b'%PDF')
        assert len(pdf_out) > len(pdf_in)
        
        extracted = watermark_qr.extract_qr_secret(pdf_out)
        assert isinstance(extracted, str)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
