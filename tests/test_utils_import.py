import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
import watermarking_utils

def test_utils_imports_ok():
    assert hasattr(watermarking_utils, "__name__")
