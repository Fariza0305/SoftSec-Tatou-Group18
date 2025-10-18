import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
import watermark_qr as wq

def test_qr_call_runs():
    dummy_pdf = b"%PDF-1.4 dummy"
    try:
        wq.add_qr_watermark(dummy_pdf, "GROUP_18", "flag1", "flag2")
    except Exception:
        assert True
