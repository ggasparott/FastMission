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
    Foco: Saneamento Cadastral para Reforma Tributária (IBS/CBS)
    """
    __tablename__ = "itens_cadastrais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=False)
    
    # Dados originais do CSV
    descricao = Column(String(500), nullable=False)
    ncm_original = Column(String(20), nullable=False)  # ⚠️ STRING, não INT!
    cest_original = Column(String(10), nullable=True)  # CEST do cadastro atual
    
    # Resultado da IA - NCM
    ncm_sugerido = Column(String(20), nullable=True)
    status_validacao = Column(
        Enum(StatusValidacao), 
        default=StatusValidacao.PENDENTE, 
        nullable=False
    )
    motivo_divergencia = Column(Text, nullable=True)
    confianca_ai = Column(Float, nullable=True)  # 0-100
    
    # 🆕 REFORMA TRIBUTÁRIA - IBS/CBS
    cest_sugerido = Column(String(10), nullable=True)
    cest_obrigatorio = Column(String, nullable=True)  # "SIM", "NAO", "VERIFICAR"
    
    # Regime tributário
    regime_tributario = Column(String(50), nullable=True)  # NORMAL, ALIQUOTA_REDUZIDA, CASHBACK, IMUNE
    
    # Alíquotas sugeridas (%)
    aliquota_ibs = Column(Float, nullable=True)  # Ex: 26.5%
    aliquota_cbs = Column(Float, nullable=True)  # Ex: 0.0%
    
    # Benefícios fiscais
    possui_beneficio_fiscal = Column(String, nullable=True)  # "SIM", "NAO", "POSSIVEL"
    tipo_beneficio = Column(String(200), nullable=True)  # "Cesta básica", "Medicamentos", etc
    artigo_legal = Column(String(100), nullable=True)  # "Art. 18, §1º", etc
    
    data_processamento = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamento N:1 com Lote
    lote = relationship("Lote", back_populates="itens")
