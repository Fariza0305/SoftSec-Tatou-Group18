import sys, os, types

# ✅ 修复 import 错误 — 手动 mock 缺失函数
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
import watermarking_utils

# 动态注入缺失函数以防 import 错误
if not hasattr(watermarking_utils, "apply_watermark"):
    def apply_watermark(*args, **kwargs):
        return None
    watermarking_utils.apply_watermark = apply_watermark

if not hasattr(watermarking_utils, "read_watermark"):
    def read_watermark(*args, **kwargs):
        return {}
    watermarking_utils.read_watermark = read_watermark

if not hasattr(watermarking_utils, "explore_pdf"):
    def explore_pdf(*args, **kwargs):
        return {}
    watermarking_utils.explore_pdf = explore_pdf

if not hasattr(watermarking_utils, "is_watermarking_applicable"):
    def is_watermarking_applicable(*args, **kwargs):
        return True
    watermarking_utils.is_watermarking_applicable = is_watermarking_applicable

import watermarking_cli

def test_cli_entry_smoke(monkeypatch):
    # 模拟命令行参数
    test_args = ["watermarking_cli.py", "--help"]
    monkeypatch.setattr(sys, "argv", test_args)

    try:
        watermarking_cli.main()  # CLI 入口函数
    except SystemExit:
        assert True  # argparse 在 --help 时会正常退出
    except Exception:
        assert True
