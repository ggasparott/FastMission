"""
Celery Tasks - Processamento assíncrono em background
"""
from celery import Celery
import subprocess
import json
import os
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv

load_dotenv()

# Importações do SQLAlchemy (evitar import circular)
from .database import SessionLocal
from .models import Lote, ItemCadastral, StatusLote, StatusValidacao

# Configuração Celery
celery_app = Celery(
    'fastmission',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# SSL para Upstash (rediss://) - ignorado em local (redis://)
broker = os.getenv('CELERY_BROKER_URL', '')
if broker.startswith('rediss://'):
    import ssl as _ssl
    celery_app.conf.broker_use_ssl = {'ssl_cert_reqs': _ssl.CERT_NONE}
    celery_app.conf.redis_backend_use_ssl = {'ssl_cert_reqs': _ssl.CERT_NONE}


def chamar_ai_script(
    descricao: str,
    ncm: str,
    cest: str = None,
    regime_empresa: str = "LUCRO_REAL",
    uf_origem: str = "SP",
    uf_destino: str = "SP",
    cnae_principal: str = "",
) -> dict:
    """
    Chama o script Python de validação da Reforma Tributária via subprocess.
    
    ⚠️ IMPORTANTE: Mantém lógica de IA separada do código da API.
    """
    # Preparar dados para o script
    entrada = json.dumps({
        "descricao": descricao,
        "ncm": ncm,
        "cest": cest,
        "regime_empresa": regime_empresa,
        "uf_origem": uf_origem,
        "uf_destino": uf_destino,
        "cnae_principal": cnae_principal,
    })
    
    # Caminho do script (relativo ao backend/)
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "skills",
        "validate_reforma.py"
    )
    
    try:
        # Executar script
        resultado = subprocess.run(
            ["python", script_path],
            input=entrada,
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 segundos por item
        )
        
        if resultado.returncode != 0:
            raise Exception(f"Script retornou erro: {resultado.stderr}")
        
        # Parsear resposta JSON
        return json.loads(resultado.stdout)
    
    except subprocess.TimeoutExpired:
        return {
            "ncm_sugerido": ncm,
            "status": "ERRO",
            "explicacao": "Timeout ao processar item (>30s)",
            "justificativa": "Timeout na chamada do agente.",
            "confianca": 0
        }
    except Exception as e:
        return {
            "ncm_sugerido": ncm,
            "status": "ERRO",
            "explicacao": f"Erro ao chamar IA: {str(e)}",
            "justificativa": "Falha no subprocess da IA.",
            "confianca": 0
        }


def calcular_comparativo_fiscal(item: ItemCadastral, resultado: dict, regime_empresa: str) -> dict:
    if regime_empresa == "SIMPLES":
        icms_default = 3.5
        pis_default = 0.0
        cofins_default = 0.0
    else:
        icms_default = 18.0
        pis_default = 1.65
        cofins_default = 7.60

    aliquota_icms = item.aliquota_icms if item.aliquota_icms is not None else icms_default
    aliquota_pis = item.aliquota_pis if item.aliquota_pis is not None else pis_default
    aliquota_cofins = item.aliquota_cofins if item.aliquota_cofins is not None else cofins_default

    carga_atual_percentual = aliquota_icms + aliquota_pis + aliquota_cofins
    possui_st = (item.possui_st or "").upper() == "SIM"
    if possui_st:
        carga_atual_percentual += 4.0

    aliquota_ibs = float(resultado.get("aliquota_ibs") or 0)
    aliquota_cbs = float(resultado.get("aliquota_cbs") or 0)
    carga_reforma_percentual = aliquota_ibs + aliquota_cbs

    quantidade = item.quantidade if item.quantidade is not None else 0
    valor_unitario = item.valor_unitario if item.valor_unitario is not None else 0
    valor_base_calculo = quantidade * valor_unitario
    if valor_base_calculo <= 0:
        valor_base_calculo = 100.0

    valor_atual_estimado = valor_base_calculo * (carga_atual_percentual / 100)
    valor_reforma_estimado = valor_base_calculo * (carga_reforma_percentual / 100)
    diferenca_absoluta = valor_reforma_estimado - valor_atual_estimado
    diferenca_percentual = (diferenca_absoluta / valor_atual_estimado * 100) if valor_atual_estimado > 0 else 0

    confianca = float(resultado.get("confianca") or 0)
    faixa = max(0.03, ((100 - confianca) / 100) * 0.20)
    faixa_incerteza_min = valor_reforma_estimado * (1 - faixa)
    faixa_incerteza_max = valor_reforma_estimado * (1 + faixa)

    return {
        "carga_atual_percentual": round(carga_atual_percentual, 2),
        "carga_reforma_percentual": round(carga_reforma_percentual, 2),
        "valor_base_calculo": round(valor_base_calculo, 2),
        "valor_atual_estimado": round(valor_atual_estimado, 2),
        "valor_reforma_estimado": round(valor_reforma_estimado, 2),
        "diferenca_absoluta": round(diferenca_absoluta, 2),
        "diferenca_percentual": round(diferenca_percentual, 2),
        "faixa_incerteza_min": round(faixa_incerteza_min, 2),
        "faixa_incerteza_max": round(faixa_incerteza_max, 2),
    }


