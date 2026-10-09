import io, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from fastapi.testclient import TestClient
from PIL import Image
import main
c = TestClient(main.app)

def png():
    b = io.BytesIO(); Image.new("RGB", (32, 32), "red").save(b, "PNG"); return b.getvalue()

def test_health(): assert c.get("/health").json()["status"] == "ok"
def test_empty_rejected(): assert c.post("/analyze", data={"text": ""}).status_code == 400
def test_bad_extension(): assert c.post("/analyze", files=[("files", ("x.exe", b"MZ", "application/octet-stream"))]).status_code == 400
def test_magic_mismatch(): assert c.post("/analyze", files=[("files", ("x.png", b"not an image", "image/png"))]).status_code == 400
def test_flow_review_delete_pdf():
    r = c.post("/analyze", data={"text": "hello there friend"}, files=[("files", ("a.png", png(), "image/png"))]).json()
    assert r["prediction"] in ("REAL", "FAKE", "UNCERTAIN") and "contributions" in r
    i = r["id"]
    assert c.post(f"/analysis/{i}/review", json={"verdict": "FAKE", "notes": "n"}).status_code == 200
    assert c.get(f"/analysis/{i}/report.pdf").headers["content-type"] == "application/pdf"
    assert any(x["id"] == i for x in c.get("/history?limit=5").json())
    assert c.delete(f"/analysis/{i}").status_code == 200 and c.get(f"/analysis/{i}").status_code == 404
def test_fuse_missing_scores(): assert main.fuse({"image": None})[0] == "UNCERTAIN"

import time
def test_job_flow_and_progress():
    jid = c.post("/jobs", data={"text": "a simple sentence about the weather today"}).json()["job_id"]
    for _ in range(100):
        j = c.get(f"/jobs/{jid}").json()
        if j["status"] != "running": break
        time.sleep(.1)
    assert j["status"] == "done" and c.get(f"/analysis/{j['analysis_id']}").status_code == 200
def test_job_rejects_empty(): assert c.post("/jobs", data={"text": ""}).status_code == 400
def test_unknown_job(): assert c.get("/jobs/nope").status_code == 404
def test_retention_purge():
    r = c.post("/analyze", data={"text": "old sample sentence here"}).json()
    main.db.execute("update analyses set ts=? where id=?", (time.time() - 90 * 86400, r["id"])); main.db.commit(); main.purge()
    assert c.get(f"/analysis/{r['id']}").status_code == 404
def test_face_crop_none_on_blank():
    import models
    try: assert models.face_crop(Image.new("RGB", (200, 200), "white")) is None
    except ImportError: pass
