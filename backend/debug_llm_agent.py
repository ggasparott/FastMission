"""
Script de Debug: Testar llm_agent + validate_reforma
Objetivo: Identificar onde está falhando a cadeia de processamento
"""

import os
import sys
import json
import subprocess
from dotenv import load_dotenv

# Carregar .env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

print("=" * 80)
print("[DEBUG] LLM_AGENT + VALIDATE_REFORMA")
print("=" * 80)

# ============================================================================
# PASSO 1: Verificar .env
# ============================================================================
print("\n[1/6] Verificando .env...")
print("-" * 80)

env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
    "PINECONE_INDEX": os.getenv("PINECONE_INDEX", "fiscal-reforma-v1"),
    "CELERY_BROKER_URL": os.getenv("CELERY_BROKER_URL"),
}

for key, value in env_vars.items():
    if value:
        masked = value[:10] + "****" if len(value) > 10 else "****"
        print(f"✓ {key}: {masked}")
    else:
        print(f"❌ {key}: NÃO CONFIGURADO")

missing = [k for k, v in env_vars.items() if not v and k != "CELERY_BROKER_URL"]
if missing:
    print(f"\n⚠️  Variáveis faltando: {missing}")
    sys.exit(1)

# ============================================================================
# PASSO 2: Testar Imports
# ============================================================================
print("\n[2/6] Testando imports...")
print("-" * 80)

try:
    print("Importando llm_agent...")
    from backend.IA_TAX.Agentes.llm_agent import FastTax, consultar_rag
    print("✓ llm_agent importado")
except Exception as e:
    print(f"❌ Erro ao importar llm_agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Importando RAG...")
    from backend.IA_TAX.RAG.rag import get_pinecone_index
    print("✓ RAG importado")
except Exception as e:
    print(f"❌ Erro ao importar RAG: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# PASSO 3: Testar Conexão Pinecone
# ============================================================================
print("\n[3/6] Testando Pinecone...")
print("-" * 80)

try:
    index = get_pinecone_index()
    stats = index.describe_index_stats()
    print(f"✓ Pinecone conectado")
    print(f"  - Index: fiscal-reforma-v1")
    print(f"  - Status: {stats}")
except Exception as e:
    print(f"❌ Erro ao conectar Pinecone: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# PASSO 4: Testar consultar_rag
# ============================================================================
print("\n[4/6] Testando consultar_rag...")
print("-" * 80)

try:
    resultado_rag = consultar_rag(
        descricao="Camiseta 100% algodão",
        ncm="61045090",
        regime_empresa="LUCRO_REAL",
        cnae="4719900",
        uf_origem="SP",
        uf_destino="RJ",
        top_k=5
    )
    print(f"✓ RAG consultado com sucesso")
    print(f"  - Contexto usado: {resultado_rag.get('contexto_usado')}")
    print(f"  - Matches encontrados: {len(resultado_rag.get('matches', []))}")
    print(f"  - Tamanho prompt: {len(resultado_rag.get('prompt', ''))} chars")
except Exception as e:
    print(f"❌ Erro ao consultar RAG: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# PASSO 5: Testar FastTax Agent
# ============================================================================
print("\n[5/6] Testando FastTax Agent...")
print("-" * 80)

try:
    print("Rodando agent com prompt simples...")
    prompt = """
    Você é auditor fiscal. Analise este produto:

    Produto: Camiseta 100% algodão
    NCM: 61045090

    Responda OBRIGATORIAMENTE com:
    1. NCM sugerido
    2. Confiança (0-100)
    3. Regime tributário
    """

    resposta_agente = FastTax.run(prompt)
    print(f"✓ Agent respondeu")
    print(f"  - Resposta (primeiros 200 chars): {str(resposta_agente)[:200]}...")

except Exception as e:
    print(f"❌ Erro ao chamar Agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# PASSO 6: Testar validate_reforma.py via subprocess
# ============================================================================
print("\n[6/6] Testando validate_reforma.py via subprocess...")
print("-" * 80)

entrada_teste = {
    "descricao": "Camiseta 100% Algodão Básica",
    "ncm": "61045090",
    "cest": "16000",
    "regime_empresa": "LUCRO_REAL",
    "uf_origem": "SP",
    "uf_destino": "RJ",
    "cnae_principal": "4719900"
}

script_path = os.path.join(
    os.path.dirname(__file__),
    "skills",
    "validate_reforma.py"
)

print(f"Script path: {script_path}")
print(f"Script existe? {os.path.exists(script_path)}")

try:
    entrada_json = json.dumps(entrada_teste, ensure_ascii=False)
    print(f"\nEnviando ao subprocess:")
    print(f"  Input: {entrada_json[:100]}...")

    processo = subprocess.Popen(
        ["python", script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(__file__)
    )

    stdout, stderr = processo.communicate(input=entrada_json, timeout=60)

    print(f"\nRetorno do subprocess:")
    print(f"  Return code: {processo.returncode}")
    print(f"\n  STDOUT:")
    print(f"  {stdout if stdout else '(vazio)'}")
    print(f"\n  STDERR:")
    print(f"  {stderr if stderr else '(vazio)'}")

    if processo.returncode == 0:
        resultado = json.loads(stdout)
        print(f"\n✓ JSON parseado com sucesso!")
        print(f"  - Status: {resultado.get('status')}")
        print(f"  - NCM sugerido: {resultado.get('ncm_sugerido')}")
        print(f"  - Confiança: {resultado.get('confianca')}")
        print(f"  - Regime: {resultado.get('regime_tributario')}")
    else:
        print(f"\n❌ Subprocess retornou erro code {processo.returncode}")

except subprocess.TimeoutExpired:
    print(f"❌ Timeout ao executar subprocess (>60s)")
    processo.kill()
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Erro ao parsear JSON de saída: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro ao executar subprocess: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ DEBUG COMPLETO - TUDO FUNCIONANDO")
print("=" * 80)
