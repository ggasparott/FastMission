"""
Modelos ORM - Tabelas do banco de dados
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from .database import Base


class StatusLote(str, enum.Enum):
    """Status do processamento de um lote"""
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    ERRO = "ERRO"


class StatusValidacao(str, enum.Enum):
    """Status da validação de um item"""
    PENDENTE = "PENDENTE"
    VALIDO = "VALIDO"
    DIVERGENTE = "DIVERGENTE"


class Lote(Base):
    """
    Representa um batch de upload CSV
    """
    __tablename__ = "lotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arquivo_nome = Column(String(255), nullable=False)
    status = Column(Enum(StatusLote), default=StatusLote.PENDENTE, nullable=False)
    total_itens = Column(Integer, default=0, nullable=False)
    data_upload = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento 1:N com ItemCadastral
    itens = relationship("ItemCadastral", back_populates="lote", cascade="all, delete-orphan")


class ItemCadastral(Base):
    """
    Cada linha do CSV é um ItemCadastral
    """
    __tablename__ = "itens_cadastrais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=False)
    
    # Dados originais do CSV
    descricao = Column(String(500), nullable=False)
    ncm_original = Column(String(20), nullable=False)  # ⚠️ STRING, não INT!
    
    # Resultado da IA
    ncm_sugerido = Column(String(20), nullable=True)
    status_validacao = Column(
        Enum(StatusValidacao), 
        default=StatusValidacao.PENDENTE, 
        nullable=False
    )
    motivo_divergencia = Column(Text, nullable=True)
    confianca_ai = Column(Float, nullable=True)  # 0-100
    
    data_processamento = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamento N:1 com Lote
    lote = relationship("Lote", back_populates="itens")
