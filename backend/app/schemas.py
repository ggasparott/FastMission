"""
Pydantic Schemas - Validação de entrada/saída da API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LoteResponse(BaseModel):
    """Response ao fazer upload de CSV"""
    id: UUID
    status: str
    total_itens: int
    arquivo_nome: str
    data_upload: datetime

    class Config:
        from_attributes = True


class LoteStatusResponse(BaseModel):
    """Response do endpoint de status"""
    status: str
    progresso: float
    total_itens: int
    itens_processados: int


class ItemCadastralResponse(BaseModel):
    """Response de cada item cadastral - Reforma Tributária"""
    id: UUID
    descricao: str
    
    # NCM
    ncm_original: str
    ncm_sugerido: Optional[str] = None
    
    # CEST
    cest_original: Optional[str] = None
    cest_sugerido: Optional[str] = None
    cest_obrigatorio: Optional[str] = None
    
    # Status
    status_validacao: str
    motivo_divergencia: Optional[str] = None
    confianca_ai: Optional[float] = None
    
    # Reforma Tributária (IBS/CBS)
    regime_tributario: Optional[str] = None
    aliquota_ibs: Optional[float] = None
    aliquota_cbs: Optional[float] = None
    
    # Benefícios Fiscais
    possui_beneficio_fiscal: Optional[str] = None
    tipo_beneficio: Optional[str] = None
    artigo_legal: Optional[str] = None
    
    data_processamento: Optional[datetime] = None

    class Config:
        from_attributes = True


class BeneficiosFiscaisResponse(BaseModel):
    """Response com resumo de benefícios fiscais detectados"""
    total_itens: int
    itens_com_beneficio: int
    economia_potencial_ibs: float
    beneficios: list[ItemCadastralResponse]


class DivergenciasReformaResponse(BaseModel):
    """Response com divergências específicas da Reforma Tributária"""
    total_divergencias: int
    cest_faltando: int
    regime_invalido: int
    itens: list[ItemCadastralResponse]


class UploadResponse(BaseModel):
    """Response imediato do upload (202 Accepted)"""
    lote_id: UUID
    status: str
    mensagem: str
    total_itens: int
