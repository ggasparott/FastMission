import os, sys, json, subprocess, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(os.path.join(Path(__file__).parent.parent, '.env'))

print("\n" + "="*80)
print("[FULL DEBUG] Teste Completo do Pipeline IA")
print("="*80)

# TEST 1: Environment
print("\n[TEST 1] Variaveis de Ambiente")
print("-"*80)
openai_key = os.getenv('OPENAI_API_KEY')
pinecone_key = os.getenv('PINECONE_API_KEY')
print("OPENAI_API_KEY: " + ("OK" if openai_key else "MISSING"))
print("PINECONE_API_KEY: " + ("OK" if pinecone_key else "MISSING"))

if not all([openai_key, pinecone_key]):
    print("FATAL: Variaveis faltando!")
    sys.exit(1)

# TEST 2: Imports
print("\n[TEST 2] Imports")
print("-"*80)
try:
    from backend.IA_TAX.RAG.rag import get_pinecone_index
    from backend.IA_TAX.Agentes.llm_agent import FastTax, consultar_rag
    from backend.app.models import ItemCadastral
    from backend.app.tasks import chamar_ai_script, calcular_comparativo_fiscal
    print("OK - Todos imports OK")
except Exception as e:
    print("ERRO - Imports: " + str(e))
    sys.exit(1)

# TEST 3: Pinecone
print("\n[TEST 3] Pinecone")
print("-"*80)
try:
    index = get_pinecone_index()
    print("OK - Pinecone conectado")
except Exception as e:
    print("ERRO - Pinecone: " + str(e))
    sys.exit(1)

# TEST 4: RAG
print("\n[TEST 4] RAG Query")
print("-"*80)
try:
    rag = consultar_rag("Camiseta 100% algodao", "61045090", "LUCRO_REAL", "4719900", "SP", "RJ", top_k=5)
    print("OK - RAG: " + str(len(rag.get('matches', []))) + " matches")
except Exception as e:
    print("ERRO - RAG: " + str(e))
    traceback.print_exc()
    sys.exit(1)

# TEST 5: Agent
print("\n[TEST 5] Agent Direto")
print("-"*80)
try:
    resp = FastTax.run("Analise NCM 61045090 para Camiseta algodao. Qual eh o NCM sugerido? Qual a confianca?")
    print("OK - Agent respondeu: " + str(len(str(resp))) + " chars")
except Exception as e:
    print("ERRO - Agent: " + str(e))
    traceback.print_exc()
    sys.exit(1)

# TEST 6: Subprocess
print("\n[TEST 6] validate_reforma.py Subprocess")
print("-"*80)
entrada = {"descricao": "Camiseta", "ncm": "61045090", "cest": "16000", "regime_empresa": "LUCRO_REAL", "uf_origem": "SP", "uf_destino": "RJ", "cnae_principal": "4719900"}
script_path = os.path.join(os.path.dirname(__file__), 'skills', 'validate_reforma.py')

try:
    entrada_json = json.dumps(entrada, ensure_ascii=False)
    processo = subprocess.Popen([sys.executable, script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.path.dirname(script_path), env=os.environ.copy())
    stdout, stderr = processo.communicate(input=entrada_json, timeout=90)

    print("Return code: " + str(processo.returncode))

    if stderr:
        print("\nSTDERR (primeiros 1000 chars):")
        print(stderr[:1000])

    if stdout:
        print("\nSTDOUT (primeiros 1000 chars):")
        print(stdout[:1000])

        # Parsear JSON
        lines = stdout.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                try:
                    resultado = json.loads('\n'.join(lines[i:]))
                    print("\nOK - JSON parseado!")
                    print("  Status: " + str(resultado.get('status')))
                    print("  Confianca: " + str(resultado.get('confianca')))
                    print("  Explicacao: " + str(resultado.get('explicacao'))[:200])
                    break
                except:
                    pass

except Exception as e:
    print("ERRO: " + str(e))
    traceback.print_exc()

# TEST 7: chamar_ai_script
print("\n[TEST 7] chamar_ai_script()")
print("-"*80)
try:
    resultado = chamar_ai_script("Camiseta 100% Algodao", "61045090", "16000", "LUCRO_REAL", "SP", "RJ", "4719900")
    print("OK - Retornou")
    print("  Status: " + str(resultado.get('status')))
    print("  Confianca: " + str(resultado.get('confianca')))
    if resultado.get('status') == 'ERRO':
        print("  ERRO: " + str(resultado.get('explicacao'))[:300])
except Exception as e:
    print("ERRO: " + str(e))
    traceback.print_exc()

print("\n" + "="*80)
print("[CONCLUSAO] Debug completo")
print("="*80)
