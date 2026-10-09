"""VeriLens AI backend. Each engine is an adapter returning score (P(fake) or None) + evidence; swap in trained models there."""
import asyncio, os, re, io, json, time, uuid, base64, sqlite3, logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageChops
from dotenv import load_dotenv
load_dotenv()
import models

class _J(logging.Formatter):
    def format(self, r): return json.dumps({"ts": self.formatTime(r), "level": r.levelname, "logger": r.name, "msg": r.getMessage()})
_h = logging.StreamHandler(); _h.setFormatter(_J()); logging.basicConfig(level=logging.INFO, handlers=[_h])
log = logging.getLogger("verilens")
MODEL_VERSION = "hf-ensemble-1.0"
MAX = int(os.getenv("MAX_UPLOAD_MB", 25)) * 1024 * 1024
EXT = {"image": {"jpg", "jpeg", "png", "webp"}, "audio": {"mp3", "wav", "m4a"}, "video": {"mp4", "mov", "webm"}}
DATA = Path(__file__).parent / "data"
db = sqlite3.connect(os.getenv("DB_PATH", "verilens.db"), check_same_thread=False)
db.execute("create table if not exists analyses(id text primary key, ts real, verdict text, conf real, ms int, result text, review text)")
app = FastAPI(title="VeriLens AI")
if os.getenv("PRELOAD_MODELS") == "1":
    @app.on_event("startup")
    def _pre():
        for f in (lambda: models.image_score(Image.new("RGB", (64, 64)))):
            try: f()
            except Exception as e: log.error("preload: %s", e)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])
HITS = {}

@app.middleware("http")
async def limiter(req: Request, call_next):  # per-IP limit: 60 req/min
    k, now = (req.client.host if req.client else "x"), time.time()
    HITS[k] = [t for t in HITS.get(k, []) if now - t < 60] + [now]
    if len(HITS[k]) > 60: return JSONResponse({"detail": "Rate limit exceeded"}, 429)
    return await call_next(req)

CUES = ["breaking", "shocking", "you wont believe", "secret", "exposed", "leaked", "banned", "100%", "miracle", "they dont want", "share before", "sovereign", "conspiracy", "hoax"]

def text_engine(t):
    low, spans = t.lower().replace("\u0027", ""), []
    for c in CUES:
        for m in re.finditer(re.escape(c), low): spans.append({"start": m.start(), "end": m.end(), "label": "suspicious wording", "text": t[m.start():m.end()]})
    ents = sorted(set(re.findall(r"\b[A-Z][a-z]{2,}(?:\s[A-Z][a-z]+)*\b", t)))[:12]
    caps = sum(1 for w in t.split() if len(w) > 3 and w.isupper()) + t.count("!")
    score = min(0.95, 0.25 + 0.15 * len(spans) + 0.05 * caps)
    ev = [{"type": "suspicious_language", "severity": "high" if len(spans) > 1 else "medium", "description": f"{len(spans)} sensational/unsupported phrases found."}] if spans else []
    return {"score": round(score, 3), "entities": ents, "highlights": spans, "claims": [s.strip() for s in re.split(r"[.!?]", t) if len(s.split()) > 5][:5], "evidence": ev}

