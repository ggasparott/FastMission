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

# Configuração Celery
celery_app = Celery(
    'fastmission',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Carregar celeryconfig (SSL para Upstash)
try:
    celery_app.config_from_object('celeryconfig')
except Exception:
    # Se não encontrar celeryconfig, configurar SSL inline para rediss://
    import ssl as _ssl
    broker = os.getenv('CELERY_BROKER_URL', '')
    if broker.startswith('rediss://'):
        celery_app.conf.broker_use_ssl = {'ssl_cert_reqs': _ssl.CERT_NONE}
        celery_app.conf.redis_backend_use_ssl = {'ssl_cert_reqs': _ssl.CERT_NONE}

# Importações do SQLAlchemy (evitar import circular)
from .database import SessionLocal
from .models import Lote, ItemCadastral, StatusLote, StatusValidacao


def chamar_ai_script(descricao: str, ncm: str, cest: str = None) -> dict:
    """
    Chama o script Python de validação da Reforma Tributária via subprocess.
    
    ⚠️ IMPORTANTE: Mantém lógica de IA separada do código da API.
    """
    # Preparar dados para o script
    entrada = json.dumps({
        "descricao": descricao,
        "ncm": ncm,
        "cest": cest
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
            "confianca": 0
        }
    except Exception as e:
        return {
            "ncm_sugerido": ncm,
            "status": "ERRO",
            "explicacao": f"Erro ao chamar IA: {str(e)}",
            "confianca": 0
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
                    item.cest_original
                )
                
                # Atualizar item com resultado - NCM
                item.ncm_sugerido = resultado.get('ncm_sugerido')
                item.status_validacao = StatusValidacao[resultado.get('status', 'ERRO')]
                item.motivo_divergencia = resultado.get('explicacao')
                item.confianca_ai = resultado.get('confianca')
                
                # Atualizar item com resultado - REFORMA TRIBUTÁRIA
                item.cest_sugerido = resultado.get('cest_sugerido')
                item.cest_obrigatorio = resultado.get('cest_obrigatorio')
                item.regime_tributario = resultado.get('regime_tributario')
                item.aliquota_ibs = resultado.get('aliquota_ibs')
                item.aliquota_cbs = resultado.get('aliquota_cbs')
                item.possui_beneficio_fiscal = resultado.get('possui_beneficio_fiscal')
                item.tipo_beneficio = resultado.get('tipo_beneficio')
                item.artigo_legal = resultado.get('artigo_legal')
                
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
