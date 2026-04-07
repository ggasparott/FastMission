"""
Endpoints da API FastAPI
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List
import csv
import io
import json
import subprocess
import os
from uuid import UUID

from .database import get_db
from .models import Lote, ItemCadastral, StatusLote, StatusValidacao
from .schemas import (
    AnaliseItemResponse,
    AgentQueryRequest,
    UploadResponse,
    LoteResponse,
    LoteStatusResponse,
    ItemCadastralResponse,
    ItemCreateSchema,
    ItemUpdateSchema,
    ComparativoFiscalResponse,
)
from .tasks import processar_lote_task
from .services.item_service import ItemService, ItemNotFoundException, ItemValidationError

router = APIRouter()


def parsear_csv(conteudo: bytes) -> List[dict]:
    """
    Parse CSV com suporte a múltiplos encodings (UTF-8 e Latin-1)
    Com validações robustas de tamanho e formato
    """
    # Validar tamanho (máximo 50MB)
    MAX_SIZE = 50 * 1024 * 1024
    if len(conteudo) > MAX_SIZE:
        raise ValueError(f"Arquivo muito grande. Máximo: 50MB")
    
    if len(conteudo) == 0:
        raise ValueError("Arquivo vazio")
    
    # Tentar UTF-8 primeiro
    try:
        texto = conteudo.decode('utf-8')
    except UnicodeDecodeError:
        # Fallback para Latin-1 (comum em sistemas brasileiros legados)
        try:
            texto = conteudo.decode('latin-1')
        except:
            raise ValueError("Erro ao decodificar arquivo. Use UTF-8 ou Latin-1")
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(texto))
    linhas = list(reader)
    
    # Validar colunas obrigatórias
    if not linhas:
        raise ValueError("CSV vazio")
    
    primeira_linha = linhas[0]
    if 'descricao' not in primeira_linha or 'ncm' not in primeira_linha:
        colunas_encontradas = ', '.join(primeira_linha.keys())
        raise ValueError(f"CSV deve conter colunas 'descricao' e 'ncm'. Encontrado: {colunas_encontradas}")
    
    # Validar limite de linhas
    if len(linhas) > 10000:
        raise ValueError(f"Máximo de 10.000 itens por lote. Encontrado: {len(linhas)}")
    
    # Validar dados linha por linha
    for idx, linha in enumerate(linhas, start=2):  # linha 1 = header
        if not linha.get('descricao', '').strip():
            raise ValueError(f"Linha {idx}: campo 'descricao' é obrigatório")
        
        ncm = linha.get('ncm', '').strip().replace('.', '').replace('-', '')
        if ncm and len(ncm) != 8:
            raise ValueError(f"Linha {idx}: NCM deve ter 8 dígitos. Encontrado: '{ncm}'")

        if linha.get('quantidade'):
            try:
                if float(linha.get('quantidade')) < 0:
                    raise ValueError()
            except Exception:
                raise ValueError(f"Linha {idx}: quantidade inválida")

        if linha.get('valor_unitario'):
            try:
                if float(linha.get('valor_unitario')) < 0:
                    raise ValueError()
            except Exception:
                raise ValueError(f"Linha {idx}: valor_unitario inválido")
    
    return linhas


@router.post("/import-csv", response_model=UploadResponse, status_code=202)
async def upload_csv(
    file: UploadFile = File(...),
    regime_empresa: str = Form(...),
    uf_origem: str = Form(...),
    uf_destino: str = Form(...),
    cnae_principal: str = Form(...),
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

    regime_empresa = regime_empresa.strip().upper()
    uf_origem = uf_origem.strip().upper()
    uf_destino = uf_destino.strip().upper()
    cnae_principal = cnae_principal.strip()

    regimes_validos = {"SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"}
    if regime_empresa not in regimes_validos:
        raise HTTPException(status_code=400, detail="regime_empresa inválido")

    if len(uf_origem) != 2 or len(uf_destino) != 2:
        raise HTTPException(status_code=400, detail="UF origem/destino devem conter 2 caracteres")

    if not cnae_principal:
        raise HTTPException(status_code=400, detail="cnae_principal é obrigatório")
    
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
        total_itens=len(linhas),
        regime_empresa=regime_empresa,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        cnae_principal=cnae_principal,
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
            cest_original=linha.get('cest', '').strip() if linha.get('cest') else None,  # CEST opcional
            quantidade=float(linha.get('quantidade')) if linha.get('quantidade') else None,
            valor_unitario=float(linha.get('valor_unitario')) if linha.get('valor_unitario') else None,
            status_validacao=StatusValidacao.PENDENTE
        )
        itens.append(item)
    
    db.bulk_save_objects(itens)
    db.commit()
    
    # Agendar processamento (enviar para Redis via Celery)
    try:
        processar_lote_task.delay(str(lote.id))
    except Exception as e:
        print(f"⚠️ Erro ao enviar task para Celery: {e}")
        # Não falhar o upload - o lote foi salvo, pode ser reprocessado depois
    
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
async def listar_itens_lote(
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


@router.get("/lotes/{lote_id}/comparativo", response_model=ComparativoFiscalResponse)
async def comparativo_fiscal_lote(lote_id: UUID, db: Session = Depends(get_db)):
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")

    itens = db.query(ItemCadastral).filter(ItemCadastral.lote_id == lote_id).all()
    if not itens:
        return ComparativoFiscalResponse(
            lote_id=lote_id,
            regime_empresa=lote.regime_empresa,
            uf_origem=lote.uf_origem,
            uf_destino=lote.uf_destino,
            cnae_principal=lote.cnae_principal,
            total_itens=0,
            total_base_calculo=0,
            total_atual_estimado=0,
            total_reforma_estimado=0,
            diferenca_absoluta=0,
            diferenca_percentual=0,
            faixa_incerteza_min=0,
            faixa_incerteza_max=0,
        )

    total_base = sum((item.valor_base_calculo or 0) for item in itens)
    total_atual = sum((item.valor_atual_estimado or 0) for item in itens)
    total_reforma = sum((item.valor_reforma_estimado or 0) for item in itens)
    total_min = sum((item.faixa_incerteza_min or 0) for item in itens)
    total_max = sum((item.faixa_incerteza_max or 0) for item in itens)

    diferenca_abs = total_reforma - total_atual
    diferenca_pct = ((diferenca_abs / total_atual) * 100) if total_atual > 0 else 0

    return ComparativoFiscalResponse(
        lote_id=lote_id,
        regime_empresa=lote.regime_empresa,
        uf_origem=lote.uf_origem,
        uf_destino=lote.uf_destino,
        cnae_principal=lote.cnae_principal,
        total_itens=len(itens),
        total_base_calculo=round(total_base, 2),
        total_atual_estimado=round(total_atual, 2),
        total_reforma_estimado=round(total_reforma, 2),
        diferenca_absoluta=round(diferenca_abs, 2),
        diferenca_percentual=round(diferenca_pct, 2),
        faixa_incerteza_min=round(total_min, 2),
        faixa_incerteza_max=round(total_max, 2),
    )


@router.get("/lotes/{lote_id}/beneficios-fiscais")
async def listar_beneficios_fiscais(lote_id: UUID, db: Session = Depends(get_db)):
    """
    Lista produtos que podem ter benefício fiscal da Reforma Tributária.
    Útil para identificar economia potencial com IBS/CBS.
    """
    # Buscar itens com benefícios
    itens = db.query(ItemCadastral).filter(
        ItemCadastral.lote_id == lote_id,
        ItemCadastral.possui_beneficio_fiscal.in_(["SIM", "POSSIVEL"])
    ).all()
    
    # Calcular economia estimada (diferença entre alíquota padrão e aplicada)
    economia_total = 0.0
    for item in itens:
        if item.aliquota_ibs is not None:
            economia_total += (0.1 - item.aliquota_ibs)  # 26.5% = alíquota padrão
    
    return {
        "total_itens": len(itens),
        "itens_com_beneficio": len(itens),
        "economia_potencial_ibs": round(economia_total, 2),
        "beneficios": itens
    }


@router.get("/lotes/{lote_id}/divergencias-reforma")
async def listar_divergencias_reforma(lote_id: UUID, db: Session = Depends(get_db)):
    """
    Lista divergências específicas da Reforma Tributária:
    - CEST faltando quando obrigatório
    - Regime tributário não identificado
    - NCM incompatível com benefício fiscal
    """
    from sqlalchemy import or_
    
    # Buscar itens com problemas da Reforma
    itens = db.query(ItemCadastral).filter(
        ItemCadastral.lote_id == lote_id,
        or_(
            ItemCadastral.cest_obrigatorio == "SIM",  # CEST obrigatório
            ItemCadastral.status_validacao == StatusValidacao.DIVERGENTE
        )
    ).all()
    
    # Contar tipos de divergências
    cest_faltando = sum(1 for item in itens if item.cest_obrigatorio == "SIM" and not item.cest_original)
    regime_invalido = sum(1 for item in itens if not item.regime_tributario or item.regime_tributario == "INVALIDO")
    
    return {
        "total_divergencias": len(itens),
        "cest_faltando": cest_faltando,
        "regime_invalido": regime_invalido,
        "itens": itens
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Estatísticas gerais do sistema para o dashboard
    """
    from sqlalchemy import func
    
    try:
        total_lotes = db.query(func.count(Lote.id)).scalar() or 0
        total_itens = db.query(func.sum(Lote.total_itens)).scalar() or 0
        
        lotes_pendentes = db.query(func.count(Lote.id)).filter(
            Lote.status == StatusLote.PENDENTE
        ).scalar() or 0
        
        lotes_concluidos = db.query(func.count(Lote.id)).filter(
            Lote.status == StatusLote.CONCLUIDO
        ).scalar() or 0
        
        # Total de divergências
        total_divergencias = db.query(func.count(ItemCadastral.id)).filter(
            ItemCadastral.status_validacao == StatusValidacao.DIVERGENTE
        ).scalar() or 0
        
        # Total de benefícios detectados
        try:
            total_beneficios = db.query(func.count(ItemCadastral.id)).filter(
                ItemCadastral.possui_beneficio_fiscal.in_(["SIM", "POSSIVEL"])
            ).scalar() or 0
        except Exception:
            total_beneficios = 0
        
        return {
            "totalLotes": total_lotes,
            "totalItens": int(total_itens),
            "lotesPendentes": lotes_pendentes,
            "lotesConcluidos": lotes_concluidos,
            "divergencias": total_divergencias,
            "beneficios": total_beneficios,
            "economia": 0  # TODO: calcular economia real
        }
    except Exception as e:
        print(f"Erro em /stats: {e}")
        return {
            "totalLotes": 0,
            "totalItens": 0,
            "lotesPendentes": 0,
            "lotesConcluidos": 0,
            "divergencias": 0,
            "beneficios": 0,
            "economia": 0
        }


