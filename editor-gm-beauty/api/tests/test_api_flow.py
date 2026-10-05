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
    assert client.get("/logo/status").json() == {"exists": False}
    with open(logo, "rb") as f:
        assert client.post("/logo", files={"file": ("logo.png", f, "image/png")}).status_code == 201
    assert client.get("/logo/status").json() == {"exists": True}
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


def test_zoom_and_trim_start_export(client, landscape_video, tmp_path):
    pid = upload(client, landscape_video).json()["id"]
    client.post(f"/projects/{pid}/analyze")
    wait(client, pid)

    # análise do gancho: a fala só começa em 0,1 s, então o início está ok
    ins = client.get(f"/projects/{pid}/insights").json()
    assert ins["zoomPlan"] == [] and ins["hook"]["checks"][0]["ok"]

    client.patch(f"/projects/{pid}", json={"settings": {"zoomMode": "dynamic"}})
    plan = client.get(f"/projects/{pid}/insights").json()["zoomPlan"]
    assert plan and plan[0]["kind"] == "settle" and plan[0]["startSec"] == 0

    r = client.post(f"/projects/{pid}/hook/highlight").json()
    assert r["captions"][0]["highlightWords"]  # palavra do gancho destacada

    # exporta com zoom + corte do início (sem remover silêncios)
    client.patch(f"/projects/{pid}", json={"settings": {"zoomMode": "dynamic", "trimStartSec": 3.0, "captionMode": "highlight"}})
    client.post(f"/projects/{pid}/export")
    p = wait(client, pid)
    assert p["status"] == "ready", p["errorMessage"]
    out = tmp_path / "zoom.mp4"
    out.write_bytes(client.get(f"/projects/{pid}/download").content)
    info = ffprobe(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (1080, 1920)
    assert 6.5 < float(info["format"]["duration"]) < 7.5  # 10 s - 3 s cortados do início

    # o zoom realmente muda a imagem: compara com a mesma exportação sem zoom
    client.patch(f"/projects/{pid}", json={"settings": {"zoomMode": "off", "trimStartSec": 3.0, "captionMode": "highlight"}})
    client.post(f"/projects/{pid}/export")
    wait(client, pid)
    plain = tmp_path / "plain.mp4"
    plain.write_bytes(client.get(f"/projects/{pid}/download").content)
    assert _frame_diff(out, plain, at=4.8) > 0.5  # pico do zoom (6,8 s original - 3 s cortados + 1 s)
    assert _frame_diff(out, plain, at=0.5) < 0.2  # fora do zoom as imagens são iguais
    client.delete(f"/projects/{pid}")


def _frame_diff(a, b, at):
    """Diferença média (0-255) entre o mesmo quadro de dois vídeos."""
    def frame(path):
        return subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(at), "-i", str(path), "-frames:v", "1", "-vf", "scale=108:192,format=gray", "-f", "rawvideo", "-"],
            capture_output=True, check=True,
        ).stdout
    fa, fb = frame(a), frame(b)
    return sum(abs(x - y) for x, y in zip(fa, fb)) / len(fa)


def _make_beep(path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=880:d=0.5", str(path)], check=True)


def _mean_volume(path, start, dur):
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", str(start), "-t", str(dur), "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split("mean_volume:")[1].split("dB")[0])
    return -91.0


