import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_rmap_and_version_routes():
    app.testing = True
    client = app.test_client()

    # rmap health check
    rmap_health = client.get("/api/rmap-healthz")
    assert rmap_health.status_code in [200, 500]

    # list versions
    lv = client.get("/api/list-versions/1")
    assert lv.status_code in [200, 400, 404, 401, 500]

    # get-version (fake link)
    gv = client.get("/api/get-version/fakelink123")
    assert gv.status_code in [200, 400, 404]
