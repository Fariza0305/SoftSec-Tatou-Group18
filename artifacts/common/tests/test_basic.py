def test_healthz():
    import requests
    resp = requests.get("http://127.0.0.1:5000/healthz")
    assert resp.status_code == 200
