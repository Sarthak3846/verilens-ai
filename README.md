# VeriLens AI
Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000`
Frontend: `cd frontend && npm install && npm run dev` (dev proxy /api -> :8000). Production: set VITE_API_URL to the backend URL.
Real results: put JSON in backend/data/ (see data/README.md). Deploy the backend on any container host; set CORS_ORIGINS.

## Real models
Set GEMINI_API_KEY / HF_TOKEN in backend/.env. First request downloads HF weights (needs internet + ~2GB disk). Docker: `docker compose up --build` (frontend :8080, API :8000).
Image: prithivMLmods/Deep-Fake-Detector-v2-Model · Audio: garystafford/wav2vec2-deepfake-voice-detector · ASR: openai/whisper-small · Text/consistency: Gemini.

## Experiments
1. Create `backend/data/manifest.csv` (id,path,text,label,source,manip_type[,split]) from your licensed dataset (>=300 rows).
2. `cd backend && python scripts/evaluate.py --manifest data/manifest.csv --faith` — runs the real models, writes results.json, dataset.json, cases.json and fusion.json (learned fusion + abstention band, picked up by the API automatically).
3. Tests: `cd backend && pytest tests`. Optional: `PRELOAD_MODELS=1` loads the image model at startup.
