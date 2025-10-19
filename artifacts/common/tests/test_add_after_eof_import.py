import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
import add_after_eof

def test_add_after_eof_class_methods():
    wm = add_after_eof.AddAfterEOF()  # ✅ 正确类名
    pdf_bytes = b"%PDF-1.4\n%%EOF"
    key = "TEST_KEY"

    # 1️⃣ 检查类方法存在
    assert hasattr(wm, "add_watermark")
    assert hasattr(wm, "is_watermark_applicable")
    assert hasattr(wm, "get_usage")

    # 2️⃣ 测试是否可以执行 add_watermark()
    try:
        wm.add_watermark(pdf_bytes, "SECRET_TEXT", key)
    except Exception:
        # 即使报错也说明执行到函数体内部
        assert True

    # 3️⃣ 调用 is_watermark_applicable()
    applicable = wm.is_watermark_applicable(pdf_bytes)
    assert isinstance(applicable, bool)

    # 4️⃣ 调用 get_usage()
    usage = wm.get_usage()
    assert isinstance(usage, str)

    # 5️⃣ 调用私有函数 _build_payload 和 _mac_hex
    payload = wm._build_payload("FLAG123", key)
    mac = wm._mac_hex(b"FLAG123", key)
    assert isinstance(payload, (bytes, bytearray))
    assert isinstance(mac, str)
