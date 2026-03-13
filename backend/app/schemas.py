"""
Pydantic Schemas - Validação de entrada/saída da API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# =============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO (reutilizadas por Create e Update)
# =============================================================================

def _val_ean(v):
    if v is None:
        return None
    v = v.strip()
    if not v.isdigit():
        raise ValueError("EAN/GTIN deve conter apenas dígitos numéricos")
    if len(v) not in (8, 12, 13, 14):
        raise ValueError("EAN/GTIN deve ter 8, 12, 13 ou 14 dígitos numéricos")
    return v

def _val_ncm(v):
    if v is None:
        return None
    v = v.strip().replace(".", "")
    if not v.isdigit() or len(v) != 8:
        raise ValueError("NCM deve ter exatamente 8 dígitos numéricos")
    return v

def _val_cest(v):
    if v is None:
        return None
    v = v.strip().replace(".", "")
    if not v.isdigit() or len(v) != 7:
        raise ValueError("CEST deve ter exatamente 7 dígitos numéricos")
    return v

def _val_cfop(v):
    if v is None:
        return None
    if not v.isdigit() or len(v) != 4:
        raise ValueError("CFOP inválido")
    if v[0] not in ("1", "2", "3", "5", "6", "7"):
        raise ValueError("CFOP inválido")
    return v

def _val_cst_csosn(v):
    if v is None:
        return None
    if not v.isdigit():
        raise ValueError("Tem que ser apenas dígitos numéricos")
    if len(v) not in (3, 4):
        raise ValueError("CST deve ter 3 dígitos ou CSOSN deve ter 4 dígitos")
    return v

def _val_possui_st(v):
    if v is None:
        return None
    v = v.upper()
    if v not in ("SIM", "NAO"):
        raise ValueError("possui_st deve ser 'SIM' ou 'NAO'")
    return v


# =============================================================================
# SCHEMAS DE ITEM - CRUD Manual (Cadastro no Varejo)
# =============================================================================

class ItemCreateSchema(BaseModel):
    """
    Schema para CRIAR um item manualmente (POST /api/itens).
    
    Regras de validação que VOCÊ deve implementar:
    - sku: opcional, mas se informado deve ser único (validar no service)
    - ean_gtin: deve ter 8, 12, 13 ou 14 dígitos numéricos
    - ncm: exatamente 8 dígitos numéricos
    - cest: exatamente 7 dígitos numéricos (se informado)
    - cfop: exatamente 4 dígitos numéricos
    - origem_produto: inteiro de 0 a 8
    - cst_csosn: 3 dígitos (CST) ou 4 dígitos (CSOSN)
    - aliquotas: entre 0.0 e 100.0
    """
    
    # --- Bloco 1: Identificação ---
    sku: Optional[str] = Field(None, max_length=50, examples=["SKU-001"])
    ean_gtin: Optional[str] = Field(None, examples=["7891234567890"])
    descricao: str = Field(..., min_length=3, max_length=500, examples=["Chocolate ao Leite 200g"])
    descricao_longa: Optional[str] = Field(None, examples=["Chocolate ao leite em barra, peso líquido 200g"])
    
    # --- Bloco 2: Classificação Fiscal ---
    ncm: str = Field(..., examples=["18063110"])
    cest: Optional[str] = Field(None, examples=["1704600"])
    cfop: Optional[str] = Field(None, examples=["5102"])
    
    # --- Bloco 3: Tributação ---
    origem_produto: Optional[int] = Field(None, ge=0, le=8, examples=[0])
    cst_csosn: Optional[str] = Field(None, examples=["060"])
    aliquota_icms: Optional[float] = Field(None, ge=0, le=100, examples=[18.0])
    aliquota_pis: Optional[float] = Field(None, ge=0, le=100, examples=[1.65])
    aliquota_cofins: Optional[float] = Field(None, ge=0, le=100, examples=[7.60])
    possui_st: Optional[str] = Field(None, examples=["SIM"])

    # TODO: Implemente os validators abaixo seguindo a lógica indicada
    
    @field_validator("ean_gtin")
    @classmethod
    def validar_ean(cls, v):       return _val_ean(v)

    @field_validator("ncm")
    @classmethod
    def validar_ncm(cls, v):       return _val_ncm(v)

    @field_validator("cest")
    @classmethod
    def validar_cest(cls, v):      return _val_cest(v)

    @field_validator("cfop")
    @classmethod
    def validar_cfop(cls, v):      return _val_cfop(v)

    @field_validator("cst_csosn")
    @classmethod
    def validar_cst_csosn(cls, v): return _val_cst_csosn(v)

    @field_validator("possui_st")
    @classmethod
    def validar_possui_st(cls, v): return _val_possui_st(v)

class ItemUpdateSchema(BaseModel):
    """
    Schema para ATUALIZAR um item (PUT /api/itens/{id}).
    
    Todos os campos são Optional — só altera o que foi enviado.
    Mesmas regras de validação do ItemCreateSchema.
    """
    
    # : Declare todos os campos como Optional (mesmos do ItemCreateSchema)
    # Dica: copie os campos do ItemCreateSchema, mas mude "descricao" e "ncm" para Optional também
    # 
    # sku: Optional[str] = Field(None, max_length=50)
    # ean_gtin: Optional[str] = None
    # descricao: Optional[str] = Field(None, min_length=3, max_length=500)
    # ... continue para todos os campos ...
    #
    # Reutilize os MESMOS validators (copie ou crie uma função auxiliar)
    
    sku: Optional[str] = Field(None, max_length=50, examples=["SKU-001"])
    ean_gtin: Optional[str] = Field(None, examples=["7891234567890"])
    descricao: Optional[str] = Field(None, min_length=3, max_length=500, examples=["Chocolate ao Leite 200g"])
    descricao_longa: Optional[str] = Field(None, examples=["Chocolate ao leite em barra, peso líquido 200g"])
    
    # --- Bloco 2: Classificação Fiscal ---
    ncm: Optional[str] = Field(None, examples=["18063110"])
    cest: Optional[str] = Field(None, examples=["1704600"])
    cfop: Optional[str] = Field(None, examples=["5102"])
    
    # --- Bloco 3: Tributação ---
    origem_produto: Optional[int] = Field(None, ge=0, le=8, examples=[0])
    cst_csosn: Optional[str] = Field(None, examples=["060"])
    aliquota_icms: Optional[float] = Field(None, ge=0, le=100, examples=[18.0])
    aliquota_pis: Optional[float] = Field(None, ge=0, le=100, examples=[1.65])
    aliquota_cofins: Optional[float] = Field(None, ge=0, le=100, examples=[7.60])
    possui_st: Optional[str] = Field(None, examples=["SIM"])

    # Validators — reutilizam as mesmas funções auxiliares do ItemCreateSchema
    @field_validator("ean_gtin")
    @classmethod
    def validar_ean(cls, v):       return _val_ean(v)

    @field_validator("ncm")
    @classmethod
    def validar_ncm(cls, v):       return _val_ncm(v)

    @field_validator("cest")
    @classmethod
    def validar_cest(cls, v):      return _val_cest(v)

    @field_validator("cfop")
    @classmethod
    def validar_cfop(cls, v):      return _val_cfop(v)

    @field_validator("cst_csosn")
    @classmethod
    def validar_cst_csosn(cls, v): return _val_cst_csosn(v)

    @field_validator("possui_st")
    @classmethod
    def validar_possui_st(cls, v): return _val_possui_st(v)


# =============================================================================
# SCHEMAS EXISTENTES (não alterar)
# =============================================================================


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
    
    # Identificação
    sku: Optional[str] = None
    ean_gtin: Optional[str] = None
    descricao_longa: Optional[str] = None
    
    # NCM
    ncm_original: str
    ncm_sugerido: Optional[str] = None
    
    # Classificação Fiscal
    cest_original: Optional[str] = None
    cest_sugerido: Optional[str] = None
    cest_obrigatorio: Optional[str] = None
    cfop: Optional[str] = None
    
    # Tributação
    origem_produto: Optional[int] = None
    cst_csosn: Optional[str] = None
    aliquota_icms: Optional[float] = None
    aliquota_pis: Optional[float] = None
    aliquota_cofins: Optional[float] = None
    possui_st: Optional[str] = None
    
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
