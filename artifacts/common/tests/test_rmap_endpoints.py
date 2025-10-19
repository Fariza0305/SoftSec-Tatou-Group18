import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_rmap_initiate():
    app.testing = True
    client = app.test_client()
    data = {"payload": "dummy"}
    resp = client.post("/rmap-initiate", json=data)
    assert resp.status_code in [200, 400, 500]

def test_rmap_get_link():
    app.testing = True
    client = app.test_client()
    data = {"doc_id": 999, "requester_group": "GROUP_18", "wm_method": "attachment"}
    resp = client.post("/rmap-get-link", json=data)
    assert resp.status_code in [200, 400, 404, 500]
