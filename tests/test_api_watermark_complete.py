"""
/api/create-watermark 和 /api/read-watermark 路由测试（精简版 - 真实水印）
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import server as srv


def create_minimal_pdf():
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
xref
0 3
trailer
<< /Root 1 0 R >>
%%EOF"""


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

        if "SELECT * FROM DOCUMENTS WHERE ID=" in sql_u and "AND OWNER_ID=" in sql_u:
            doc_id, owner_id = params[0], params[1]
            row = next((d for d in self.store["docs"] if d["id"] == doc_id and d["owner_id"] == owner_id), None)
            self._rows = [row] if row else []
            return
        
        if sql_u.startswith("INSERT INTO VERSIONS"):
            self.lastrowid = len(self.store["versions"]) + 1
            self.store["versions"].append({
                "id": self.lastrowid,
                "link": params[0] if len(params) > 0 else "",
                "method": params[3] if len(params) > 3 else "",
                "doc_id": params[6] if len(params) > 6 else 0,
            })
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
def fake_db_with_doc(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    versions_dir = tmp_path / "versions"
    upload_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = upload_dir / "doc_1.pdf"
    pdf_path.write_bytes(create_minimal_pdf())
    
    store = {
        "users": [{"id": 1, "login": "testuser", "email": "test@example.com"}],
        "docs": [{
            "id": 1,
            "name": "test.pdf",
            "path": str(pdf_path),
            "owner_id": 1
        }],
        "versions": []
    }
    
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))
    monkeypatch.setattr(srv, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(srv, "VERSIONS_DIR", versions_dir)
    srv._load_watermark_modules()
    
    return store


class TestCreateWatermark:
    """测试创建水印（真实功能）"""
    
    def test_create_watermark_attachment(self, fake_db_with_doc):
        """✅ 测试attachment水印"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.post(
            "/api/create-watermark/1",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "wm_method": "attachment",
                "params": {"secret": "TEST_SECRET", "key": "TEST_KEY"}
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "link" in data
    
    def test_create_watermark_metadata(self, fake_db_with_doc):
        """✅ 测试metadata水印"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.post(
            "/api/create-watermark/1",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "wm_method": "metadata",
                "params": {"secret": "META_SECRET"}
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["method"] == "metadata"
    
    def test_create_watermark_invalid_method(self, fake_db_with_doc):
        """❌ 测试无效方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.post(
            "/api/create-watermark/1",
            headers={"Authorization": f"Bearer {token}"},
            json={"wm_method": "invalid_method"}
        )
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
