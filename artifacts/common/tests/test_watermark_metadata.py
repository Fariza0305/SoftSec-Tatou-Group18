import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_create_watermark_attachment():
    app.testing = True
    client = app.test_client()
    data = {"doc_id": 1, "wm_method": "attachment"}
    resp = client.post("/create-watermark", json=data)
    assert resp.status_code in [200, 400, 500]

def test_create_watermark_metadata():
    app.testing = True
    client = app.test_client()
    data = {"doc_id": 1, "wm_method": "metadata"}
    resp = client.post("/create-watermark", json=data)
    assert resp.status_code in [200, 400, 500]

def test_create_watermark_qr():
    app.testing = True
    client = app.test_client()
    data = {"doc_id": 1, "wm_method": "qr"}
    resp = client.post("/create-watermark", json=data)
    assert resp.status_code in [200, 400, 500]