def image_engine(b):  # Error Level Analysis
    im = Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((768, 768))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    ela = ImageChops.difference(im, Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
    ext = max(ch.getextrema()[1] for ch in ela.split()) or 1
    heat = ela.point(lambda p: min(255, int(p * (255 / ext))))
    out = io.BytesIO(); heat.save(out, "PNG")
    px = list(ela.convert("L").getdata()); mean = sum(px) / len(px)
    score = max(0.05, min(0.95, 0.2 + mean / 12))
    ev = [{"type": "visual_artifact", "severity": "high" if score > .65 else "medium", "description": f"ELA residual mean {mean:.2f}; uneven compression can indicate edits."}] if score > .45 else []
    return {"score": round(score, 3), "heatmap": "data:image/png;base64," + base64.b64encode(out.getvalue()).decode(), "evidence": ev}

def adapter_missing(kind):  # plug Whisper / wav2vec2 / video model here
    return {"score": None, "evidence": [], "note": f"No {kind} model configured; modality received but not scored."}

def learned():
    p = DATA / "fusion.json"; return json.loads(p.read_text()) if p.exists() else None

def fuse(scores):
    import math
    v = [x for x in scores.values() if x is not None]
    if not v: return "UNCERTAIN", 1.0, {"REAL": 0, "FAKE": 0, "UNCERTAIN": 1}
    L, spread = learned(), max(v) - min(v)
    if L:  # learned stacking fusion + validation-tuned abstention band
        z = L["intercept"] + sum(L["coef"][2 * i] * (scores.get(m) or 0) + L["coef"][2 * i + 1] * (scores.get(m) is not None) for i, m in enumerate(L["features"]))
        p = 1 / (1 + math.exp(-z)); unc = max(0.0, 1 - abs(2 * p - 1) / max(2 * L["band"], 1e-6)) if L["band"] > 0 else 0.0
        unc = min(1, max(unc, spread * .5))
    else:
        p = sum(v) / len(v); unc = min(1, (1 - abs(2 * p - 1)) * .6 + spread * .8 + (.15 if len(v) < 2 else 0))
    probs = {"FAKE": p * (1 - unc), "REAL": (1 - p) * (1 - unc), "UNCERTAIN": unc}
    t = sum(probs.values()); probs = {k: round(x / t, 3) for k, x in probs.items()}
    top = max(probs, key=probs.get); return top, probs[top], probs

MAGIC = {"jpg": [b"\xff\xd8"], "jpeg": [b"\xff\xd8"], "png": [b"\x89PNG"], "webp": [b"RIFF"], "wav": [b"RIFF"], "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
         "m4a": [b"ftyp"], "mp4": [b"ftyp"], "mov": [b"ftyp", b"moov", b"wide", b"free"], "webm": [b"\x1a\x45\xdf\xa3"]}
def sniff_ok(ext, d): return any(d[:len(m)] == m or d[4:4 + len(m)] == m for m in MAGIC[ext]) if ext in MAGIC else False

def run(text, files, progress=lambda s: None):
    t0, scores, mods, ev, detail, notes = time.time(), {}, [], [], {}, []
    img_bytes, transcript = None, ""
    def fail(kind, e): scores[kind] = None; detail.setdefault(kind, {})["note"] = str(e); log.warning("%s: %s", kind, e)
    if text and text.strip():
        mods.append("text"); progress("Analyzing text")
        try:
            r = models.text_analysis(text); spans = []
            for p in r["phrases"]:
                for m in re.finditer(re.escape(p), text): spans.append({"start": m.start(), "end": m.end(), "text": p})
            scores["text"] = round(r["score"], 3); detail["text"] = {"entities": r["entities"], "claims": r["claims"], "highlights": spans, "engine": "gemini", "rationale": r["rationale"]}
            if r["score"] > .5: ev.append({"type": "suspicious_language", "severity": "high" if r["score"] > .75 else "medium", "description": r["rationale"] or "Text assessed as likely false or manipulative."})
        except Exception as e:  # honest fallback to the heuristic baseline, labelled as such
            r = text_engine(text); scores["text"] = r["score"]; ev += r["evidence"]
            detail["text"] = {k: v for k, v in r.items() if k != "evidence"} | {"engine": "heuristic-fallback", "note": f"LLM unavailable ({e})"}
    for f in files:
        ext = f["name"].rsplit(".", 1)[-1].lower()
        kind = next((k for k, e in EXT.items() if ext in e), None)
        if not kind: raise HTTPException(400, f"Unsupported file type: .{ext}")
        if len(f["data"]) > MAX: raise HTTPException(413, "File too large")
        if not sniff_ok(ext, f["data"]): raise HTTPException(400, f"File content does not match .{ext}")
        mods.append(kind); progress(f"Analyzing {kind}")
        try:
            if kind == "image":
                try: ela = image_engine(f["data"])
                except Exception: raise HTTPException(400, "Invalid image file")
                img_bytes = f["data"]; detail["image"] = {"heatmap": ela["heatmap"], "heatmap_kind": "ELA (compression residual, not model attribution)"}
                s_, face = models.image_analysis(Image.open(io.BytesIO(f["data"]))); scores["image"] = round(s_, 3); detail["image"]["face_detected"] = face
                if scores["image"] > .5: ev.append({"type": "visual_artifact", "severity": "high" if scores["image"] > .75 else "medium", "description": f"Image classifier ({models.IMG_MODEL}) rates P(fake)={scores['image']:.0%}."})
            else:
                with models.tmpfile(f["data"], "." + ext) as p:
                    tl = []
                    if kind == "audio": s, tl = models.audio_score(p); wav = p
                    else:
                        s, vtl = models.video_score(p); detail["video"] = {"timeline": vtl}
                        wav = models.video_audio(p)
                        if wav:
                            try: a, atl = models.audio_score(wav); scores["audio"] = round(a, 3); detail["audio"] = {"timeline": atl}; mods.append("audio")
                            except Exception as e: fail("audio", e)
                    scores[kind] = round(s, 3)
                    if kind == "audio": detail["audio"] = {"timeline": tl}
                    sus = [x for x in (tl or detail.get("video", {}).get("timeline", [])) if x["score"] > .7]
                    if scores[kind] > .5: ev.append({"type": "synthetic_speech" if kind == "audio" else "video_manipulation", "severity": "high" if scores[kind] > .75 else "medium", "description": f"{kind.title()} model rates P(fake)={scores[kind]:.0%}; {len(sus)} suspicious segment(s)."})
                    try:
                        if kind == "audio" or wav: transcript = models.transcribe(wav if kind == "video" else p); detail.setdefault("audio", {})["transcript"] = transcript
                    except Exception as e: detail.setdefault("audio", {})["note"] = f"Transcription unavailable: {e}"
                    if wav and wav != p and os.path.exists(wav): os.unlink(wav)
        except HTTPException: raise
        except Exception as e: fail(kind, e)
    if not mods: raise HTTPException(400, "Provide text or at least one file")
    cons = None; progress("Checking cross-modal consistency")
    try:
        cons = models.consistency(text if text.strip() else "", img_bytes, transcript)
        if cons:
            vals = [v for k, v in cons.items() if k != "contradictions" and isinstance(v, (int, float))]
            if vals: scores["cross_modal"] = round(1 - sum(vals) / len(vals), 3)
            for c in cons.get("contradictions", []): ev.append({"type": "semantic_mismatch", "severity": "high", "description": c})
    except Exception as e: notes.append(f"Cross-modal check unavailable: {e}")
    sc = {k: v for k, v in scores.items() if v is not None}
    progress("Fusing evidence")
    verdict, conf, probs = fuse(scores)
    if len(sc) > 1 and max(sc.values()) - min(sc.values()) > .4:
        ev.append({"type": "modality_disagreement", "severity": "medium", "description": "Modalities disagree: " + ", ".join(f"{k} {v:.0%}" for k, v in sc.items())})
    tot = sum(abs(v - .5) for v in sc.values()) or 1
    contrib = {k: round(abs(v - .5) / tot, 3) for k, v in sc.items()}
    why = f"Late fusion of {', '.join(sc)} gave mean P(fake)={sum(sc.values())/len(sc):.0%}." if sc else "No modality could be scored (see notes)."
    return {"id": uuid.uuid4().hex[:10], "prediction": verdict, "confidence": round(conf, 3), "probabilities": probs, "modalities": scores, "detected": mods,
            "evidence": ev, "detail": detail, "explanation": why, "consistency": cons, "notes": notes, "text": text, "contributions": contrib,
            "model_version": json.dumps(models.versions()), "processing_ms": int((time.time() - t0) * 1000), "timestamp": time.time()}

RETENTION_DAYS = float(os.getenv("RETENTION_DAYS", 30))
def purge():
    if RETENTION_DAYS > 0: db.execute("delete from analyses where ts < ?", (time.time() - RETENTION_DAYS * 86400,)); db.commit()

def save(r):
    purge()
    db.execute("insert into analyses values(?,?,?,?,?,?,?)", (r["id"], r["timestamp"], r["prediction"], r["confidence"], r["processing_ms"], json.dumps(r), None)); db.commit()
    log.info("analysis %s -> %s (%.2f)", r["id"], r["prediction"], r["confidence"]); return r

async def rd(fs):
    out = []
    for f in fs:
        d = await f.read(MAX + 1)
        if len(d) > MAX: raise HTTPException(413, "File too large")
        out.append({"name": os.path.basename(f.filename or "file"), "data": d})
    return out  # memory only, nothing written to disk

@app.post("/analyze")
async def analyze(text: str = Form(""), files: list[UploadFile] = File(default=[])): return save(await asyncio.to_thread(run, text, await rd(files)))
@app.post("/analyze/text")
async def a_text(text: str = Form(...)): return save(await asyncio.to_thread(run, text, []))
@app.post("/analyze/image")
async def a_img(file: UploadFile = File(...)): return save(await asyncio.to_thread(run, "", await rd([file])))
@app.post("/analyze/audio")
async def a_aud(file: UploadFile = File(...)): return save(await asyncio.to_thread(run, "", await rd([file])))
@app.post("/analyze/video")
async def a_vid(file: UploadFile = File(...)): return save(await asyncio.to_thread(run, "", await rd([file])))

@app.get("/analysis/{id}")
def get(id: str):
    r = db.execute("select result, review from analyses where id=?", (id,)).fetchone()
    if not r: raise HTTPException(404, "Not found")
    d = json.loads(r[0]); d["review"] = json.loads(r[1]) if r[1] else None; return d

@app.post("/analysis/{id}/review")
def review(id: str, body: dict):
    if body.get("verdict") not in ("REAL", "FAKE", "UNCERTAIN"): raise HTTPException(400, "Invalid verdict")
    rv = {"verdict": body["verdict"], "notes": str(body.get("notes", ""))[:2000], "ts": time.time()}
    if not db.execute("update analyses set review=? where id=?", (json.dumps(rv), id)).rowcount: raise HTTPException(404, "Not found")
    db.commit(); return rv

@app.get("/history")
def history(verdict: str = "", limit: int = 50, offset: int = 0):
    q, args = "select id, ts, verdict, conf, ms from analyses", []
    if verdict: q += " where verdict=?"; args.append(verdict.upper())
    return [dict(zip(("id", "timestamp", "prediction", "confidence", "processing_ms"), r)) for r in db.execute(q + " order by ts desc limit ? offset ?", args + [min(limit, 200), offset])]

@app.delete("/analysis/{id}")
def delete(id: str):
    if not db.execute("delete from analyses where id=?", (id,)).rowcount: raise HTTPException(404, "Not found")
    db.commit(); return {"deleted": id}

def jf(name, empty):
    p = DATA / name; return json.loads(p.read_text()) if p.exists() else empty

@app.get("/research/results")
def research(): return jf("results.json", {"available": False, "message": "No experiment results found. Write real results to backend/data/results.json."})
@app.get("/dataset/statistics")
def dataset(): return jf("dataset.json", {"available": False, "message": "No dataset statistics found. Write them to backend/data/dataset.json."})
@app.get("/cases")
def cases():  # difficult cases = analyses where a human reviewer disagreed with the model, plus any curated data/cases.json
    out = jf("cases.json", [])
    for i, (rid, res, rv) in enumerate(db.execute("select id, result, review from analyses where review is not null")):
        rv, res = json.loads(rv), json.loads(res)
        if rv["verdict"] != res["prediction"]: out.append({"id": rid, "expected": rv["verdict"], "predicted": res["prediction"], "reason": rv["notes"] or "Reviewer override"})
    return out

@app.get("/analysis/{id}/report.pdf")
def report(id: str):
    from fastapi.responses import Response
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    d = get(id); buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); y = [800]
    def line(t, size=10):
        for chunk in [t[i:i + 95] for i in range(0, len(t), 95)] or [""]:
            c.setFont("Helvetica", size); c.drawString(40, y[0], chunk); y[0] -= size + 5
            if y[0] < 50: c.showPage(); y[0] = 800
    line("VERILENS AI - CONTENT VERIFICATION REPORT", 16); line(f"Analysis {d['id']}   {time.ctime(d['timestamp'])}")
    line(f"Verdict: {d['prediction']}   Confidence: {d['confidence']:.1%}", 14); line("Modalities: " + ", ".join(d["detected"]))
    for k, v in d["modalities"].items(): line(f"  {k}: " + ("not scored" if v is None else f"P(fake)={v:.1%}"))
    if d.get("consistency"): line("Cross-modal consistency: " + ", ".join(f"{k}={v}" for k, v in d["consistency"].items() if k != "contradictions" and v is not None))
    line("Evidence:", 12)
    for e in d["evidence"]: line(f" - [{e['severity']}] {e['type']}: {e['description']}")
    line("Explanation: " + d["explanation"]); line("Probabilities: " + str(d["probabilities"]))
    if d.get("review"): line(f"Human review: {d['review']['verdict']} - {d['review']['notes']}")
    line("Models: " + (lambda mv: ", ".join(f"{k}={v}" for k, v in mv.items()) if isinstance(mv, dict) else str(mv))(json.loads(d["model_version"]) if d["model_version"].startswith("{") else d["model_version"]))
    c.save(); return Response(buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=verilens-{id}.pdf"})
@app.get("/health")
def health(): return {"status": "ok", "model_version": MODEL_VERSION, "models": {k: ("loaded" if k in models._cache and not isinstance(models._cache[k], Exception) else (str(models._cache[k]) if k in models._cache else "not loaded yet")) for k in ("image", "audio", "asr")}, "gemini_configured": not os.getenv("GEMINI_API_KEY", "your_").startswith("your_"), "learned_fusion": learned() is not None}


import threading
JOBS = {}
def _worker(jid, text, fs):
    try:
        r = save(run(text, fs, lambda st: JOBS[jid].update(stage=st)))
        JOBS[jid].update(status="done", stage="Done", analysis_id=r["id"])
    except HTTPException as e: JOBS[jid].update(status="error", error=e.detail)
    except Exception as e: log.exception("job failed"); JOBS[jid].update(status="error", error="Analysis failed unexpectedly")

@app.post("/jobs")
async def start_job(text: str = Form(""), files: list[UploadFile] = File(default=[])):
    fs = await rd(files)
    if not text.strip() and not fs: raise HTTPException(400, "Provide text or at least one file")
    for k in [k for k, v in JOBS.items() if time.time() - v["created"] > 3600]: JOBS.pop(k)
    jid = uuid.uuid4().hex[:12]; JOBS[jid] = {"status": "running", "stage": "Validating input", "created": time.time()}
    threading.Thread(target=_worker, args=(jid, text, fs), daemon=True).start(); return {"job_id": jid}

@app.get("/jobs/{jid}")
def job(jid: str):
    if jid not in JOBS: raise HTTPException(404, "Unknown job")
    return {k: v for k, v in JOBS[jid].items() if k != "created"}