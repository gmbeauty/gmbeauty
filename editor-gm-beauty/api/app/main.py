"""Backend do Editor GM Beauty (FastAPI)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, jobs
from .db import init_db
from .errors import setup_logging
from .routers import projects


@asynccontextmanager
async def lifespan(_: FastAPI):
    config.ensure_dirs()
    setup_logging()
    init_db()
    jobs.recover_interrupted()
    yield


app = FastAPI(title="Editor GM Beauty API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
