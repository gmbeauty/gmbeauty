"""Tarefas demoradas (análise e exportação) rodando em segundo plano.

Fila simples dentro da própria API (2 tarefas ao mesmo tempo). Se um dia
precisar de algo maior, só este arquivo muda.
"""
from __future__ import annotations

import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from . import storage
from .db import DictionaryTerm, Project, SessionLocal, SfxSound
from .errors import GENERIC_MESSAGE, ProcessingError, logger
from .schemas import Caption, RenderSettings
from .services import captions as captions_svc
from .services import ffmpeg, render, transcribe

_pool = ThreadPoolExecutor(max_workers=2)


def submit(fn, project_id: str) -> None:
    _pool.submit(_guard, fn, project_id)


def _guard(fn, project_id: str) -> None:
    """Qualquer erro vira mensagem simples na tela + detalhe técnico no log."""
    db = SessionLocal()
    try:
        fn(db, project_id)
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, ProcessingError):
            msg, detail = exc.user_message, exc.detail
        else:
            msg, detail = GENERIC_MESSAGE, traceback.format_exc()
        logger.error("project=%s failed: %s\n%s", project_id, msg, detail)
        p = db.get(Project, project_id)
        if p:
            p.status, p.stage, p.error_message, p.error_detail = "error", None, msg, detail[:8000]
            db.commit()
    finally:
        db.close()


def _set(db, p: Project, **fields) -> None:
    for k, v in fields.items():
        setattr(p, k, v)
    db.commit()


def analyze(db, project_id: str) -> None:
    """Extrair áudio → transcrever → timestamps → silêncios → legendas."""
    p = db.get(Project, project_id)
    settings = RenderSettings(**(p.settings or {}))
    terms = [t.term for t in db.query(DictionaryTerm).filter_by(owner_id=p.owner_id)]

    _set(db, p, status="processing", stage="audio", error_message=None, error_detail=None)
    if not p.has_audio:
        raise ProcessingError("Este vídeo não tem áudio para transcrever.", "no audio stream")
    wav = storage.audio(p.id)
    ffmpeg.extract_audio(storage.original(p.id, p.ext), wav)

    _set(db, p, stage="transcricao")
    words = transcribe.transcribe(wav, terms)

    _set(db, p, stage="silencios")
    silences = ffmpeg.detect_silences(wav, p.duration_sec, min_sec=0.5)

    _set(db, p, stage="legendas")
    caps = captions_svc.build_captions(words)
    captions_svc.apply_strategy(caps, settings.highlight_strategy)
    wav.unlink(missing_ok=True)  # o áudio temporário não precisa ficar guardado

    p.captions = caps
    p.silences = [{"id": f"s{i}", "startSec": round(a, 2), "endSec": round(b, 2)} for i, (a, b) in enumerate(silences)]
    _set(db, p, analyzed=True, status="draft", stage=None, has_output=False)


def export(db, project_id: str) -> None:
    p = db.get(Project, project_id)
    settings = RenderSettings(**(p.settings or {}))
    _set(db, p, status="processing", stage="render", progress=0, error_message=None, error_detail=None)

    out = storage.output(p.id)
    tmp = out.with_suffix(".tmp.mp4")

    def on_progress(pct: float) -> None:
        # Guarda no máximo de 2 em 2% para não sobrecarregar o banco.
        if pct - (p.progress or 0) >= 2:
            _set(db, p, progress=round(pct, 1))

    render.render(
        video=storage.original(p.id, p.ext),
        out=tmp,
        work_dir=storage.project_dir(p.id),
        src_w=p.width,
        src_h=p.height,
        duration=p.duration_sec,
        has_audio=p.has_audio,
        captions=[Caption(**c) for c in p.captions],
        silences=[(s["startSec"], s["endSec"]) for s in p.silences],
        settings=settings,
        logo=storage.logo_path(),
        sfx=_sfx_files(db, p),
        on_progress=on_progress,
    )
    tmp.replace(out)
    _set(db, p, status="ready", stage=None, progress=100, has_output=True)


def _sfx_files(db, p: Project) -> list[tuple[float, Path]]:
    """Efeitos do projeto que ainda existem na Biblioteca GM."""
    out = []
    for ev in p.sfx_events or []:
        snd = db.get(SfxSound, ev["sfxId"])
        if snd and storage.sfx_file(snd.id, snd.ext).exists():
            out.append((float(ev["startSec"]), storage.sfx_file(snd.id, snd.ext)))
    return sorted(out)


def recover_interrupted() -> None:
    """Se a API foi fechada no meio de uma tarefa, não deixa o projeto 'processando' para sempre."""
    db = SessionLocal()
    try:
        for p in db.query(Project).filter_by(status="processing"):
            p.status, p.stage = "error", None
            p.error_message = "O processamento foi interrompido. Tente novamente."
        db.commit()
    finally:
        db.close()
