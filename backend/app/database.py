from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Use SQLite for development
# 确保数据库文件路径正确
db_path = os.path.join(os.path.dirname(__file__), "test.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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