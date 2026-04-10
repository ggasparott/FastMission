#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

print("=" * 80)
print("[DEBUG] LLM_AGENT + VALIDATE_REFORMA")
print("=" * 80)

# PASSO 1: Verificar .env
print("\n[1/5] Verificando .env...")
print("-" * 80)

openai_key = os.getenv('OPENAI_API_KEY')
pinecone_key = os.getenv('PINECONE_API_KEY')

if openai_key:
    print(f"OK OPENAI_API_KEY: {openai_key[:15]}...")
else:
    print("ERRO OPENAI_API_KEY nao configurada")
    sys.exit(1)

if pinecone_key:
    print(f"OK PINECONE_API_KEY: {pinecone_key[:15]}...")
else:
    print("ERRO PINECONE_API_KEY nao configurada")
    sys.exit(1)

# PASSO 2: Teste subprocess direto
print("\n[2/5] Testando subprocess com validate_reforma.py...")
print("-" * 80)

entrada_teste = {
    "descricao": "Camiseta 100% Algodao",
    "ncm": "61045090",
    "cest": "16000",
    "regime_empresa": "LUCRO_REAL",
    "uf_origem": "SP",
    "uf_destino": "RJ",
    "cnae_principal": "4719900"
}

script_path = os.path.join(os.path.dirname(__file__), 'backend', 'skills', 'validate_reforma.py')

print(f"Script path: {script_path}")
print(f"Script existe: {os.path.exists(script_path)}")

entrada_json = json.dumps(entrada_teste, ensure_ascii=False)

try:
    print("\nExecutando subprocess...")
    processo = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(script_path)
    )

    stdout, stderr = processo.communicate(input=entrada_json, timeout=60)

    print(f"\nReturn code: {processo.returncode}")

    if stderr:
        print(f"\n[STDERR]:")
        print(stderr)

    if stdout:
        print(f"\n[STDOUT]:")
        print(stdout)

        if processo.returncode == 0:
            try:
                resultado = json.loads(stdout)
                print(f"\n[RESULTADO JSON]:")
                print(f"  status: {resultado.get('status')}")
                print(f"  ncm_sugerido: {resultado.get('ncm_sugerido')}")
                print(f"  confianca: {resultado.get('confianca')}")
                print(f"  regime_tributario: {resultado.get('regime_tributario')}")
                print(f"  cest_sugerido: {resultado.get('cest_sugerido')}")
                print(f"  aliquota_ibs: {resultado.get('aliquota_ibs')}")
                print(f"  aliquota_cbs: {resultado.get('aliquota_cbs')}")
                print(f"  tipo_beneficio: {resultado.get('tipo_beneficio')}")
                print(f"  justificativa: {resultado.get('justificativa')[:100] if resultado.get('justificativa') else 'N/A'}...")
            except json.JSONDecodeError as je:
                print(f"ERRO ao parsear JSON: {je}")

    if processo.returncode != 0:
        print(f"\nERRO: Subprocess retornou code {processo.returncode}")

except subprocess.TimeoutExpired:
    print("ERRO: Timeout (>60s)")
    processo.kill()
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[FIM] Debug concluido")
print("=" * 80)
