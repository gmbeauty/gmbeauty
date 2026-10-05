from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config, jobs, storage
from ..db import DictionaryTerm, Project, SfxSound, _new_id, get_db
from ..errors import ProcessingError, logger
from ..schemas import (
    Caption,
    CaptionsIn,
    DictionaryIn,
    HighlightsIn,
    InsightsOut,
    SfxEventsIn,
    ProjectOut,
    ProjectPatch,
    RenderSettings,
)
from ..services import captions as captions_svc
from ..services import ffmpeg, hook, sfx, zoom

router = APIRouter()
ALLOWED_EXT = {".mp4", ".mov"}
NOT_FOUND = HTTPException(404, "Projeto não encontrado.")


def _get(db: Session, project_id: str) -> Project:
    p = db.get(Project, project_id)
    if not p or p.owner_id != "local":
        raise NOT_FOUND
    return p


def _out(p: Project) -> ProjectOut:
    data = {c.name: getattr(p, c.name) for c in Project.__table__.columns}
    data["settings"] = RenderSettings(**(p.settings or {}))
    data["sfx_events"] = p.sfx_events or []
    return ProjectOut.model_validate(data)


@router.get("/projects", response_model=list[ProjectOut], response_model_by_alias=True)
def list_projects(db: Session = Depends(get_db)):
    rows = db.query(Project).filter_by(owner_id="local").order_by(Project.created_at.desc()).all()
    return [_out(p) for p in rows]


@router.post("/projects", response_model=ProjectOut, response_model_by_alias=True, status_code=201)
def create_project(
    file: UploadFile = File(...),
    content_type: str = Form("ugc", alias="contentType"),
    style: str = Form("gm-clean"),
    name: str = Form(""),
    settings: str = Form("{}"),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Formato não aceito. Envie um vídeo MP4 ou MOV.")
    try:
        parsed = RenderSettings(**json.loads(settings or "{}"))
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "Configurações inválidas.")

    project = Project(
        id=_new_id(),
        name=name.strip() or Path(file.filename or "Vídeo").stem,
        content_type=content_type,
        style=style,
        original_name=file.filename or "",
        ext=ext,
        settings=parsed.model_dump(by_alias=False),
    )
    dest = storage.original(project.id, ext)
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"O vídeo é maior que {config.MAX_UPLOAD_MB} MB.")
                out.write(chunk)
        info = ffmpeg.probe(dest)
        ffmpeg.make_thumbnail(dest, storage.thumbnail(project.id), info["duration"])
    except ProcessingError as exc:
        logger.error("upload rejected: %s | %s", exc.user_message, exc.detail)
        storage.delete_project_files(project.id)
        raise HTTPException(400, exc.user_message)
    except HTTPException:
        storage.delete_project_files(project.id)
        raise

    project.size_bytes = size
    project.duration_sec = info["duration"]
    project.width, project.height, project.has_audio = info["width"], info["height"], info["has_audio"]
    db.add(project)
    db.commit()
    return _out(project)


@router.get("/projects/{project_id}", response_model=ProjectOut, response_model_by_alias=True)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return _out(_get(db, project_id))