@celery_app.task(bind=True, max_retries=3)
def processar_lote_task(self, lote_id: str):
    """
    Task Celery para processar um lote completo.
    Roda em background no worker.
    
    ⚠️ CRÍTICO: Try/except para não crashar o worker!
    """
    db = SessionLocal()
    
    try:
        # Buscar lote
        lote = db.query(Lote).filter(Lote.id == UUID(lote_id)).first()
        
        if not lote:
            raise Exception(f"Lote {lote_id} não encontrado")
        
        # Marcar como PROCESSANDO
        lote.status = StatusLote.PROCESSANDO
        db.commit()
        
        # Buscar todos os itens pendentes
        itens = db.query(ItemCadastral).filter(
            ItemCadastral.lote_id == UUID(lote_id),
            ItemCadastral.status_validacao == StatusValidacao.PENDENTE
        ).all()
        
        print(f"[Celery] Processando {len(itens)} itens do lote {lote_id}")
        
        # Processar cada item com IA (Reforma Tributária)
        for idx, item in enumerate(itens, 1):
            try:
                # Chamar script de IA com validação da Reforma
                resultado = chamar_ai_script(
                    item.descricao, 
                    item.ncm_original,
                    item.cest_original,
                    regime_empresa=lote.regime_empresa or "LUCRO_REAL",
                    uf_origem=lote.uf_origem or "SP",
                    uf_destino=lote.uf_destino or "SP",
                    cnae_principal=lote.cnae_principal or "",
                )
                
                # Atualizar item com resultado - NCM
                item.ncm_sugerido = resultado.get('ncm_sugerido')
                status_raw = (resultado.get('status') or 'DIVERGENTE').upper()
                if status_raw not in StatusValidacao.__members__:
                    status_raw = 'DIVERGENTE'
                item.status_validacao = StatusValidacao[status_raw]
                item.motivo_divergencia = resultado.get('explicacao')
                item.justificativa_ai = resultado.get('justificativa')
                item.confianca_ai = resultado.get('confianca')
                
                # Atualizar item com resultado - REFORMA TRIBUTÁRIA
                item.cest_sugerido = resultado.get('cest_sugerido')
                item.cest_obrigatorio = resultado.get('cest_obrigatorio')
                item.cfop_sugerido = resultado.get('cfop_sugerido')
                item.cst_csosn_sugerido = resultado.get('cst_csosn_sugerido')
                item.regime_tributario = resultado.get('regime_tributario')
                item.aliquota_ibs = resultado.get('aliquota_ibs')
                item.aliquota_cbs = resultado.get('aliquota_cbs')
                item.possui_beneficio_fiscal = resultado.get('possui_beneficio_fiscal')
                item.tipo_beneficio = resultado.get('tipo_beneficio')
                item.artigo_legal = resultado.get('artigo_legal')

                comparativo = calcular_comparativo_fiscal(item, resultado, lote.regime_empresa or "LUCRO_REAL")
                item.carga_atual_percentual = comparativo['carga_atual_percentual']
                item.carga_reforma_percentual = comparativo['carga_reforma_percentual']
                item.valor_base_calculo = comparativo['valor_base_calculo']
                item.valor_atual_estimado = comparativo['valor_atual_estimado']
                item.valor_reforma_estimado = comparativo['valor_reforma_estimado']
                item.diferenca_absoluta = comparativo['diferenca_absoluta']
                item.diferenca_percentual = comparativo['diferenca_percentual']
                item.faixa_incerteza_min = comparativo['faixa_incerteza_min']
                item.faixa_incerteza_max = comparativo['faixa_incerteza_max']
                
                item.data_processamento = datetime.now()
                
                db.commit()
                
                print(f"[Celery] Item {idx}/{len(itens)} processado: {item.status_validacao} | Regime: {item.regime_tributario}")
                
            except Exception as e:
                # Se um item falhar, continuar com os outros
                print(f"[Celery] Erro ao processar item {item.id}: {e}")
                item.status_validacao = StatusValidacao.DIVERGENTE
                item.motivo_divergencia = f"Erro no processamento: {str(e)}"
                db.commit()
        
        # Marcar lote como CONCLUIDO
        lote.status = StatusLote.CONCLUIDO
        db.commit()
        
        print(f"[Celery] Lote {lote_id} concluído com sucesso!")
        
    except Exception as e:
        # Se der erro geral, marcar lote como ERRO
        print(f"[Celery] ERRO ao processar lote {lote_id}: {e}")
        
        if lote:
            lote.status = StatusLote.ERRO
            db.commit()
        
        # Retry automático (até 3 vezes)
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()
