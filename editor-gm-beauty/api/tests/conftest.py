import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

_tmp = tempfile.mkdtemp(prefix="gmb-test-")
os.environ["DATA_DIR"] = _tmp
os.environ["TRANSCRIBER"] = "fake"

# Fala simulada: 3 trechos de som e 2 pausas (2–4 s e 6–6,7 s) no áudio de teste.
WORDS = [
    {"w": "Você", "s": 0.1, "e": 0.5}, {"w": "ainda", "s": 0.5, "e": 0.9}, {"w": "aplica", "s": 0.9, "e": 1.4},
    {"w": "base", "s": 1.4, "e": 1.9},
    {"w": "Então", "s": 4.1, "e": 4.6}, {"w": "olha", "s": 4.6, "e": 5.0}, {"w": "R$", "s": 5.0, "e": 5.3},
    {"w": "29,90", "s": 5.3, "e": 5.9},
    {"w": "Acabamento", "s": 6.8, "e": 7.6}, {"w": "natural.", "s": 7.6, "e": 8.8},
]
(Path(_tmp) / "fake.json").write_text(json.dumps(WORDS), encoding="utf-8")
os.environ["FAKE_TRANSCRIPT"] = str(Path(_tmp) / "fake.json")


def make_video(path: Path, size: str = "1280x720", seconds: int = 10) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"testsrc=size={size}:rate=30",
         "-f", "lavfi", "-i", "sine=f=440:sample_rate=44100",
         "-af", "volume=enable='between(t,2,4)+between(t,6,6.7)':volume=0",
         "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)],
        check=True,
    )


@pytest.fixture(scope="session")
def landscape_video(tmp_path_factory):
    p = tmp_path_factory.mktemp("v") / "teste.mp4"
    make_video(p)
    return p


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
