import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

os.makedirs(settings.data_dir, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.exec_driver_sql(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS movies_fts USING fts5(
                title, sort_title, year,
                content='movies', content_rowid='id',
                tokenize='unicode61'
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TRIGGER IF NOT EXISTS movies_ai AFTER INSERT ON movies BEGIN
                INSERT INTO movies_fts(rowid, title, sort_title, year)
                VALUES (new.id, new.title, new.sort_title, new.year);
            END
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TRIGGER IF NOT EXISTS movies_ad AFTER DELETE ON movies BEGIN
                INSERT INTO movies_fts(movies_fts, rowid, title, sort_title, year)
                VALUES ('delete', old.id, old.title, old.sort_title, old.year);
            END
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TRIGGER IF NOT EXISTS movies_au AFTER UPDATE ON movies BEGIN
                INSERT INTO movies_fts(movies_fts, rowid, title, sort_title, year)
                VALUES ('delete', old.id, old.title, old.sort_title, old.year);
                INSERT INTO movies_fts(rowid, title, sort_title, year)
                VALUES (new.id, new.title, new.sort_title, new.year);
            END
            """
        )
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()