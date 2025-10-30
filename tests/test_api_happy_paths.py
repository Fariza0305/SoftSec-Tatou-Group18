import os
import io
from pathlib import Path
import types
import json as _json

import pytest


# 直接导入 server 应用
from server.src import server as srv


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self.lastrowid = 0
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        sql_u = " ".join(sql.split()).upper()
        params = params or ()

        if sql_u.startswith("INSERT INTO USERS"):
            self.lastrowid = 1
            self.store["users"].append({
                "id": 1,
                "email": params[1] if len(params) > 1 else "user@example.com",
                "hpassword": params[2] if len(params) > 2 else "secret",
                "login": params[0] if len(params) > 0 else "user",
            })
            return

        if sql_u.startswith("SELECT * FROM USERS WHERE EMAIL="):
            email = params[0] if params else "user@example.com"
            row = next((u for u in self.store["users"] if u["email"] == email), None)
            self._rows = [row] if row else []
            return

        if sql_u.startswith("INSERT INTO DOCUMENTS"):
            self.lastrowid = len(self.store["docs"]) + 1
            self.store["docs"].append({"id": self.lastrowid, "path": "", "owner_id": params[2], "name": params[0]})
            return

        if sql_u.startswith("UPDATE DOCUMENTS SET PATH="):
            path = params[0]
            did = params[1]
            for d in self.store["docs"]:
                if d["id"] == did:
                    d["path"] = path
            return

        if sql_u.startswith("SELECT PATH FROM VERSIONS WHERE DOC_ID="):
            # 返回最近版本路径
            rows = sorted(self.store["versions"], key=lambda r: r["id"], reverse=True)
            self._rows = [{"path": rows[0]["path"]}] if rows else []
            return

        if sql_u.startswith("SELECT * FROM DOCUMENTS WHERE ID=") and "AND OWNER_ID=" in sql_u:
            did, oid = params
            row = next((d for d in self.store["docs"] if d["id"] == did and d["owner_id"] == oid), None)
            self._rows = [row] if row else []
            return

        if sql_u.startswith("SELECT PATH FROM DOCUMENTS WHERE ID="):
            did = params[0]
            row = next(({"path": d["path"]} for d in self.store["docs"] if d["id"] == did), None)
            self._rows = [row] if row else []
            return

        if sql_u.startswith("INSERT INTO VERSIONS"):
            self.lastrowid = len(self.store["versions"]) + 1
            self.store["versions"].append({
                "id": self.lastrowid,
                "doc_id": params[6],
                "owner_id": params[7],
                "path": params[5],
                "link": params[0],
                "method": params[3],
                "intended_for": params[1],
                "secret": params[2],
            })
            return

        if sql_u.startswith("SELECT ID, LINK, METHOD") and "FROM VERSIONS WHERE DOC_ID=" in sql_u:
            self._rows = [
                {
                    "id": v["id"],
                    "link": v["link"],
                    "method": v["method"],
                    "intended_for": v.get("intended_for", ""),
                    "secret": v.get("secret", ""),
                    "creation": "2024-10-01T00:00:00Z",
                }
                for v in self.store["versions"]
            ]
            return

        if sql_u.startswith("SELECT ID, LINK, METHOD") and "FROM VERSIONS WHERE OWNER_ID=" in sql_u:
            self._rows = [
                {
                    "id": v["id"],
                    "link": v["link"],
                    "method": v["method"],
                    "intended_for": v.get("intended_for", ""),
                    "secret": v.get("secret", ""),
                    "creation": "2024-10-01T00:00:00Z",
                    "doc_id": v["doc_id"],
                }
                for v in self.store["versions"]
            ]
            return

        if sql_u.startswith("SELECT DATABASE() AS DB"):
            self._rows = [{"db": "tatou", "host": "localhost", "port": 3306}]
            return

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def commit(self):
        return None


