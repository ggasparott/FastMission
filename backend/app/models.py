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
    regime_empresa = Column(String(30), nullable=True)  # SIMPLES, LUCRO_PRESUMIDO, LUCRO_REAL
    uf_origem = Column(String(2), nullable=True)
    uf_destino = Column(String(2), nullable=True)
    cnae_principal = Column(String(10), nullable=True)
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
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=True)  # Nullable: item pode existir sem lote
    
    # ========== BLOCO 1: IDENTIFICAÇÃO ==========
    sku = Column(String(50), nullable=True, index=True)         # Código interno da empresa
    ean_gtin = Column(String(14), nullable=True, index=True)    # Código de barras (8, 12, 13 ou 14 dígitos)
    descricao = Column(String(500), nullable=False)             # Descrição curta (ex: "Chocolate ao Leite 200g")
    descricao_longa = Column(Text, nullable=True)               # Descrição detalhada para NF-e
    
    # ========== BLOCO 2: CLASSIFICAÇÃO FISCAL ==========
    ncm_original = Column(String(20), nullable=False)           # NCM do cadastro (8 dígitos, ex: "18063110")
    cest_original = Column(String(10), nullable=True)           # CEST do cadastro (7 dígitos, ex: "1704600")
    cfop = Column(String(4), nullable=True)                     # CFOP padrão (ex: "5102" = venda interna)
    cfop_sugerido = Column(String(4), nullable=True)
    
    # ========== BLOCO 3: TRIBUTAÇÃO ==========
    origem_produto = Column(Integer, nullable=True)             # 0=Nacional, 1=Estrangeira importação direta, 2=Estrangeira mercado interno... até 8
    cst_csosn = Column(String(4), nullable=True)                # CST (3 dígitos) ou CSOSN (4 dígitos Simples Nacional)
    cst_csosn_sugerido = Column(String(4), nullable=True)
    aliquota_icms = Column(Float, nullable=True)                # Alíquota ICMS % (ex: 18.0, 12.0, 7.0)
    aliquota_pis = Column(Float, nullable=True)                 # Alíquota PIS % (ex: 1.65)
    aliquota_cofins = Column(Float, nullable=True)              # Alíquota COFINS % (ex: 7.60)
    possui_st = Column(String(3), nullable=True)                # "SIM" ou "NAO" - Substituição Tributária
    quantidade = Column(Float, nullable=True)
    valor_unitario = Column(Float, nullable=True)
    
    # Resultado da IA - NCM
    ncm_sugerido = Column(String(20), nullable=True)
    status_validacao = Column(
        Enum(StatusValidacao), 
        default=StatusValidacao.PENDENTE, 
        nullable=False
    )
    motivo_divergencia = Column(Text, nullable=True)
    justificativa_ai = Column(Text, nullable=True)
    confianca_ai = Column(Float, nullable=True)  # 0-100
    
    #REFORMA TRIBUTÁRIA - IBS/CBS
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

    # Comparativo fiscal
    carga_atual_percentual = Column(Float, nullable=True)
    carga_reforma_percentual = Column(Float, nullable=True)
    valor_base_calculo = Column(Float, nullable=True)
    valor_atual_estimado = Column(Float, nullable=True)
    valor_reforma_estimado = Column(Float, nullable=True)
    diferenca_absoluta = Column(Float, nullable=True)
    diferenca_percentual = Column(Float, nullable=True)
    faixa_incerteza_min = Column(Float, nullable=True)
    faixa_incerteza_max = Column(Float, nullable=True)
    
    data_processamento = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamento N:1 com Lote
    lote = relationship("Lote", back_populates="itens")


class NCMOficial(Base):
    """Tabela de referência oficial de NCM para validação."""
    __tablename__ = "ncm_oficiais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(8), nullable=False, unique=True, index=True)
    descricao = Column(Text, nullable=False)
