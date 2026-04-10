"""
Bridge entre Celery + subprocess e FastTax Agent

Fluxo:
1. tasks.py chama: python validate_reforma.py < entrada.json
2. Lê JSON do stdin com dados do item: {descricao, ncm, cest, regime_empresa, uf_origem, uf_destino, cnae_principal}
3. Consulta RAG (Pinecone) para puxar contexto fiscal relevante
4. Monta prompt estruturado com instruções da agencia
5. Chama FastTax.run() para gerar resposta
6. Parseia resposta e retorna JSON com todos os campos esperados por tasks.py
7. Escreve resultado no stdout (stdout é capturado por tasks.py)

IMPORTANTE: Todo erro deve retornar {"status": "ERRO", "explicacao": "..."}
"""

import os
import sys
import json
import re
from dotenv import load_dotenv

# ===== CONFIGURAÇÃO INICIAL =====
# 1. Carregar .env da raiz do projeto
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env")))

# 2. Configurar sys.path para imports relativos funcionarem
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# 3. Importar funcionalidades do projeto
from backend.IA_TAX.Agentes.llm_agent import consultar_rag, FastTax, filter_insecure_phrases
from backend.IA_TAX.RAG.rag import get_pinecone_index


def ler_entrada_stdin():
    """
    PASSO 1: Ler e validar entrada JSON do stdin

    Esperado: {"descricao", "ncm", "cest", "regime_empresa", "uf_origem", "uf_destino", "cnae_principal"}
    """
    try:
        entrada_raw = sys.stdin.read()
        dados = json.loads(entrada_raw)
        return dados
    except json.JSONDecodeError as e:
        return {
            "status": "ERRO",
            "explicacao": f"JSON invalido do stdin: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "ERRO",
            "explicacao": f"Erro ao ler stdin: {str(e)}"
        }


def consultar_contexto_rag(dados):
    """
    PASSO 2: Consultar RAG para puxar contexto fiscal do estado/regime

    Retorna um dicionario com:
    - "prompt": prompt montado com contexto legal
    - "matches": lista de matches do Pinecone
    - "contexto_usado": bool se achou dados
    """
    try:
        descricao = dados.get("descricao", "")
        ncm = dados.get("ncm", "")
        regime = dados.get("regime_empresa", "")
        cnae = dados.get("cnae_principal", "")
        uf_origem = dados.get("uf_origem", "")
        uf_destino = dados.get("uf_destino", "")

        # Chamando a funcao que ja existe em llm_agent.py
        resultado_rag = consultar_rag(
            descricao=descricao,
            ncm=ncm,
            regime_empresa=regime,
            cnae=cnae,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
            top_k=10
        )
        return resultado_rag
    except Exception as e:
        return {
            "status": "ERRO",
            "explicacao": f"Erro ao consultar RAG: {str(e)}"
        }


def montar_prompt_agente(dados, contexto_rag):
    """
    PASSO 3: Montar prompt estruturado para o agente

    Combina:
    - Contexto legal do RAG
    - Dados do item (descricao, ncm, cest, regime, cnae, UFs)
    - Instrucoes estritas do agente (de llm_agent.py)
    """
    try:
        prompt_base = contexto_rag.get("prompt", "")

        # Adiciona contexto especifico do item
        prompt_estruturado = f"""
Voce e o FastTax Agent, auditor fiscal especializado em reforma tributaria (LC 214/2025).

=== DADOS DO ITEM A AUDITAR ===
Descricao: {dados.get('descricao', '')}
NCM Atual: {dados.get('ncm', '')}
CEST Atual: {dados.get('cest', '')}
Regime Tributario: {dados.get('regime_empresa', '')}
CNAE Principal: {dados.get('cnae_principal', '')}
UF Origem: {dados.get('uf_origem', '')}
UF Destino: {dados.get('uf_destino', '')}

=== CONTEXTO LEGAL (RAG) ===
{prompt_base}

=== TAREFA ===
Analise este item e forneca OBRIGATORIAMENTE em sua resposta:
1. NCM sugerido (se diferente do atual)
2. CEST sugerido (se aplicavel)
3. Tipo de beneficio fiscal (se houver)
4. CST/CSOSN sugerido
5. CFOP sugerido (se houver mudanca)
6. Justificativa tecnica (maximo 3 linhas)
7. Score de confianca (0-100)
8. Artigo legal principal citado

NUNCA consulte outras fontes alem do contexto RAG fornecido.
NUNCA peca para o usuario verificar com outras fontes.
VOCE E O BANCO DE DADOS.
        """
        return prompt_estruturado
    except Exception as e:
        return {
            "status": "ERRO",
            "explicacao": f"Erro ao montar prompt: {str(e)}"
        }


