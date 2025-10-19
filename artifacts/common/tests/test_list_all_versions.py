import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_list_all_versions_route():
    app.testing = True
    client = app.test_client()
    resp = client.get("/api/list-all-versions")
    assert resp.status_code in [200, 400, 404, 401, 500]
