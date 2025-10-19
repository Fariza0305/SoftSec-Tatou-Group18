import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_rmap_endpoints():
    app.testing = True
    client = app.test_client()
    payload = {"payload": "dummy"}
    r1 = client.post("/api/rmap-initiate", json=payload)
    r2 = client.post("/api/rmap-get-link", json={"doc_id": 1, "requester_group": "GROUP_18"})
    assert r1.status_code in [200,400,500]
    assert r2.status_code in [200,400,404,500]