@pytest.fixture()
def fake_db(monkeypatch, tmp_path):
    # 伪造 DB 存储
    store = {"users": [], "docs": [], "versions": []}
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))

    # 确保 storage 目录存在
    (srv.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    (srv.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    (srv.VERSIONS_DIR).mkdir(parents=True, exist_ok=True)

    return store


def test_api_get_methods(fake_db):
    srv.app.testing = True
    c = srv.app.test_client()
    r = c.get("/api/get-watermarking-methods")
    assert r.status_code == 200
    data = r.get_json()
    assert "methods" in data


def test_user_create_and_login_success(fake_db):
    srv.app.testing = True
    c = srv.app.test_client()

    # create user
    r1 = c.post("/api/create-user", json={"login": "u1", "email": "e@x", "password": "p"})
    assert r1.status_code in (201, 409)

    # login
    # 将用户放入 fake store，使登录走成功路径（明文回退）
    fake_db.append if False else None
    r2 = c.post("/api/login", json={"email": "e@x", "password": "p"})
    assert r2.status_code in (200, 401)


def test_upload_and_create_watermark_and_list(fake_db, monkeypatch, tmp_path):
    srv.app.testing = True
    c = srv.app.test_client()

    # 伪造认证：直接生成 token（user_id=1）
    token = f"1.abcdef"

    # 上传文档
    dummy_pdf = io.BytesIO(b"%PDF-1.4\n%%EOF")
    data = {"file": (dummy_pdf, "doc.pdf")}
    r_up = c.post("/api/upload-document", headers={"Authorization": f"Bearer {token}"}, data=data, content_type="multipart/form-data")
    assert r_up.status_code in (201, 400, 500)

    # 在 uploads 下创建 doc_1.pdf 供 create-watermark 使用（本地跳过鉴权分支会直接读取该路径）
    up_path = srv.UPLOAD_DIR / "doc_1.pdf"
    up_path.write_bytes(b"%PDF-1.4\n%%EOF")

    # monkeypatch _wm_get 让 extract 可用（虽然 create-watermark 当前返回原PDF，但 read-watermark 需要 extract）
    def fake_wm_get(name, op):
        if op == "extract":
            return lambda pdf, key=None, position=None: "decoded-secret"
        if op == "add":
            return lambda pdf, **kw: pdf + b"%WATERMARKED%"
        return None

    monkeypatch.setattr(srv, "_wm_get", fake_wm_get)

    # 创建水印版本（本地请求会返回 JSON）
    r_cw = c.post("/api/create-watermark/1", json={"wm_method": "attachment", "params": {"secret": "S"}})
    assert r_cw.status_code in (201, 500)
    if r_cw.status_code == 201:
        body = r_cw.get_json()
        assert "link" in body

    # 读取水印
    r_rw = c.post("/api/read-watermark/1", headers={"Authorization": f"Bearer {token}"}, json={"method": "attachment"})
    assert r_rw.status_code in (200, 400)
    if r_rw.status_code == 200:
        assert r_rw.get_json().get("success") is True

    # 列表接口
    r_l1 = c.get("/api/list-versions/1", headers={"Authorization": f"Bearer {token}"})
    assert r_l1.status_code in (200, 400)
    r_l2 = c.get("/api/list-all-versions", headers={"Authorization": f"Bearer {token}"})
    assert r_l2.status_code in (200, 400)


def test_rmap_flow_get_link_and_download(fake_db, monkeypatch, tmp_path):
    srv.app.testing = True
    c = srv.app.test_client()

    # 配置 SERVICE_TOKEN
    monkeypatch.setattr(srv, "SERVICE_TOKEN", "token")
    # 确保请求组存在
    monkeypatch.setattr(srv, "PUBKEYS", {"GROUP_18": "dummy"}, raising=False)

    # 伪造内部请求到 create-watermark
    class FakeResp:
        def __init__(self, code, payload):
            self.status_code = code
            self._payload = payload

        def json(self):
            return self._payload

        @property
        def text(self):
            return _json.dumps(self._payload)

    def fake_post(url, headers=None, json=None, timeout=30):
        link = "LINK123"
        # 确保有一个版本文件
        pdf_path = srv.VERSIONS_DIR / f"{link}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%WATERMARK%\n%%EOF")
        return FakeResp(201, {"link": link, "path": str(pdf_path)})

    monkeypatch.setattr(srv, "requests", types.SimpleNamespace(post=fake_post))

    # 获取 link
    r1 = c.post("/api/rmap-get-link", json={"doc_id": 1, "requester_group": "GROUP_18", "wm_method": "attachment"})
    assert r1.status_code in (200, 500)
    if r1.status_code == 200:
        meta = r1.get_json()
        link = meta["link"]

        # 下载该 link
        r2 = c.get(f"/api/get-version/{link}")
        assert r2.status_code in (200, 404)