def test_sound_library_and_sfx_mix(client, landscape_video, tmp_path):
    beep = tmp_path / "pop.wav"
    _make_beep(beep)
    # biblioteca: upload, tipos, validações
    with open(beep, "rb") as f:
        r = client.post("/library/sfx", files={"file": ("pop.wav", f, "audio/wav")}, data={"name": "Pop", "category": "destaque"})
    assert r.status_code == 201, r.text
    snd = r.json()
    assert snd["category"] == "destaque" and 0.4 < snd["durationSec"] < 0.7
    assert client.get(f"/library/sfx/{snd['id']}/audio").status_code == 200
    bad = tmp_path / "falso.mp3"
    bad.write_text("não é áudio")
    r = client.post("/library/sfx", files={"file": ("falso.mp3", open(bad, "rb"), "audio/mpeg")}, data={"category": "outro"})
    assert r.status_code == 400 and "ffmpeg" not in r.json()["detail"].lower()
    assert client.post("/library/sfx", files={"file": ("a.txt", b"x", "text/plain")}, data={"category": "outro"}).status_code == 400

    pid = upload(client, landscape_video).json()["id"]
    client.post(f"/projects/{pid}/analyze")
    wait(client, pid)

    # sugestão: destaque na palavra marcada
    client.post(f"/projects/{pid}/highlights", json={"strategy": "keywords"})
    client.patch(f"/projects/{pid}", json={"settings": {"captionMode": "highlight", "highlightStrategy": "keywords"}})
    sug = client.post(f"/projects/{pid}/sfx/suggest").json()
    assert sug["sfxEvents"] and all(e["sfxId"] == snd["id"] for e in sug["sfxEvents"])

    # evento manual no meio do silêncio (3,0 s) e exporta sem/ com efeitos
    ev = [{"id": "m1", "startSec": 3.0, "sfxId": snd["id"]}]
    assert client.put(f"/projects/{pid}/sfx", json={"events": ev}).json()["sfxEvents"][0]["startSec"] == 3.0
    assert client.put(f"/projects/{pid}/sfx", json={"events": ev + [{"id": "x", "startSec": 1, "sfxId": "naoexiste"}]}).json()["sfxEvents"] == ev

    outs = {}
    for name, enabled in (("sem", False), ("com", True)):
        client.patch(f"/projects/{pid}", json={"settings": {"sfxEnabled": enabled, "sfxGainDb": -10}})
        client.post(f"/projects/{pid}/export")
        p = wait(client, pid)
        assert p["status"] == "ready", p["errorMessage"]
        outs[name] = tmp_path / f"{name}.mp4"
        outs[name].write_bytes(client.get(f"/projects/{pid}/download").content)
    assert _mean_volume(outs["sem"], 3.0, 0.4) < -60  # o trecho é silêncio na fala
    assert _mean_volume(outs["com"], 3.0, 0.4) > -35  # o efeito está lá
    assert abs(float(ffprobe(outs["com"])["format"]["duration"]) - float(ffprobe(outs["sem"])["format"]["duration"])) < 0.2

    # apagar o som da biblioteca o remove dos projetos
    assert client.delete(f"/library/sfx/{snd['id']}").status_code == 204
    assert client.get(f"/projects/{pid}").json()["sfxEvents"] == []
    assert client.get("/library/sfx").json() == []
    client.delete(f"/projects/{pid}")


def test_old_database_gets_new_columns(tmp_path):
    """Um banco criado antes da Fase 12 (sem sfx_events) é atualizado sozinho."""
    import sqlite3

    from sqlalchemy import create_engine, inspect

    import app.db as dbmod

    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE projects (id VARCHAR PRIMARY KEY, name VARCHAR)")
    con.execute("INSERT INTO projects VALUES ('a1', 'antigo')")
    con.commit(); con.close()

    old = dbmod.engine
    dbmod.engine = create_engine(f"sqlite:///{path}")
    try:
        dbmod.Base.metadata.create_all(dbmod.engine)  # igual ao init_db: cria tabelas novas...
        dbmod._add_missing_columns()  # ...e acrescenta colunas novas nas antigas
        cols = {c["name"] for c in inspect(dbmod.engine).get_columns("projects")}
    finally:
        dbmod.engine = old
    assert {"sfx_events", "settings", "captions"} <= cols


def _make_color_clip(path, color="red", size="1080x1920", seconds=3):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={color}:s={size}:r=30:d={seconds}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )


