"""Arquivos no disco. Ficam FORA de qualquer pasta pública: só saem pela API."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import config


def project_dir(project_id: str) -> Path:
    d = config.PROJECTS_DIR / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def original(project_id: str, ext: str) -> Path:
    return project_dir(project_id) / f"original{ext}"


def audio(project_id: str) -> Path:
    return project_dir(project_id) / "audio.wav"


def thumbnail(project_id: str) -> Path:
    return project_dir(project_id) / "thumb.jpg"


def output(project_id: str) -> Path:
    return project_dir(project_id) / "output.mp4"


def delete_project_files(project_id: str) -> None:
    """Exclusão permanente: apaga original, áudio, miniatura e vídeo exportado."""
    shutil.rmtree(config.PROJECTS_DIR / project_id, ignore_errors=True)


def logo_path() -> Path | None:
    for p in sorted(config.DATA_DIR.glob("logo.*")):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            return p
    return None


def delete_logo() -> None:
    for p in config.DATA_DIR.glob("logo.*"):
        p.unlink(missing_ok=True)


def sfx_dir() -> Path:
    d = config.DATA_DIR / "library" / "sfx"
    d.mkdir(parents=True, exist_ok=True)
    return d


def sfx_file(sound_id: str, ext: str) -> Path:
    return sfx_dir() / f"{sound_id}{ext}"


def broll_dir() -> Path:
    d = config.DATA_DIR / "library" / "broll"
    d.mkdir(parents=True, exist_ok=True)
    return d


def broll_file(clip_id: str, ext: str) -> Path:
    return broll_dir() / f"{clip_id}{ext}"


def broll_thumb(clip_id: str) -> Path:
    return broll_dir() / f"{clip_id}.jpg"
