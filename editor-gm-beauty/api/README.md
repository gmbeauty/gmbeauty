# API (FastAPI) — esqueleto da Fase 1

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/health
```

Pastas preparadas (vazias por enquanto):
- `app/routers/`  → rotas HTTP (projetos, upload, export)
- `app/services/` → lógica de vídeo (ffmpeg, whisper, legendas, silêncios)
