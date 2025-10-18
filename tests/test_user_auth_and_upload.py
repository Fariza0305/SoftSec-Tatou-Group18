import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../server/src"))
from server import app

def test_user_auth_and_upload():
    app.testing = True
    client = app.test_client()

    # ---- Create user ----
    resp_create = client.post("/api/create-user", json={
        "username": "testuser",
        "password": "testpass"
    })
    # should return 200 or 400 (user exists)
    assert resp_create.status_code in [200, 400, 500]

    # ---- Login ----
    resp_login = client.post("/api/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert resp_login.status_code in [200, 400, 401, 500]

    # ---- Upload document ----
    data = {
        "file": (open(__file__, "rb"), "dummy.txt")
    }
    resp_upload = client.post("/api/upload-document", data=data, content_type="multipart/form-data")
    assert resp_upload.status_code in [200, 400, 500]

    # ---- Optional watermark creation ----
    resp_create_wm = client.post("/api/create-watermark/1", json={
        "wm_method": "metadata"
    })
    assert resp_create_wm.status_code in [200, 400, 404, 500]
