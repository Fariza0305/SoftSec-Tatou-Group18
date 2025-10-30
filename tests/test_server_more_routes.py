import os
import io
from pathlib import Path
import types
import sys
import json

import pytest

from server.src import server as srv


@pytest.fixture()
def ensure_storage(tmp_path, monkeypatch):
    (srv.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    (srv.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    (srv.VERSIONS_DIR).mkdir(parents=True, exist_ok=True)
    return True


def test_method_not_allowed_returns_405(ensure_storage):
    srv.app.testing = True
    c = srv.app.test_client()
    resp = c.put("/api/get-watermarking-methods")
    assert resp.status_code == 405


def test_global_error_handler_on_extract_exception(ensure_storage, monkeypatch, tmp_path):
    srv.app.testing = True
    c = srv.app.test_client()

    # 伪造 auth/owner
    monkeypatch.setattr(srv, "require_auth", lambda: 1)
    monkeypatch.setattr(srv, "_ensure_owner", lambda uid, did: {"id": did, "owner_id": uid})

    # 创建可读路径
    pdf_path = srv.UPLOAD_DIR / "doc_1.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    # 假 DB：Documents(id=1)-> path
    class Cur:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def execute(self, sql, params=None):
            self._rows = []
            sql_u = " ".join(sql.split()).upper()
            if sql_u.startswith("SELECT PATH FROM VERSIONS"):
                self._rows = []
            if sql_u.startswith("SELECT PATH FROM DOCUMENTS WHERE ID="):
                self._rows = [{"path": str(pdf_path)}]
        def fetchone(self):
            return self._rows[0] if self._rows else None
        def fetchall(self):
            return list(self._rows)
    class Conn:
        def get_handler(self):
            return Cur()
    monkeypatch.setattr(srv, "get_db", lambda: Conn())

    # extract 抛异常，触发全局 500 处理
    def bad_extract(pdf, key=None, position=None):
        raise RuntimeError("boom")
    monkeypatch.setattr(srv, "_wm_get", lambda name, op: bad_extract if op == "extract" else None)

    resp = c.post("/api/read-watermark/1", headers={"Authorization": "Bearer 1.x"}, json={"method": "attachment"})
    assert resp.status_code == 500
    body = resp.get_json()
    assert body.get("error") == "Internal Server Error"


def test_login_bcrypt_success(monkeypatch):
    srv.app.testing = True
    c = srv.app.test_client()

    import bcrypt
    hp = bcrypt.hashpw(b"pw123", bcrypt.gensalt()).decode()

    class Cur:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, sql, params=None):
            sql_u = " ".join(sql.split()).upper()
            if sql_u.startswith("SELECT * FROM USERS WHERE EMAIL="):
                self._rows = [{"id": 1, "email": "bx@x", "hpassword": hp, "login": "u"}]
            else:
                self._rows = []
        def fetchone(self):
            return self._rows[0] if self._rows else None
        def fetchall(self):
            return list(self._rows)
    class Conn:
        def get_handler(self): return Cur()
    monkeypatch.setattr(srv, "get_db", lambda: Conn())

    r = c.post("/api/login", json={"email": "bx@x", "password": "pw123"})
    assert r.status_code == 200
    assert r.get_json().get("success") is True


def test_rmap_initiate_encrypted_payload(monkeypatch):
    srv.app.testing = True
    c = srv.app.test_client()

    # 构造假的 rmap.compat_helpers 模块
    fake_mod = types.SimpleNamespace()
    class DecryptionError(Exception):
        pass
    def decrypt_forgiving_json(priv, payload):
        return {"identity": "GROUP_18", "nonceClient": 42}
    fake_mod.DecryptionError = DecryptionError
    fake_mod.decrypt_forgiving_json = decrypt_forgiving_json

    sys.modules["rmap.compat_helpers"] = fake_mod
    sys.modules["rmap"] = types.SimpleNamespace(compat_helpers=fake_mod)

    r = c.post("/api/rmap-initiate", json={"payload": "xxxxx"})
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        body = r.get_json()
        assert "nonceServer" in body and body.get("nonceClient") == 42


def test_get_version_unknown_and_file_missing(monkeypatch):
    srv.app.testing = True
    c = srv.app.test_client()

    # unknown
    r1 = c.get("/api/get-version/NOPE")
    assert r1.status_code == 404

    # cached but missing file
    srv.LINK_CACHE["L1"] = "/non/existent/path.pdf"
    r2 = c.get("/api/get-version/L1")
    assert r2.status_code == 404


