"""
Configuração do banco de dados PostgreSQL com SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexão do PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fastmission:Fastdb2026@postgres:5432/cadastral_db "
)

# Engine do SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco.
    Usar com Depends() nos endpoints FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
