"""Real model adapters. Every function either returns a real model output or raises RuntimeError -
nothing is ever faked. Models are lazy-loaded and cached; weights download from Hugging Face on first use."""
import os, io, json, base64, shutil, logging, subprocess, tempfile, contextlib
import httpx
from PIL import Image

log = logging.getLogger("verilens.models")
IMG_MODEL = os.getenv("IMAGE_MODEL", "prithivMLmods/Deep-Fake-Detector-v2-Model")
AUDIO_MODEL = os.getenv("AUDIO_MODEL", "garystafford/wav2vec2-deepfake-voice-detector")
ASR_MODEL = os.getenv("ASR_MODEL", "openai/whisper-small")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
VIDEO_FRAMES = int(os.getenv("VIDEO_FRAMES", 12))
_cache = {}

def _lazy(key, build):
    if key not in _cache:
        try: _cache[key] = build()
        except Exception as e: log.error("load %s failed: %s", key, e); _cache[key] = e
    if isinstance(_cache[key], Exception): raise RuntimeError(f"{key} unavailable: {_cache[key]}")
    return _cache[key]

def versions():
    return {"image": IMG_MODEL, "audio": AUDIO_MODEL, "asr": ASR_MODEL, "llm": GEMINI_MODEL}

@contextlib.contextmanager
def tmpfile(data, suffix):  # uploads live on disk only for the duration of inference
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try: f.write(data); f.close(); yield f.name
    finally: os.unlink(f.name)

def _fake_p(out):  # label-agnostic: take the probability of the label that names the fake class
    for o in out:
        if any(w in o["label"].lower() for w in ("fake", "spoof", "artificial", "synthetic", "ai")): return float(o["score"])
    for o in out:
        if any(w in o["label"].lower() for w in ("real", "human", "bonafide", "realism")): return 1 - float(o["score"])
    raise RuntimeError(f"cannot map labels {[o['label'] for o in out]}")

def face_crop(img):
    """Largest frontal face (+25% margin) via OpenCV Haar cascade, or None. Deepfake classifiers are trained on face crops."""
    import cv2, numpy as np
    c = _lazy("face", lambda: cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"))
    f = c.detectMultiScale(cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY), 1.1, 5, minSize=(48, 48))
    if len(f) == 0: return None
    x, y, w, h = max(f, key=lambda r: r[2] * r[3]); mg = int(.25 * w)
    return img.crop((max(0, x - mg), max(0, y - mg), min(img.width, x + w + mg), min(img.height, y + h + mg)))

def image_analysis(img: Image.Image):
    """Returns (P(fake), face_detected). Scores the face crop when a face is found, else the whole image."""
    from transformers import pipeline
    try: face = face_crop(img)
    except Exception as e: log.warning("face detection unavailable: %s", e); face = None
    pipe = _lazy("image", lambda: pipeline("image-classification", model=IMG_MODEL, top_k=None))
    return _fake_p(pipe((face or img).convert("RGB"))), face is not None

def image_score(img: Image.Image) -> float: return image_analysis(img)[0]

def audio_score(path):
    """Returns (P(fake), per-window timeline) over 6s windows."""
    import librosa, numpy as np
    from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
    import torch
    fe = _lazy("audio_fe", lambda: AutoFeatureExtractor.from_pretrained(AUDIO_MODEL))
    m = _lazy("audio", lambda: AutoModelForAudioClassification.from_pretrained(AUDIO_MODEL).eval())
    y, sr = librosa.load(path, sr=16000, mono=True)
    if len(y) < 1600: raise RuntimeError("audio too short")
    w, tl = 16000 * 6, []
    for i in range(0, len(y), w):
        seg = y[i:i + w]
        if len(seg) < 16000 and tl: break
        with torch.no_grad(): p = torch.softmax(m(**fe(seg, sampling_rate=16000, return_tensors="pt")).logits, -1)[0]
        lab = {k: v.lower() for k, v in m.config.id2label.items()}
        fi = next((k for k, v in lab.items() if any(x in v for x in ("fake", "spoof", "synthetic"))), 1)
        tl.append({"t": i / 16000, "score": float(p[fi])})
    return float(np.mean([x["score"] for x in tl])), tl

def transcribe(path):
    from transformers import pipeline
    asr = _lazy("asr", lambda: pipeline("automatic-speech-recognition", model=ASR_MODEL, chunk_length_s=30))
    return asr(path)["text"].strip()

def video_frames(path, n=VIDEO_FRAMES):
    import cv2
    cap = cv2.VideoCapture(path); total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 25
    if total <= 0: raise RuntimeError("cannot read video")
    out = []
    for k in range(min(n, total)):
        idx = int(k * total / min(n, total)); cap.set(cv2.CAP_PROP_POS_FRAMES, idx); ok, fr = cap.read()
        if ok: out.append((idx / fps, Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
    cap.release(); return out

def video_score(path):
    frames = video_frames(path)
    tl = [{"t": round(t, 2), "score": image_score(im)} for t, im in frames]
    if not tl: raise RuntimeError("no frames decoded")
    return sum(x["score"] for x in tl) / len(tl), tl

def video_audio(path):  # extract audio track with ffmpeg, if present
    if not shutil.which("ffmpeg"): return None
    wav = path + ".wav"
    r = subprocess.run(["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav], capture_output=True)
    return wav if r.returncode == 0 and os.path.exists(wav) else None

def gemini(parts, instruction):
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key.startswith("your_"): raise RuntimeError("GEMINI_API_KEY not set")
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                   headers={"x-goog-api-key": key}, timeout=60,
                   json={"contents": [{"parts": [{"text": instruction}] + parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}})
    r.raise_for_status()
    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])

TEXT_PROMPT = """You are a misinformation analyst. Analyze the text and return JSON only:
{"fake_probability": 0-1 (likelihood the text is false, fabricated or manipulative),
 "claims": [short factual claims], "entities": [named entities],
 "suspicious_phrases": [exact substrings of the text that raised suspicion],
 "rationale": "one sentence"}
Text (may be English or Hindi-English code-mixed):
"""

def text_analysis(text):
    d = gemini([{"text": text}], TEXT_PROMPT)
    return {"score": max(0, min(1, float(d["fake_probability"]))), "claims": d.get("claims", []), "entities": d.get("entities", []),
            "phrases": [p for p in d.get("suspicious_phrases", []) if p and p in text], "rationale": d.get("rationale", "")}

CONS_PROMPT = """Check cross-modal consistency. Using only the provided material, return JSON:
{"text_image": 0-1 or null, "text_audio": 0-1 or null, "image_audio": 0-1 or null,
 "contradictions": [short descriptions]}
1 = fully consistent, 0 = contradictory. Use null if either side is missing.
"""

def consistency(text, image_bytes, transcript):
    parts = []
    if text: parts.append({"text": "CAPTION/TEXT: " + text})
    if image_bytes: parts.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}})
    if transcript: parts.append({"text": "AUDIO TRANSCRIPT: " + transcript})
    if len(parts) < 2: return None
    return gemini(parts, CONS_PROMPT)
