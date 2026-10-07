from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from . import config


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    # Hoje há um único usuário ("local"). Já guardamos o dono para o futuro login.
    owner_id: Mapped[str] = mapped_column(String, default="local", index=True)
    name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="draft")  # draft|processing|ready|error
    stage: Mapped[str | None] = mapped_column(String, nullable=True)  # etapa atual
    progress: Mapped[float] = mapped_column(Float, default=0)  # 0-100 (exportação)
    content_type: Mapped[str] = mapped_column(String, default="ugc")
    style: Mapped[str] = mapped_column(String, default="gm-clean")

    original_name: Mapped[str] = mapped_column(String, default="")
    ext: Mapped[str] = mapped_column(String, default=".mp4")
    duration_sec: Mapped[float] = mapped_column(Float, default=0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=True)

    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    captions: Mapped[list] = mapped_column(JSON, default=list)
    silences: Mapped[list] = mapped_column(JSON, default=list)
    sfx_events: Mapped[list | None] = mapped_column(JSON, default=list)  # efeitos sonoros posicionados
    broll_events: Mapped[list | None] = mapped_column(JSON, default=list)  # B-roll posicionados
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    has_output: Mapped[bool] = mapped_column(Boolean, default=False)

    error_message: Mapped[str | None] = mapped_column(String, nullable=True)  # mostrado ao usuário
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # só para debug

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class SfxSound(Base):
    """Efeito sonoro da Biblioteca GM (arquivo enviado por você)."""

    __tablename__ = "sfx_sounds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    owner_id: Mapped[str] = mapped_column(String, default="local", index=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, default="outro")  # transicao|destaque|oferta|outro
    ext: Mapped[str] = mapped_column(String, default=".mp3")
    duration_sec: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class BrollClip(Base):
    """Clipe de B-roll da Biblioteca GM (vídeo seu de produto/aplicação)."""

    __tablename__ = "broll_clips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    owner_id: Mapped[str] = mapped_column(String, default="local", index=True)
    name: Mapped[str] = mapped_column(String)
    tag: Mapped[str] = mapped_column(String, default="")  # como o produto é falado; variações separadas por vírgula
    ext: Mapped[str] = mapped_column(String, default=".mp4")
    duration_sec: Mapped[float] = mapped_column(Float, default=0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DictionaryTerm(Base):
    """Dicionário GM Beauty (marcas, produtos, nomes). Estrutura pronta; a tela vem depois."""

    __tablename__ = "dictionary_terms"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    owner_id: Mapped[str] = mapped_column(String, default="local", index=True)
    term: Mapped[str] = mapped_column(String)  # forma correta, ex.: "Ruby Rose"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
config.ensure_dirs()
engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def _add_missing_columns() -> None:
    """Migração simples: bancos criados em fases anteriores ganham as colunas novas."""
    insp = inspect(engine)
    for table in Base.metadata.sorted_tables:
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name not in existing:
                ddl = col.type.compile(engine.dialect)
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl}"))


def init_db() -> None:
    Base.metadata.create_all(engine)
    _add_missing_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