def _pixel(path, at):
    """Cor média (R, G, B) do quadro em `at` segundos."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(at), "-i", str(path), "-frames:v", "1", "-vf", "crop=400:400:340:760,scale=1:1,format=rgb24", "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout
    return tuple(raw[:3])


def test_broll_library_suggestion_and_render(client, landscape_video, tmp_path):
    clip = tmp_path / "ruby.mp4"
    _make_color_clip(clip)
    with open(clip, "rb") as f:
        r = client.post("/library/broll", files={"file": ("ruby.mp4", f, "video/mp4")}, data={"name": "Close", "tag": "acabamento natural"})
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["tag"] == "acabamento natural" and c["durationSec"] > 2.5 and (c["width"], c["height"]) == (1080, 1920)
    assert client.get(f"/library/broll/{c['id']}/thumbnail").status_code == 200
    assert client.get(f"/library/broll/{c['id']}/video").status_code == 200
    assert client.patch(f"/library/broll/{c['id']}", json={"tag": "acabamento natural, natural"}).json()["tag"].endswith("natural")
    assert client.post("/library/broll", files={"file": ("a.txt", b"x", "text/plain")}, data={}).status_code == 400
    bad = tmp_path / "falso.mp4"
    bad.write_text("não é vídeo")
    r = client.post("/library/broll", files={"file": ("falso.mp4", open(bad, "rb"), "video/mp4")}, data={})
    assert r.status_code == 400 and "ffmpeg" not in r.json()["detail"].lower()

    pid = upload(client, landscape_video).json()["id"]
    empty = client.post(f"/projects/{pid}/broll/suggest")  # sem legendas ainda: nada foi citado, então nada é sugerido
    assert empty.status_code == 200 and empty.json()["brollEvents"] == []
    client.post(f"/projects/{pid}/analyze")
    wait(client, pid)
    sug = client.post(f"/projects/{pid}/broll/suggest").json()["brollEvents"]
    # "Acabamento natural." é falado em 6,8 s
    assert len(sug) == 1 and abs(sug[0]["startSec"] - 6.8) < 0.05 and sug[0]["clipId"] == c["id"]

    # PUT: encurta, rejeita clipe inexistente e limita ao tamanho do clipe
    ev = [dict(sug[0], endSec=60.0), {"id": "x", "startSec": 1, "endSec": 2, "clipId": "naoexiste"}]
    saved = client.put(f"/projects/{pid}/broll", json={"events": ev}).json()["brollEvents"]
    assert len(saved) == 1 and saved[0]["endSec"] <= sug[0]["startSec"] + c["durationSec"] + 0.01
    client.put(f"/projects/{pid}/broll", json={"events": [dict(sug[0], endSec=sug[0]["startSec"] + 2.0)]})

    outs = {}
    for name, on in (("sem", False), ("com", True)):
        client.patch(f"/projects/{pid}", json={"settings": {"brollEnabled": on, "zoomMode": "off", "captionMode": "traditional"}})
        client.post(f"/projects/{pid}/export")
        p = wait(client, pid)
        assert p["status"] == "ready", p["errorMessage"]
        outs[name] = tmp_path / f"{name}.mp4"
        outs[name].write_bytes(client.get(f"/projects/{pid}/download").content)
    r, g, b = _pixel(outs["com"], 7.5)
    assert r > 200 and g < 60 and b < 60, (r, g, b)  # no B-roll: o clipe vermelho cobre a imagem
    r2, g2, _ = _pixel(outs["com"], 3.0)
    assert not (r2 > 200 and g2 < 60)  # fora do B-roll: vídeo normal
    assert not (_pixel(outs["sem"], 7.5)[0] > 200 and _pixel(outs["sem"], 7.5)[1] < 60)  # desligado: sem B-roll
    assert abs(float(ffprobe(outs["com"])["format"]["duration"]) - float(ffprobe(outs["sem"])["format"]["duration"])) < 0.2

    # apagar o clipe da biblioteca o remove dos projetos
    assert client.delete(f"/library/broll/{c['id']}").status_code == 204
    assert client.get(f"/projects/{pid}").json()["brollEvents"] == []
    assert client.get("/library/broll").json() == []
    client.delete(f"/projects/{pid}")
