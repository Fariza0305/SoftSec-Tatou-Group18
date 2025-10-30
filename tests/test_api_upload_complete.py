"""
/api/upload-document 路由测试（精简版）
"""
import pytest
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import server as srv


class MockDBHandler:
    def __init__(self, store):
        self.store = store
        self.lastrowid = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        sql_u = " ".join(sql.split()).upper()
        params = params or ()

        if sql_u.startswith("INSERT INTO DOCUMENTS"):
            self.lastrowid = len(self.store["docs"]) + 1
            self.store["docs"].append({
                "id": self.lastrowid,
                "name": params[0],
                "path": params[1],
                "owner_id": params[2],
                "sha256": params[3] if len(params) > 3 else None,
                "size": params[4] if len(params) > 4 else 0
            })
            return
        
        if sql_u.startswith("UPDATE DOCUMENTS"):
            doc_id = params[1]
            path = params[0]
            for d in self.store["docs"]:
                if d["id"] == doc_id:
                    d["path"] = path
            return

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class FakeConn:
    def __init__(self, store):
        self.store = store

    def get_handler(self):
        return MockDBHandler(self.store)

    def commit(self):
        return None


@pytest.fixture()
def fake_db(monkeypatch, tmp_path):
    store = {"users": [], "docs": [], "versions": []}
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))
    
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(srv, "UPLOAD_DIR", upload_dir)
    
    return store


def create_valid_pdf():
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


class TestUploadDocument:
    """测试文档上传"""
    
    def test_upload_success(self, fake_db):
        """✅ 测试成功上传"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        pdf_content = create_valid_pdf()
        data = {
            'file': (io.BytesIO(pdf_content), 'test.pdf', 'application/pdf')
        }
        
        response = client.post(
            "/api/upload-document",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        resp_data = response.get_json()
        assert "id" in resp_data
        assert resp_data["name"] == "test.pdf"
    
    def test_upload_no_auth(self, fake_db):
        """❌ 测试未认证"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        data = {
            'file': (io.BytesIO(create_valid_pdf()), 'test.pdf')
        }
        
        response = client.post(
            "/api/upload-document",
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 401
    
    def test_upload_no_file(self, fake_db):
        """❌ 测试缺少文件"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        
        response = client.post(
            "/api/upload-document",
            headers={"Authorization": f"Bearer {token}"},
            data={},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
