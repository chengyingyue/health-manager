"""
数据库连接配置模块
================

本模块负责配置 SQLAlchemy 数据库连接，创建 SessionLocal 工厂，并提供获取数据库会话的依赖函数。

Attributes:
    SQLALCHEMY_DATABASE_URL (str): 数据库连接 URL，默认使用 SQLite。
    engine (Engine): SQLAlchemy 数据库引擎实例。
    SessionLocal (sessionmaker): 数据库会话工厂。
    Base (DeclarativeMeta): SQLAlchemy 声明式基类。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./health_manager.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    获取数据库会话。

    该函数作为一个生成器，用于 FastAPI 的依赖注入系统。
    它创建一个新的数据库会话，在使用完毕后自动关闭。

    Yields:
        Session: SQLAlchemy 数据库会话对象。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
