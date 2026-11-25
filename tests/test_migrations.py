"""
tests/test_migrations.py
------------------------
Runs Alembic migrations against a throwaway SQLite file: upgrade to head,
downgrade one step, upgrade again (docs/workflow.md, section 4).

The repo has no baseline revision, so the tables that migrations depend on
(users, projects, tasks, tags) are created from the models first.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine

import app.models  # noqa: F401  (registers every model on Base.metadata)
from alembic import command
from app.core import config as app_config
from app.db.session import Base

ROOT = Path(__file__).resolve().parents[1]
MIGRATED_TABLES = {"task_comments"}


def tables(db_file: Path) -> set[str]:
    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        return {name for (name,) in rows}


@pytest.fixture
def alembic_config(tmp_path, monkeypatch) -> tuple[Config, Path]:
    db_file = tmp_path / "migrations.db"
    # Tables that existed before the first migration.
    engine = create_engine(f"sqlite:///{db_file}")
    pre_existing = [
        t for t in Base.metadata.sorted_tables if t.name not in MIGRATED_TABLES
    ]
    Base.metadata.create_all(engine, tables=pre_existing)
    engine.dispose()

    # alembic/env.py reads the URL from settings, so point settings at the file.
    monkeypatch.setattr(
        app_config.settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_file.as_posix()}"
    )
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg, db_file


def test_task_comments_migration_upgrades_downgrades_and_upgrades_again(
    alembic_config,
) -> None:
    cfg, db_file = alembic_config

    command.upgrade(cfg, "head")
    assert "task_comments" in tables(db_file)

    command.downgrade(cfg, "-1")
    assert "task_comments" not in tables(db_file)

    command.upgrade(cfg, "head")
    assert "task_comments" in tables(db_file)
