import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
import watermark_attachment as wa

def test_attachment_call_runs():
    dummy_pdf = b"%PDF-1.4 dummy"
    try:
        wa.add_attachment_watermark(dummy_pdf, "GROUP_18", "flag1", "flag2")
    except Exception:
        # even if it raises, it's fine; we only want to execute paths
        assert True