@router.patch("/projects/{project_id}", response_model=ProjectOut, response_model_by_alias=True)
def patch_project(project_id: str, body: ProjectPatch, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    if body.name is not None:
        p.name = body.name.strip() or p.name
    if body.content_type is not None:
        p.content_type = body.content_type
    if body.style is not None:
        p.style = body.style
    if body.settings is not None:
        p.settings = body.settings.model_dump(by_alias=False)
    if p.status == "ready":
        p.status = "draft"  # mexeu depois de exportar: o vídeo exportado ficou desatualizado
    db.commit()
    return _out(p)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    storage.delete_project_files(p.id)
    db.delete(p)
    db.commit()


@router.post("/projects/{project_id}/duplicate", response_model=ProjectOut, response_model_by_alias=True, status_code=201)
def duplicate_project(project_id: str, db: Session = Depends(get_db)):
    src = _get(db, project_id)
    copy = Project(
        id=_new_id(),
        name=f"{src.name} (cópia)",
        content_type=src.content_type,
        style=src.style,
        original_name=src.original_name,
        ext=src.ext,
        duration_sec=src.duration_sec,
        width=src.width,
        height=src.height,
        size_bytes=src.size_bytes,
        has_audio=src.has_audio,
        settings=json.loads(json.dumps(src.settings)),
        captions=json.loads(json.dumps(src.captions)),
        silences=json.loads(json.dumps(src.silences)),
        sfx_events=json.loads(json.dumps(src.sfx_events or [])),
        analyzed=src.analyzed,
    )
    shutil.copyfile(storage.original(src.id, src.ext), storage.original(copy.id, copy.ext))
    if storage.thumbnail(src.id).exists():
        shutil.copyfile(storage.thumbnail(src.id), storage.thumbnail(copy.id))
    db.add(copy)
    db.commit()
    return _out(copy)


# ---------- arquivos (nunca públicos: só por estas rotas) ----------

@router.get("/projects/{project_id}/video")
def get_video(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    path = storage.original(p.id, p.ext)
    if not path.exists():
        raise NOT_FOUND
    return FileResponse(path, media_type="video/quicktime" if p.ext == ".mov" else "video/mp4")


@router.get("/projects/{project_id}/thumbnail")
def get_thumbnail(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    path = storage.thumbnail(p.id)
    if not path.exists():
        raise NOT_FOUND
    return FileResponse(path, media_type="image/jpeg")


@router.get("/projects/{project_id}/download")
def download(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    path = storage.output(p.id)
    if not p.has_output or not path.exists():
        raise HTTPException(404, "O vídeo ainda não foi exportado.")
    safe = "".join(ch for ch in p.name if ch.isalnum() or ch in " -_").strip() or "video"
    return FileResponse(path, media_type="video/mp4", filename=f"{safe} - GM Beauty.mp4")


# ---------- processamento ----------

def _require_idle(p: Project) -> None:
    if p.status == "processing":
        raise HTTPException(409, "Este vídeo já está sendo processado. Aguarde um instante.")


@router.post("/projects/{project_id}/analyze", response_model=ProjectOut, response_model_by_alias=True, status_code=202)
def analyze(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    _require_idle(p)
    p.status, p.stage, p.error_message = "processing", "audio", None
    db.commit()
    jobs.submit(jobs.analyze, p.id)
    return _out(p)


@router.post("/projects/{project_id}/export", response_model=ProjectOut, response_model_by_alias=True, status_code=202)
def export(project_id: str, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    _require_idle(p)
    p.status, p.stage, p.progress, p.error_message = "processing", "render", 0, None
    db.commit()
    jobs.submit(jobs.export, p.id)
    return _out(p)


@router.put("/projects/{project_id}/captions", response_model=ProjectOut, response_model_by_alias=True)
def put_captions(project_id: str, body: CaptionsIn, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    old = {c["id"]: c for c in p.captions}
    new = []
    for c in body.captions:
        if c.end_sec <= c.start_sec:
            raise HTTPException(400, "O fim de uma legenda precisa ser depois do início.")
        d = c.model_dump(by_alias=True)
        prev = old.get(c.id)
        # Os tempos por palavra só valem se o texto e os tempos não mudaram.
        unchanged = prev and prev["text"].split() == c.text.split() and prev["startSec"] == c.start_sec and prev["endSec"] == c.end_sec
        d["words"] = prev.get("words") if unchanged else None
        new.append(d)
    p.captions = sorted(new, key=lambda c: c["startSec"])
    if p.status == "ready":
        p.status = "draft"
    db.commit()
    return _out(p)


@router.post("/projects/{project_id}/highlights", response_model=ProjectOut, response_model_by_alias=True)
def set_highlights(project_id: str, body: HighlightsIn, db: Session = Depends(get_db)):
    """Recalcula os destaques automáticos (substitui os destaques atuais)."""
    p = _get(db, project_id)
    caps = json.loads(json.dumps(p.captions))
    p.captions = captions_svc.apply_strategy(caps, body.strategy)
    settings = RenderSettings(**(p.settings or {}))
    settings.highlight_strategy = body.strategy
    p.settings = settings.model_dump(by_alias=False)
    if p.status == "ready":
        p.status = "draft"
    db.commit()
    return _out(p)


# ---------- zoom (Fase 9) e gancho (Fase 10) ----------

@router.get("/projects/{project_id}/insights", response_model=InsightsOut, response_model_by_alias=True)
def insights(project_id: str, db: Session = Depends(get_db)):
    """Plano de zooms (usado na prévia e na exportação) e análise do gancho."""
    p = _get(db, project_id)
    settings = RenderSettings(**(p.settings or {}))
    caps = [Caption(**c) for c in p.captions]
    events = zoom.plan_zoom(caps, p.duration_sec, settings.zoom_mode)
    return {
        "zoom_plan": [{"start_sec": e.start, "end_sec": e.end, "amp": e.amp, "kind": e.kind} for e in events],
        "hook": hook.analyze_hook(caps, settings),
    }


@router.post("/projects/{project_id}/hook/highlight", response_model=ProjectOut, response_model_by_alias=True)
def highlight_hook(project_id: str, db: Session = Depends(get_db)):
    """Destaca a palavra mais forte da primeira fala."""
    p = _get(db, project_id)
    caps = json.loads(json.dumps(p.captions))
    first = min(caps, key=lambda c: c["startSec"], default=None)
    if first is None:
        raise HTTPException(400, "Ainda não há legendas para destacar.")
    first["highlightWords"] = hook.suggest_hook_highlight(first["text"])
    p.captions = caps
    if p.status == "ready":
        p.status = "draft"
    db.commit()
    return _out(p)


# ---------- efeitos sonoros (Fase 12) ----------

@router.post("/projects/{project_id}/sfx/suggest", response_model=ProjectOut, response_model_by_alias=True)
def suggest_sfx(project_id: str, db: Session = Depends(get_db)):
    """Propõe onde colocar os efeitos da Biblioteca GM (substitui a lista atual; a pessoa revisa)."""
    p = _get(db, project_id)
    settings = RenderSettings(**(p.settings or {}))
    caps = [Caption(**c) for c in p.captions]
    sounds = [sfx.Sound(s.id, s.category) for s in db.query(SfxSound).filter_by(owner_id="local")]
    if not sounds:
        raise HTTPException(400, "A Biblioteca GM ainda não tem efeitos sonoros. Envie alguns em “Biblioteca”.")
    zplan = zoom.plan_zoom(caps, p.duration_sec, settings.zoom_mode)
    p.sfx_events = sfx.plan_sfx(caps, zplan, settings, sounds, p.duration_sec)
    if p.status == "ready":
        p.status = "draft"
    db.commit()
    return _out(p)


@router.put("/projects/{project_id}/sfx", response_model=ProjectOut, response_model_by_alias=True)
def put_sfx(project_id: str, body: SfxEventsIn, db: Session = Depends(get_db)):
    p = _get(db, project_id)
    known = {s.id for s in db.query(SfxSound).filter_by(owner_id="local")}
    events = [e.model_dump(by_alias=True) for e in body.events if e.sfx_id in known and e.start_sec <= p.duration_sec]
    p.sfx_events = sorted(events, key=lambda e: e["startSec"])
    if p.status == "ready":
        p.status = "draft"
    db.commit()
    return _out(p)


# ---------- logo (única, da GM Beauty) ----------

@router.get("/logo/status")
def logo_status():
    return {"exists": storage.logo_path() is not None}


@router.get("/logo")
def get_logo():
    path = storage.logo_path()
    if not path:
        raise HTTPException(404, "Nenhuma logo enviada.")
    return FileResponse(path)


@router.post("/logo", status_code=201)
def upload_logo(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(400, "Envie a logo em PNG, JPG ou WEBP (PNG com fundo transparente é o ideal).")
    data = file.file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "A logo é grande demais (máximo 10 MB).")
    storage.delete_logo()
    (config.DATA_DIR / f"logo{ext}").write_bytes(data)
    return {"ok": True}


@router.delete("/logo", status_code=204)
def remove_logo():
    storage.delete_logo()


# ---------- Dicionário GM Beauty (estrutura pronta; ajuda a transcrição) ----------

@router.get("/dictionary")
def list_terms(db: Session = Depends(get_db)):
    return [{"id": t.id, "term": t.term} for t in db.query(DictionaryTerm).filter_by(owner_id="local")]


@router.post("/dictionary", status_code=201)
def add_term(body: DictionaryIn, db: Session = Depends(get_db)):
    t = DictionaryTerm(term=body.term.strip())
    db.add(t)
    db.commit()
    return {"id": t.id, "term": t.term}


@router.delete("/dictionary/{term_id}", status_code=204)
def delete_term(term_id: str, db: Session = Depends(get_db)):
    t = db.get(DictionaryTerm, term_id)
    if t:
        db.delete(t)
        db.commit()
