"""Backend do Editor GM Beauty.

Fase 1: apenas um esqueleto com verificação de saúde. As rotas reais de
projetos/upload entram na Fase 2; transcrição na Fase 3; render na Fase 5.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Editor GM Beauty API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # o frontend local
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
