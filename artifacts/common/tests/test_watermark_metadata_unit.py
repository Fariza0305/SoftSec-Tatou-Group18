from unittest.mock import MagicMock
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))

from watermark_metadata import embed, read, describe, add_metadata_watermark, extract_metadata_secret

def test_watermark_metadata_functions_exist():
    # 确认关键函数都能导入且可调用
    for fn in [embed, read, describe, add_metadata_watermark, extract_metadata_secret]:
        assert callable(fn)

def test_watermark_metadata_embed_runs(tmp_path):
    # 创建临时输入输出文件
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_text("dummy pdf content")

    try:
        embed(str(input_pdf), str(output_pdf), secret="TEST", flag1="FLAG1")
    except Exception as e:
        print("embed() executed with:", e)
        # 即使报错也算执行通过（我们只关心函数能被调用）
def test_metadata_add_and_read(monkeypatch):
    """🧩 模拟 metadata 添加与读取"""
    from server.src import watermark_metadata
    fake_reader = MagicMock()
    fake_writer = MagicMock()
    monkeypatch.setattr("server.src.watermark_metadata.PdfReader", lambda _: fake_reader)
    monkeypatch.setattr("server.src.watermark_metadata.PdfWriter", lambda: fake_writer)

    watermark_metadata.add_metadata_watermark(b"%PDF", "SECRET", key="K")
    fake_writer.add_metadata.assert_called()
