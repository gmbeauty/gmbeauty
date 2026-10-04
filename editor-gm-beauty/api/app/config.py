"""Configuração por variáveis de ambiente (com padrões para uso local)."""
import os
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.getenv("DATA_DIR", API_DIR / "storage"))
PROJECTS_DIR = DATA_DIR / "projects"
LOGS_DIR = DATA_DIR / "logs"

# SQLite local por padrão. Para PostgreSQL/Supabase, basta trocar esta URL.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'editor.db'}")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "2048"))

# Transcrição: "auto" (OpenAI se houver chave, senão local), "openai", "local"
# ou "fake" (somente testes automatizados).
TRANSCRIBER = os.getenv("TRANSCRIBER", "auto")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")  # tiny/base/small/medium/large-v3

# Fonte usada nas legendas gravadas no vídeo (precisa estar instalada no computador
# que roda a API). Se não existir, o FFmpeg usa uma fonte parecida.
CAPTION_FONT = os.getenv("CAPTION_FONT", "Arial")
CAPTION_FONTS_DIR = os.getenv("CAPTION_FONTS_DIR", "")  # pasta com .ttf extras (opcional)

FFMPEG = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE = os.getenv("FFPROBE_BIN", "ffprobe")


def ensure_dirs() -> None:
    for d in (DATA_DIR, PROJECTS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
