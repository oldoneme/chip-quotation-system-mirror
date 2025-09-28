from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings as runtime_settings


def _build_engine_url() -> str:
    """返回标准化的数据库连接URL"""
    return runtime_settings.DATABASE_URL


def _build_connect_args(url: str) -> dict:
    """针对SQLite提供必要的连接参数"""
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


SQLALCHEMY_DATABASE_URL = _build_engine_url()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=_build_connect_args(SQLALCHEMY_DATABASE_URL),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session to endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models here to ensure they are registered
    from . import models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize sample data
    from .init_data import init_db_data
    db = SessionLocal()
    try:
        init_db_data(db)
    finally:
        db.close()
