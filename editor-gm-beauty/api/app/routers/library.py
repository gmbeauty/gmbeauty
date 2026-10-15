"""Biblioteca GM: arquivos seus (hoje, efeitos sonoros; depois, B-roll)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import storage
from ..db import BrollClip, Project, SfxSound, _new_id, get_db
from ..errors import ProcessingError, logger
from ..schemas import BrollClipOut, BrollClipPatch, SfxSoundOut
from ..services import ffmpeg

router = APIRouter(prefix="/library")

ALLOWED_AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
CATEGORIES = {"transicao", "destaque", "oferta", "outro"}
MAX_SFX_BYTES = 10 * 1024 * 1024
MAX_SFX_SEC = 15.0
ALLOWED_VIDEO = {".mp4", ".mov"}
MAX_BROLL_BYTES = 500 * 1024 * 1024


def _out(s: SfxSound) -> SfxSoundOut:
    return SfxSoundOut.model_validate(
        {"id": s.id, "name": s.name, "category": s.category, "duration_sec": s.duration_sec, "created_at": s.created_at}
    )


@router.get("/sfx", response_model=list[SfxSoundOut], response_model_by_alias=True)
def list_sfx(db: Session = Depends(get_db)):
    rows = db.query(SfxSound).filter_by(owner_id="local").order_by(SfxSound.created_at).all()
    return [_out(s) for s in rows]


@router.post("/sfx", response_model=SfxSoundOut, response_model_by_alias=True, status_code=201)
def upload_sfx(
    file: UploadFile = File(...),
    name: str = Form(""),
    category: str = Form("outro"),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(400, "Formato não aceito. Envie o som em MP3, WAV, M4A, AAC ou OGG.")
    if category not in CATEGORIES:
        raise HTTPException(400, "Tipo de efeito inválido.")
    data = file.file.read(MAX_SFX_BYTES + 1)
    if len(data) > MAX_SFX_BYTES:
        raise HTTPException(413, "O arquivo de som é grande demais (máximo 10 MB).")

    sound = SfxSound(
        id=_new_id(),
        name=name.strip() or Path(file.filename or "Efeito").stem,
        category=category,
        ext=ext,
    )
    dest = storage.sfx_file(sound.id, ext)
    dest.write_bytes(data)
    try:
        duration = ffmpeg.probe_audio(dest)
    except ProcessingError as exc:
        logger.error("sfx rejected: %s | %s", exc.user_message, exc.detail)
        dest.unlink(missing_ok=True)
        raise HTTPException(400, exc.user_message)
    if duration > MAX_SFX_SEC:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, f"O efeito é longo demais ({duration:.0f} s). Use sons de até {MAX_SFX_SEC:.0f} s.")
    sound.duration_sec = duration
    db.add(sound)
    db.commit()
    return _out(sound)


@router.get("/sfx/{sound_id}/audio")
def sfx_audio(sound_id: str, db: Session = Depends(get_db)):
    s = db.get(SfxSound, sound_id)
    path = storage.sfx_file(s.id, s.ext) if s else None
    if not s or not path.exists():
        raise HTTPException(404, "Som não encontrado.")
    return FileResponse(path)


@router.delete("/sfx/{sound_id}", status_code=204)
def delete_sfx(sound_id: str, db: Session = Depends(get_db)):
    s = db.get(SfxSound, sound_id)
    if not s:
        return
    storage.sfx_file(s.id, s.ext).unlink(missing_ok=True)
    # tira o som removido de todos os projetos
    for p in db.query(Project).all():
        if p.sfx_events and any(e["sfxId"] == sound_id for e in p.sfx_events):
            p.sfx_events = [e for e in p.sfx_events if e["sfxId"] != sound_id]
    db.delete(s)
    db.commit()


# ---------- B-roll (Fase 11) ----------

def _clip_out(c: BrollClip) -> BrollClipOut:
    return BrollClipOut.model_validate(
        {"id": c.id, "name": c.name, "tag": c.tag, "duration_sec": c.duration_sec, "width": c.width, "height": c.height, "created_at": c.created_at}
    )


@router.get("/broll", response_model=list[BrollClipOut], response_model_by_alias=True)
def list_broll(db: Session = Depends(get_db)):
    return [_clip_out(c) for c in db.query(BrollClip).filter_by(owner_id="local").order_by(BrollClip.created_at)]


@router.post("/broll", response_model=BrollClipOut, response_model_by_alias=True, status_code=201)
def upload_broll(
    file: UploadFile = File(...),
    name: str = Form(""),
    tag: str = Form(""),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO:
        raise HTTPException(400, "Formato não aceito. Envie o clipe em MP4 ou MOV.")
    clip = BrollClip(id=_new_id(), name=name.strip() or Path(file.filename or "Clipe").stem, tag=tag.strip(), ext=ext)
    dest = storage.broll_file(clip.id, ext)
    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BROLL_BYTES:
                    raise HTTPException(413, "O clipe é grande demais (máximo 500 MB).")
                out.write(chunk)
        info = ffmpeg.probe(dest)
        ffmpeg.make_thumbnail(dest, storage.broll_thumb(clip.id), info["duration"])
    except ProcessingError as exc:
        logger.error("broll rejected: %s | %s", exc.user_message, exc.detail)
        dest.unlink(missing_ok=True)
        raise HTTPException(400, exc.user_message)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    clip.duration_sec, clip.width, clip.height = info["duration"], info["width"], info["height"]
    db.add(clip)
    db.commit()
    return _clip_out(clip)


@router.patch("/broll/{clip_id}", response_model=BrollClipOut, response_model_by_alias=True)
def patch_broll(clip_id: str, body: BrollClipPatch, db: Session = Depends(get_db)):
    c = db.get(BrollClip, clip_id)
    if not c:
        raise HTTPException(404, "Clipe não encontrado.")
    if body.name is not None and body.name.strip():
        c.name = body.name.strip()
    if body.tag is not None:
        c.tag = body.tag.strip()
    db.commit()
    return _clip_out(c)


@router.get("/broll/{clip_id}/video")
def broll_video(clip_id: str, db: Session = Depends(get_db)):
    c = db.get(BrollClip, clip_id)
    path = storage.broll_file(c.id, c.ext) if c else None
    if not c or not path.exists():
        raise HTTPException(404, "Clipe não encontrado.")
    return FileResponse(path, media_type="video/quicktime" if c.ext == ".mov" else "video/mp4")


@router.get("/broll/{clip_id}/thumbnail")
def broll_thumbnail(clip_id: str):
    path = storage.broll_thumb(clip_id)
    if not path.exists():
        raise HTTPException(404, "Miniatura não encontrada.")
    return FileResponse(path, media_type="image/jpeg")


@router.delete("/broll/{clip_id}", status_code=204)
def delete_broll(clip_id: str, db: Session = Depends(get_db)):
    c = db.get(BrollClip, clip_id)
    if not c:
        return
    storage.broll_file(c.id, c.ext).unlink(missing_ok=True)
    storage.broll_thumb(c.id).unlink(missing_ok=True)
    for p in db.query(Project).all():  # tira o clipe removido de todos os projetos
        if p.broll_events and any(e["clipId"] == clip_id for e in p.broll_events):
            p.broll_events = [e for e in p.broll_events if e["clipId"] != clip_id]
    db.delete(c)
    db.commit()
