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
    """Response de cada item cadastral"""
    id: UUID
    descricao: str
    ncm_original: str
    ncm_sugerido: Optional[str] = None
    status_validacao: str
    motivo_divergencia: Optional[str] = None
    confianca_ai: Optional[float] = None
    data_processamento: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response imediato do upload (202 Accepted)"""
    lote_id: UUID
    status: str
    mensagem: str
    total_itens: int
