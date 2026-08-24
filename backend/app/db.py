from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text

from .config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upgrade_schema():
    with engine.begin() as conn:
        for table, column, ddl in [
            ("import_batches", "channel", "VARCHAR(120)"),
            ("staging_rows", "in_transit", "FLOAT"),
            ("snapshot_rows", "in_transit", "FLOAT"),
        ]:
            columns = {
                row[1]
                for row in conn.execute(
                    text(f"PRAGMA table_info({table})")
                ).fetchall()
            }
            if column not in columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