def chamar_agente(prompt):
    """
    PASSO 4: Chamar FastTax Agent para processar o prompt

    Retorna a resposta em texto do agente
    """
    try:
        # Chama o agente com o prompt estruturado
        resposta_agente = FastTax.run(prompt)

        # Extrair texto da resposta (RunOutput object)
        # Tentar diferentes atributos
        if hasattr(resposta_agente, 'content'):
            return str(resposta_agente.content)
        elif hasattr(resposta_agente, 'messages'):
            # Se é uma lista de mensagens, extrair última
            if isinstance(resposta_agente.messages, list) and resposta_agente.messages:
                return str(resposta_agente.messages[-1])
            return str(resposta_agente.messages)
        else:
            # Se tiver atributo 'message'
            if hasattr(resposta_agente, 'message'):
                return str(resposta_agente.message)
            # Fallback: converter para string
            return str(resposta_agente)
    except Exception as e:
        return {
            "status": "ERRO",
            "explicacao": f"Erro ao chamar agente: {str(e)}"
        }


def parsear_resposta_agente(resposta_texto, ncm_original=None, cest_original=None):
    """
    PASSO 5: Parsear a resposta do agente em campos estruturados

    Extrai valores usando regex/string search de padroes esperados
    Retorna dicionario com todos os campos que tasks.py espera

    Parametros:
    - resposta_texto: texto retornado pelo agente FastTax
    - ncm_original: NCM do item original (para comparar divergencias)
    - cest_original: CEST do item original (para comparar divergencias)
    """
    try:
        # Se a resposta for um erro, retorna como esta
        if isinstance(resposta_texto, dict) and "status" in resposta_texto and resposta_texto["status"] == "ERRO":
            return resposta_texto

        resposta_limpa = filter_insecure_phrases(str(resposta_texto))

        # ===== EXTRAÇÃO 1: CAMPOS NUMÉRICOS SIMPLES =====

        # NCM (8 dígitos) - mais robusto para variações de espaçamento
        ncm_match = re.search(r"NCM\s*:?=?\s*(?:sugerido)?\s*:?=?\s*(\d{8})", resposta_limpa, re.IGNORECASE)
        if not ncm_match:
            ncm_match = re.search(r"(\d{8})\s+(?:é|ser)\s+(?:o\s+)?NCM", resposta_limpa, re.IGNORECASE)
        ncm_sugerido = ncm_match.group(1) if ncm_match else None

        # CEST (6 dígitos) - mais robusto
        cest_match = re.search(r"CEST\s*:?=?\s*(?:sugerido)?\s*:?=?\s*(\d{6})", resposta_limpa, re.IGNORECASE)
        if not cest_match:
            cest_match = re.search(r"(\d{6})\s+(?:é|ser)\s+(?:o\s+)?CEST", resposta_limpa, re.IGNORECASE)
        cest_sugerido = cest_match.group(1) if cest_match else None

        # CFOP (4 dígitos) - mais robusto
        cfop_match = re.search(r"CFOP\s*:?=?\s*(?:sugerido)?\s*:?=?\s*(\d{4})", resposta_limpa, re.IGNORECASE)
        if not cfop_match:
            cfop_match = re.search(r"(\d{4})\s+(?:é|ser)\s+(?:o\s+)?CFOP", resposta_limpa, re.IGNORECASE)
        cfop_sugerido = cfop_match.group(1) if cfop_match else None

        # Confiança (0-100%)
        conf_match = re.search(r"(?:confianca|confiança|score)\s*[:=]?\s*(\d+)\s*%?", resposta_limpa, re.IGNORECASE)
        confianca = int(conf_match.group(1)) if conf_match else 75
        confianca = min(max(confianca, 0), 100)  # garante 0-100

        # Alíquota IBS
        ibs_match = re.search(r"(?:aliquota|alíquota)?\s*IBS\s*[:=]?\s*([\d.,]+)\s*%?", resposta_limpa, re.IGNORECASE)
        aliquota_ibs = None
        if ibs_match:
            try:
                aliquota_ibs = float(ibs_match.group(1).replace(",", "."))
            except (ValueError, TypeError, AttributeError):
                pass

        # Alíquota CBS
        cbs_match = re.search(r"(?:aliquota|alíquota)?\s*CBS\s*[:=]?\s*([\d.,]+)\s*%?", resposta_limpa, re.IGNORECASE)
        aliquota_cbs = None
        if cbs_match:
            try:
                aliquota_cbs = float(cbs_match.group(1).replace(",", "."))
            except (ValueError, TypeError, AttributeError):
                pass

        # ===== EXTRAÇÃO 2: CAMPOS COM VARIAÇÕES =====

        # Tipo de Benefício (com mapa de variações)
        tipo_beneficio = None
        tipos_map = {
            r"isencao|isenção": "Isencao",
            r"reducao|redução": "Reducao de Base de Calculo",
            r"diferimento": "Diferimento",
            r"substituicao|substituição": "Substituicao Tributaria",
            r"credito|crédito": "Credito Presumido",
            r"suspensao|suspensão": "Suspensao",
            r"nao incidencia|não incidência": "Nao Incidencia",
        }
        for padrao, valor_normalizado in tipos_map.items():
            if re.search(padrao, resposta_limpa, re.IGNORECASE):
                tipo_beneficio = valor_normalizado
                break

        # Regime Tributário
        regime_tributario = None
        regimes_possiveis = ["Simples Nacional", "Regime Normal", "MEI", "Optante"]
        for regime in regimes_possiveis:
            if re.search(re.escape(regime), resposta_limpa, re.IGNORECASE):
                regime_tributario = regime
                break

        # CST/CSOSN
        cst_csosn_sugerido = None
        cst_match = re.search(r"CST\s*(?:sugerido)?\s*[:=]?\s*(\d{2})", resposta_limpa, re.IGNORECASE)
        if cst_match:
            cst_csosn_sugerido = cst_match.group(1)
        else:
            csosn_match = re.search(r"CSOSN\s*(?:sugerido)?\s*[:=]?\s*(\d{3})", resposta_limpa, re.IGNORECASE)
            if csosn_match:
                cst_csosn_sugerido = csosn_match.group(1)

        # ===== EXTRAÇÃO 3: CAMPOS COM CONTEXTO =====

        # Artigo Legal (até ponto ou fim)
        artigo_match = re.search(r"(?:artigo legal|fundamentacao|fundamentação|baseado em)\s*[:=]?\s*(.+?)(?:\.|$|\n)", resposta_limpa, re.IGNORECASE)
        artigo_legal = artigo_match.group(1).strip() if artigo_match else None

        # Justificativa (até parágrafo duplo ou fim)
        just_match = re.search(r"justificativa\s*[:=]?\s*(.+?)(?:\n\n|$)", resposta_limpa, re.IGNORECASE | re.DOTALL)
        justificativa = just_match.group(1).strip()[:300] if just_match else resposta_limpa[:300]

        # ===== LÓGICA: DETECTAR STATUS E BENEFÍCIO =====

        # Status: VALIDO vs DIVERGENTE
        status = "VALIDO"
        motivo_divergencia = None
        if ncm_sugerido and ncm_original and ncm_sugerido != ncm_original:
            status = "DIVERGENTE"
            motivo_divergencia = f"NCM reclassificado de {ncm_original} para {ncm_sugerido}"
        elif cest_sugerido and cest_original and cest_sugerido != cest_original:
            status = "DIVERGENTE"
            motivo_divergencia = f"CEST alterado de {cest_original} para {cest_sugerido}"

        # Detectar se tem benefício fiscal
        possui_beneficio_fiscal = False
        if tipo_beneficio:
            sem_beneficio_patterns = ["sem beneficio", "tributado", "normal"]
            has_sem_beneficio = any(re.search(p, tipo_beneficio, re.IGNORECASE) for p in sem_beneficio_patterns)
            possui_beneficio_fiscal = not has_sem_beneficio

        # ===== MONTAR RESULTADO FINAL =====

        resultado = {
            "status": status,
            "ncm_sugerido": ncm_sugerido,
            "cest_sugerido": cest_sugerido,
            "cfop_sugerido": cfop_sugerido,
            "cst_csosn_sugerido": cst_csosn_sugerido,
            "regime_tributario": regime_tributario,
            "aliquota_ibs": aliquota_ibs,
            "aliquota_cbs": aliquota_cbs,
            "tipo_beneficio": tipo_beneficio,
            "possui_beneficio_fiscal": possui_beneficio_fiscal,
            "artigo_legal": artigo_legal,
            "justificativa": justificativa,
            "confianca": confianca,
            "explicacao": resposta_limpa,
            "motivo_divergencia": motivo_divergencia,
        }

        return resultado
    except Exception as e:
        return {
            "status": "ERRO",
            "explicacao": f"Erro ao parsear resposta: {str(e)}"
        }


