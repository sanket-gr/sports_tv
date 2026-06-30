import pytest
import os
test_db_path = "./test_sports_tv.db"
if os.path.exists(test_db_path):
    os.remove(test_db_path)
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from fastapi.testclient import TestClient
from database import create_tables
from main import app

# Create tables for tests
create_tables()

def test_read_admin():
    # If no credentials are set in environment, /admin should be accessible
    if "ADMIN_USERNAME" in os.environ:
        del os.environ["ADMIN_USERNAME"]
    if "ADMIN_PASSWORD" in os.environ:
        del os.environ["ADMIN_PASSWORD"]
        
    with TestClient(app) as client:
        response = client.get("/admin")
        assert response.status_code == 200

def test_admin_auth():
    # Enable authentication
    os.environ["ADMIN_USERNAME"] = "testuser"
    os.environ["ADMIN_PASSWORD"] = "testpass"
    
    try:
        with TestClient(app) as client:
            # Unauthenticated request -> should fail with 401
            response = client.get("/admin")
            assert response.status_code == 401
            
            # Correct credentials -> should succeed with 200
            response = client.get("/admin", auth=("testuser", "testpass"))
            assert response.status_code == 200
            
            # Incorrect credentials -> should fail with 401
            response = client.get("/admin", auth=("testuser", "wrongpass"))
            assert response.status_code == 401
    finally:
        # Cleanup
        del os.environ["ADMIN_USERNAME"]
        del os.environ["ADMIN_PASSWORD"]

def test_api_categories():
    with TestClient(app) as client:
        response = client.get("/api/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_proxy_ssrf_mitigation():
    with TestClient(app) as client:
        # 1. Private IP block (RFC 1918, loopback)
        response = client.get("/api/proxy?url=http://127.0.0.1:8000/admin")
        assert response.status_code == 403
        assert "Private IP" in response.text
        
        response = client.get("/api/proxy?url=http://192.168.1.50/stream.m3u8")
        assert response.status_code == 403
        assert "Private IP" in response.text

        # 2. Unwhitelisted domain block
        response = client.get("/api/proxy?url=https://untrusteddomain.com/stream.m3u8")
        assert response.status_code == 403
        assert "whitelisted" in response.text

        # 3. Whitelisted domain (should pass SSRF check, even if it fails with 502/etc. from actual connection)
        response = client.get("/api/proxy?url=https://sportsurge.ws/manifest.m3u8")
        assert response.status_code in (200, 502)


def test_read_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Sports TV" in response.text


def test_api_version():
    with TestClient(app) as client:
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version_code"] == 2
        assert "apk_url" in data
        assert "tv.apk" in data["apk_url"]


def test_bulk_delete():
    with TestClient(app) as client:
        # 1. Get categories to find a valid category_id
        response = client.get("/api/categories")
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) > 0
        cat_id = categories[0]["id"]
        
        # 2. Add two manual streams
        resp1 = client.post("/admin/streams", data={
            "category_id": cat_id,
            "title": "Stream to delete 1",
            "hls_url": "https://example.com/stream1.m3u8"
        }, follow_redirects=False)
        assert resp1.status_code == 303
        
        resp2 = client.post("/admin/streams", data={
            "category_id": cat_id,
            "title": "Stream to delete 2",
            "hls_url": "https://example.com/stream2.m3u8"
        }, follow_redirects=False)
        assert resp2.status_code == 303
        
        # Get active streams to find their IDs
        resp_streams = client.get("/api/streams?live_only=false")
        assert resp_streams.status_code == 200
        streams = resp_streams.json()
        
        # Find the IDs of the streams we just added
        stream1 = next(s for s in streams if s["title"] == "Stream to delete 1")
        stream2 = next(s for s in streams if s["title"] == "Stream to delete 2")
        id1 = stream1["id"]
        id2 = stream2["id"]
        
        # 3. Call bulk delete
        resp_delete = client.post("/admin/streams/bulk-delete", data={
            "stream_ids": [str(id1), str(id2)]
        }, follow_redirects=False)
        assert resp_delete.status_code == 303
        
        # 4. Verify they are deleted
        resp_streams_after = client.get("/api/streams?live_only=false")
        assert resp_streams_after.status_code == 200
        streams_after = resp_streams_after.json()
        assert not any(s["id"] == id1 for s in streams_after)
        assert not any(s["id"] == id2 for s in streams_after)


@pytest.mark.anyio
async def test_cdnlivetv_scraper():
    mock_html = """
    <html>
    <head>
    <title>TSN 1 CA</title>
    </head>
    <body>
    <script>
    function GtlpmtvgfT(s){s=s.replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';try{return atob(s)}catch(e){}};
    var kxykkJHw='aHR0cHM';
    var PjGdhEkJ='Og';
    var LmIaOhFd='Ly8';
    var ktLhxjEY='Y2RubGl2ZXR2';
    var aGDrpQMu='LnR2';
    var iNwPOSvx='L3NlY3VyZS9hcGkvdjEv';
    var gwaLSzdJ='NmEyODhkMmE4MWQ4MTkyYmI3NmNjMTcy';
    var TGeIiwCb='L3BsYXlsaXN0';
    var ATkeXEmr='Lm0zdTg';
    var VSQScTBR='P3Rva2VuPU5tRXl';
    var JXodLzMRVoOI=GtlpmtvgfT(kxykkJHw)+GtlpmtvgfT(PjGdhEkJ)+GtlpmtvgfT(LmIaOhFd)+GtlpmtvgfT(ktLhxjEY)+GtlpmtvgfT(aGDrpQMu)+GtlpmtvgfT(iNwPOSvx)+GtlpmtvgfT(gwaLSzdJ)+GtlpmtvgfT(TGeIiwCb)+GtlpmtvgfT(ATkeXEmr)+GtlpmtvgfT(VSQScTBR);
    </script>
    </body>
    </html>
    """
    from scrapers.cdnlivetv import CdnLiveTvScraper
    import unittest.mock
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            text = mock_html
            status_code = 200
        return MockResponse()
        
    scraper = CdnLiveTvScraper()
    with unittest.mock.patch('httpx.AsyncClient.get', new=mock_get):
        res = await scraper.extract("https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%201")
        assert res["hls_url"].startswith("https://cdnlivetv.tv/secure/api/v1/6a288d2a81d8192bb76cc172/playlist.m3u8?token=NmEy")
        assert res["title"] == "TSN 1 CA"



