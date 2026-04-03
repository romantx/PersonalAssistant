import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Ensure the DB is placed in the backend root regardless of execution path
DB_PATH = Path(__file__).parent.parent / "agent_memory.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

from sqlalchemy import event

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_size=5,
    max_overflow=10
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Enforce IMMEDIATE transactions globally for SQLite to prevent deadlocks
@event.listens_for(engine, "begin")
def do_begin(conn):
    conn.exec_driver_sql("BEGIN IMMEDIATE")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
