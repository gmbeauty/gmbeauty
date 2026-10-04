"""Fluxo completo com vídeo de verdade: upload → análise → edição → exportação → exclusão."""
import json
import subprocess
import time

from conftest import make_video


def wait(client, pid, want=("draft", "ready", "error"), timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        p = client.get(f"/projects/{pid}").json()
        if p["status"] in want:
            return p
        time.sleep(0.3)
    raise AssertionError("timeout")


def ffprobe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def upload(client, path, **form):
    with open(path, "rb") as f:
        return client.post("/projects", files={"file": (path.name, f, "video/mp4")}, data={"contentType": "ugc", "style": "gm-viral", **form})


def test_full_flow(client, landscape_video, tmp_path):
    r = upload(client, landscape_video)
    assert r.status_code == 201, r.text
    p = r.json()
    pid = p["id"]
    assert p["status"] == "draft" and p["durationSec"] > 9 and (p["width"], p["height"]) == (1280, 720)
    assert client.get(f"/projects/{pid}/thumbnail").status_code == 200
    assert client.get(f"/projects/{pid}/video", headers={"Range": "bytes=0-99"}).status_code in (200, 206)

    # análise: transcrição (simulada), silêncios e legendas
    assert client.post(f"/projects/{pid}/analyze").status_code == 202
    p = wait(client, pid)
    assert p["status"] == "draft" and p["analyzed"], p["errorMessage"]
    assert [c["text"] for c in p["captions"]] == ["Você ainda aplica base", "Então olha R$ 29,90", "Acabamento natural."]
    sil = [(s["startSec"], s["endSec"]) for s in p["silences"]]
    assert len(sil) == 2
    assert abs(sil[0][0] - 2.0) < 0.15 and abs(sil[0][1] - 4.0) < 0.15

    # destaques automáticos de oferta
    r = client.post(f"/projects/{pid}/highlights", json={"strategy": "offer"}).json()
    assert "2990" in r["captions"][1]["highlightWords"]

    # editar texto de uma legenda (nome de marca corrigido)
    caps = r["captions"]
    caps[0]["text"] = "Você ainda aplica Ruby Rose"
    r = client.put(f"/projects/{pid}/captions", json={"captions": caps}).json()
    assert r["captions"][0]["text"].endswith("Ruby Rose") and r["captions"][0]["words"] is None
    assert r["captions"][1]["words"] is not None  # intacta: mantém tempos por palavra

    # exportar: sem silêncios, 9:16, logo, palavra a palavra
    logo = tmp_path / "logo.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0xB57EDC:s=300x120", "-frames:v", "1", str(logo)], check=True)
    with open(logo, "rb") as f:
        assert client.post("/logo", files={"file": ("logo.png", f, "image/png")}).status_code == 201
    settings = {"captionMode": "word-by-word", "fontSize": "lg", "position": "bottom", "removeSilences": True,
                "logoPosition": "top", "highlightStrategy": "offer"}
    assert client.patch(f"/projects/{pid}", json={"settings": settings}).status_code == 200
    assert client.get(f"/projects/{pid}/download").status_code == 404  # ainda não exportou

    assert client.post(f"/projects/{pid}/export").status_code == 202
    p = wait(client, pid)
    assert p["status"] == "ready", p["errorMessage"]
    assert p["hasOutput"]

    out = tmp_path / "out.mp4"
    out.write_bytes(client.get(f"/projects/{pid}/download").content)
    info = ffprobe(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (v["codec_name"], v["width"], v["height"]) == ("h264", 1080, 1920)
    assert any(s["codec_type"] == "audio" for s in info["streams"])
    dur = float(info["format"]["duration"])
    assert 8.0 < dur < 8.7, dur  # 10 s menos ~1,7 s (só o miolo das pausas é removido)

    # editar depois de exportar volta para rascunho
    client.patch(f"/projects/{pid}", json={"name": "Novo nome"})
    assert client.get(f"/projects/{pid}").json()["status"] == "draft"

    # duplicar
    d = client.post(f"/projects/{pid}/duplicate").json()
    assert d["name"].endswith("(cópia)") and d["captions"] == client.get(f"/projects/{pid}").json()["captions"]
    assert client.get(f"/projects/{d['id']}/video").status_code == 200

    # exclusão permanente apaga os arquivos
    from app import config
    assert (config.PROJECTS_DIR / pid).exists()
    assert client.delete(f"/projects/{pid}").status_code == 204
    assert not (config.PROJECTS_DIR / pid).exists()
    assert client.get(f"/projects/{pid}").status_code == 404
    client.delete(f"/projects/{d['id']}")


def test_vertical_video_without_cuts(client, tmp_path):
    v = tmp_path / "vertical.mp4"
    make_video(v, size="540x960", seconds=5)
    pid = upload(client, v).json()["id"]
    client.patch(f"/projects/{pid}", json={"settings": {"logoPosition": "none"}})
    client.post(f"/projects/{pid}/export")
    p = wait(client, pid)
    assert p["status"] == "ready", p["errorMessage"]
    info = ffprobe(__import__("app.storage", fromlist=["x"]).output(pid))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (1080, 1920)
    client.delete(f"/projects/{pid}")


def test_friendly_errors(client, tmp_path):
    bad = tmp_path / "falso.mp4"
    bad.write_text("isso não é um vídeo")
    r = upload(client, bad)
    assert r.status_code == 400
    assert "ffmpeg" not in r.json()["detail"].lower() and "exit" not in r.json()["detail"].lower()

    txt = tmp_path / "nota.txt"
    txt.write_text("x")
    r = upload(client, txt)
    assert r.status_code == 400 and "MP4 ou MOV" in r.json()["detail"]
    assert client.get("/projects/naoexiste").status_code == 404


def test_render_failure_shows_simple_message_and_logs_detail(client, landscape_video, monkeypatch):
    from app.services import render as render_mod

    pid = upload(client, landscape_video).json()["id"]
    monkeypatch.setattr(render_mod, "OUT_W", 0)  # força um erro técnico no FFmpeg
    client.post(f"/projects/{pid}/export")
    p = wait(client, pid)
    assert p["status"] == "error"
    assert p["errorMessage"] == "Não conseguimos exportar este vídeo. Tente novamente."
    from app.db import Project, SessionLocal
    with SessionLocal() as db:
        assert "ffmpeg exit" in db.get(Project, pid).error_detail  # detalhe técnico só no banco/log
    client.delete(f"/projects/{pid}")