@router.get("/health/full")
async def full_health_check(db: Session = Depends(get_db)):
    """
    Health check completo com status de todas as dependências
    """
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        
    }
    
    # Testar banco de dados
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Testar Redis/Celery
    try:
        from .tasks import celery_app
        celery_app.broker_connection().ensure_connection(max_retries=1)
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    return health_status


# =============================================================================
# CRUD MANUAL DE ITENS - Cadastro no Varejo
# TODO: Implemente o corpo de cada endpoint
# =============================================================================

@router.post("/itens", response_model=ItemCadastralResponse, status_code=201)
async def criar_item(item: ItemCreateSchema, db: Session = Depends(get_db)):
    """
    Cria um item cadastral manualmente.
    
    Lógica:
    1. Instanciar o service:  service = ItemService(db)
    2. Chamar:                novo_item = service.criar_item(item.model_dump())
    3. Retornar:              return novo_item
    
    Tratamento de erros (try/except):
    - ItemValidationError → raise HTTPException(status_code=400, detail=str(e))
    - Exception genérica  → raise HTTPException(status_code=500, detail="Erro interno")
    """
    try:
        service = ItemService(db)
        novo_item = service.criar_item(item.model_dump())
        return novo_item
    except ItemValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erro Interno")   



@router.get("/itens", response_model=List[ItemCadastralResponse])
async def listar_itens(
    skip: int = 0,
    limit: int = 50,
    sku: str = None,
    ncm: str = None,
    cfop: str = None,
    possui_st: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista itens com filtros opcionais via query params.
    
    Exemplos de chamada:
    - GET /api/itens                          → todos (paginado)
    - GET /api/itens?sku=SKU-001              → filtrar por SKU
    - GET /api/itens?ncm=18063110&possui_st=SIM → filtrar por NCM com ST
    
    Lógica:
    1. service = ItemService(db)
    2. return service.listar_itens(skip, limit, sku, ncm, cfop, possui_st)
    """
    service = ItemService(db)
    return service.listar_itens(skip, limit, sku, ncm, cfop, possui_st)

@router.get("/itens/{item_id}", response_model=ItemCadastralResponse)
async def buscar_item(item_id: UUID, db: Session = Depends(get_db)):
    """
    Busca um item pelo ID.
    
    Lógica:
    1. service = ItemService(db)
    2. return service.buscar_item_por_id(str(item_id))
    
    Tratamento de erros:
    - ItemNotFoundException → raise HTTPException(status_code=404, detail=str(e))
    """
    try:
        service = ItemService(db)
        return service.buscar_item_por_id(str(item_id))
    except ItemNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/itens/{item_id}", response_model=ItemCadastralResponse)
async def atualizar_item(item_id: UUID, item: ItemUpdateSchema, db: Session = Depends(get_db)):
    """
    Atualiza um item existente.
    
    Lógica:
    1. service = ItemService(db)
    2. dados = item.model_dump(exclude_unset=True)
       ↑ exclude_unset=True: só envia campos que foram passados no JSON
    3. return service.atualizar_item(str(item_id), dados)
    
    Tratamento de erros:
    - ItemNotFoundException  → 404
    - ItemValidationError    → 400
    """
    try:
        service = ItemService(db)
        dados = item.model_dump(exclude_unset=True)
        return service.atualizar_item(str(item_id), dados)
    except ItemNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ItemValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erro interno")

@router.delete("/itens/{item_id}", status_code=204)
async def deletar_item(item_id: UUID, db: Session = Depends(get_db)):
    """
    Deleta um item pelo ID.
    
    Lógica:
    1. service = ItemService(db)
    2. service.deletar_item(str(item_id))
    3. return None  (204 não retorna corpo)
    
    Tratamento de erros:
    - ItemNotFoundException → 404
    """
    try:
        service = ItemService(db)
        service.deletar_item(str(item_id))
        return None
    except ItemNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

# =============================================================================
# ENDPOINTS DE ANÁLISE IA - Reforma Tributária
# =============================================================================

@router.get("/itens/{item_id}/analise", response_model=AnaliseItemResponse)
async def get_analise_item(item_id: UUID, db: Session = Depends(get_db)):
    """
    Retorna análise AI completa de um item específico.

    A análise vem do processamento realizado por validate_reforma.py
    quando o lote foi submetido.

    Retorna 14 campos:
    - Status (VALIDO | DIVERGENTE)
    - NCM, CEST, CFOP, CST/CSOSN sugeridos
    - Regime tributário, alíquotas IBS/CBS
    - Benefício fiscal, artigo legal, justificativa
    - Score de confiança (0-100)
    """
    try:
        # PASSO 1: Buscar item no banco
        item = db.query(ItemCadastral).filter(ItemCadastral.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")

        # PASSO 2: Montar resposta com todos os 14 campos
        analise = AnaliseItemResponse(
            status=item.status_validacao if item.status_validacao else "VALIDO",
            ncm_sugerido=item.ncm_sugerido,
            cest_sugerido=item.cest_sugerido,
            cfop_sugerido=item.cfop_sugerido,
            cst_csosn_sugerido=item.cst_csosn_sugerido,
            regime_tributario=item.regime_tributario,
            aliquota_ibs=item.aliquota_ibs,
            aliquota_cbs=item.aliquota_cbs,
            tipo_beneficio=item.tipo_beneficio,
            possui_beneficio_fiscal=item.possui_beneficio_fiscal if item.possui_beneficio_fiscal else False,
            artigo_legal=item.artigo_legal,
            justificativa=item.justificativa_ai,
            confianca=item.confianca_ai if item.confianca_ai else 75,
            motivo_divergencia=item.motivo_divergencia,
        )

        # PASSO 3: Retornar (FastAPI serializa automaticamente)
        return analise

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar análise do item: {str(e)}"
        )


@router.post("/agent/query", response_model=AnaliseItemResponse)
async def query_agent_direto(
    request: AgentQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Consulta o agente FastTax em tempo real (sem salvar no banco).

    Útil para validação unitária de um produto antes de fazer upload.

    Request esperado:
    {
        "descricao": "Camiseta 100% Algodão",
        "ncm": "61045090",
        "regime_empresa": "SIMPLES",
        "uf_origem": "SP",
        "uf_destino": "RJ",
        "cnae": "1413800",
        "cest": "123456"
    }

    Response: AnaliseItemResponse com 14 campos
    """
    try:
        # PASSO 1: Validar regime_empresa (Pydantic já valida, mas podemos ser explícitos)
        regimes_validos = {"SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"}
        if request.regime_empresa not in regimes_validos:
            raise ValueError(f"Regime inválido. Deve ser um de: {', '.join(regimes_validos)}")

        # PASSO 2: Montar JSON de entrada para validate_reforma.py
        entrada_agente = {
            "descricao": request.descricao,
            "ncm": request.ncm,
            "regime_empresa": request.regime_empresa,
            "uf_origem": request.uf_origem,
            "uf_destino": request.uf_destino,
            "cnae_principal": request.cnae,
            "cest": request.cest,
        }

        # PASSO 3: Chamar validate_reforma.py via subprocess
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "skills",
            "validate_reforma.py"
        )

        # Converter entrada para JSON string
        entrada_json = json.dumps(entrada_agente, ensure_ascii=False)

        # Executar subprocess
        try:
            processo = subprocess.Popen(
                ["python", script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))  # Trabalhar da pasta do app
            )
            stdout, stderr = processo.communicate(input=entrada_json, timeout=30)

            if processo.returncode != 0:
                raise ValueError(f"Erro no agente: {stderr}")

            # Parse resposta JSON
            resultado = json.loads(stdout)

        except subprocess.TimeoutExpired:
            raise ValueError("Agente demorou demais (timeout > 30s)")
        except json.JSONDecodeError:
            raise ValueError(f"Resposta do agente não é JSON válido: {stdout[:200]}")

        # PASSO 4: Converter resultado para AnaliseItemResponse
        analise = AnaliseItemResponse(
            status=resultado.get("status", "VALIDO"),
            ncm_sugerido=resultado.get("ncm_sugerido"),
            cest_sugerido=resultado.get("cest_sugerido"),
            cfop_sugerido=resultado.get("cfop_sugerido"),
            cst_csosn_sugerido=resultado.get("cst_csosn_sugerido"),
            regime_tributario=resultado.get("regime_tributario"),
            aliquota_ibs=resultado.get("aliquota_ibs"),
            aliquota_cbs=resultado.get("aliquota_cbs"),
            tipo_beneficio=resultado.get("tipo_beneficio"),
            possui_beneficio_fiscal=resultado.get("possui_beneficio_fiscal", False),
            artigo_legal=resultado.get("artigo_legal"),
            justificativa=resultado.get("justificativa"),
            confianca=resultado.get("confianca", 75),
            motivo_divergencia=resultado.get("motivo_divergencia"),
        )

        return analise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao chamar agente: {str(e)}"
        )