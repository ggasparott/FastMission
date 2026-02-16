"""
Endpoints da API FastAPI
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from uuid import UUID

from .database import get_db
from .models import Lote, ItemCadastral, StatusLote, StatusValidacao
from .schemas import (
    UploadResponse, 
    LoteResponse, 
    LoteStatusResponse, 
    ItemCadastralResponse
)
from .tasks import processar_lote_task

router = APIRouter()


def parsear_csv(conteudo: bytes) -> List[dict]:
    """
    Parse CSV com suporte a múltiplos encodings (UTF-8 e Latin-1)
    """
    # Tentar UTF-8 primeiro
    try:
        texto = conteudo.decode('utf-8')
    except UnicodeDecodeError:
        # Fallback para Latin-1 (comum em sistemas brasileiros legados)
        texto = conteudo.decode('latin-1')
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(texto))
    linhas = list(reader)
    
    # Validar colunas obrigatórias
    if not linhas:
        raise ValueError("CSV vazio")
    
    primeira_linha = linhas[0]
    if 'descricao' not in primeira_linha or 'ncm' not in primeira_linha:
        raise ValueError("CSV deve conter colunas 'descricao' e 'ncm'")
    
    return linhas


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload de CSV com produtos.
    Retorna 202 Accepted e processa em background.
    
    ⚠️ REGRA DE OURO: NUNCA processar aqui! Apenas salvar e agendar.
    """
    # Validar arquivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV são aceitos")
    
    # Ler e parsear CSV
    conteudo = await file.read()
    
    try:
        linhas = parsear_csv(conteudo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar CSV: {str(e)}")
    
    # Criar Lote no banco
    lote = Lote(
        arquivo_nome=file.filename,
        status=StatusLote.PENDENTE,
        total_itens=len(linhas)
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    
    # Criar todos os itens (bulk insert)
    itens = []
    for linha in linhas:
        item = ItemCadastral(
            lote_id=lote.id,
            descricao=linha['descricao'].strip(),
            ncm_original=linha['ncm'].strip(),  # String!
            status_validacao=StatusValidacao.PENDENTE
        )
        itens.append(item)
    
    db.bulk_save_objects(itens)
    db.commit()
    
    # Agendar processamento (enviar para Redis via Celery)
    processar_lote_task.delay(str(lote.id))
    
    return UploadResponse(
        lote_id=lote.id,
        status="PENDENTE",
        mensagem="Upload recebido. Processando em background...",
        total_itens=len(linhas)
    )


@router.get("/lotes/{lote_id}/status", response_model=LoteStatusResponse)
async def get_status(lote_id: UUID, db: Session = Depends(get_db)):
    """
    Checar status de processamento de um lote.
    Frontend chama isso a cada 3 segundos (polling).
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    # Calcular progresso
    itens_processados = db.query(ItemCadastral).filter(
        ItemCadastral.lote_id == lote_id,
        ItemCadastral.status_validacao != StatusValidacao.PENDENTE
    ).count()
    
    progresso = (itens_processados / lote.total_itens * 100) if lote.total_itens > 0 else 0
    
    return LoteStatusResponse(
        status=lote.status.value,
        progresso=progresso,
        total_itens=lote.total_itens,
        itens_processados=itens_processados
    )


@router.get("/lotes/{lote_id}/itens", response_model=List[ItemCadastralResponse])
async def listar_itens(
    lote_id: UUID, 
    apenas_divergentes: bool = False,
    db: Session = Depends(get_db)
):
    """
    Listar itens de um lote.
    Opcionalmente filtrar apenas itens com divergências.
    """
    query = db.query(ItemCadastral).filter(ItemCadastral.lote_id == lote_id)
    
    if apenas_divergentes:
        query = query.filter(ItemCadastral.status_validacao == StatusValidacao.DIVERGENTE)
    
    itens = query.all()
    
    return itens


@router.get("/lotes", response_model=List[LoteResponse])
async def listar_lotes(db: Session = Depends(get_db)):
    """
    Listar todos os lotes (mais recentes primeiro)
    """
    lotes = db.query(Lote).order_by(Lote.data_upload.desc()).all()
    return lotes
