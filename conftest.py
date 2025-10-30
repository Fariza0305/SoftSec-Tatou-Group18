import sys
import types


# Provide a minimal stub for imghdr to satisfy pgpy on Python 3.13+
if "imghdr" not in sys.modules:
    im = types.ModuleType("imghdr")

    def what(file, h=None):  # pragma: no cover
        return None

    im.what = what
    sys.modules["imghdr"] = im

# conftest.py
import sys, os
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