def main():
    """
    FLUXO PRINCIPAL: Orquestra todos os passos
    """

    # PASSO 1: Ler entrada
    dados = ler_entrada_stdin()
    if "status" in dados and dados.get("status") == "ERRO":
        print(json.dumps(dados))
        sys.exit(1)

    # PASSO 2: Consultar RAG
    contexto_rag = consultar_contexto_rag(dados)
    if isinstance(contexto_rag, dict) and contexto_rag.get("status") == "ERRO":
        print(json.dumps(contexto_rag))
        sys.exit(1)

    # PASSO 3: Montar prompt
    prompt = montar_prompt_agente(dados, contexto_rag)
    if isinstance(prompt, dict) and prompt.get("status") == "ERRO":
        print(json.dumps(prompt))
        sys.exit(1)

    # PASSO 4: Chamar agente
    resposta_agente = chamar_agente(prompt)
    if isinstance(resposta_agente, dict) and resposta_agente.get("status") == "ERRO":
        print(json.dumps(resposta_agente))
        sys.exit(1)

    # PASSO 5: Parsear resposta (passa NCM e CEST originais para comparação)
    resultado_final = parsear_resposta_agente(
        resposta_texto=resposta_agente,
        ncm_original=dados.get("ncm"),
        cest_original=dados.get("cest")
    )

    # SAIDA: Retornar JSON completo no stdout (capturado por tasks.py)
    print(json.dumps(resultado_final, ensure_ascii=False))


if __name__ == "__main__":
    main()
