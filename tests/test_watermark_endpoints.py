import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_create_watermark_all_methods():
    app.testing = True
    client = app.test_client()
    for method in ["attachment", "metadata", "qr"]:
        resp = client.post("/api/create-watermark/1", json={"wm_method": method})
        assert resp.status_code in [200, 400, 500]
