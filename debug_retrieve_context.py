#!/usr/bin/env python3
"""
Debug: Comparar retrieve_fiscal_context vs query direto
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from backend.IA_TAX.RAG.rag import (
    build_query_vector,
    get_pinecone_index,
    retrieve_fiscal_context
)

def test_both_methods():
    """Testa ambos os métodos"""
    index = get_pinecone_index()

    print("=" * 70)
    print("COMPARAÇÃO: Query RAW vs retrieve_fiscal_context")
    print("=" * 70)

    # Parâmetros de teste
    descricao = "cesta básica alimentos isenção"
    ncm = ""
    regime_empresa = ""
    cnae = ""
    uf_origem = "RJ"
    uf_destino = "SC"

    print(f"\nParâmetros:")
    print(f"  descricao: {descricao}")
    print(f"  ncm: {ncm}")
    print(f"  regime_empresa: {regime_empresa}")
    print(f"  uf_origem: {uf_origem}")
    print(f"  uf_destino: {uf_destino}\n")

    # ===== MÉTODO 1: Query RAW =====
    print("=" * 70)
    print("MÉTODO 1: Query RAW direto no Pinecone")
    print("=" * 70)
    vector = build_query_vector(descricao)
    response = index.query(vector=vector, top_k=3, include_metadata=True)
    matches_raw = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])

    print(f"\nResultados: {len(matches_raw)}\n")
    for i, match in enumerate(matches_raw, 1):
        metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
        score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
        print(f"Resultado {i}:")
        print(f"  Score: {score:.4f}")
        print(f"  uf_origem: {metadata.get('uf_origem', 'MISSING')}")
        print(f"  codigo_cbenef: {metadata.get('codigo_cbenef', 'MISSING')}")
        print(f"  tipo_beneficio: {metadata.get('tipo_beneficio', 'MISSING')}")
        print()

    # ===== MÉTODO 2: retrieve_fiscal_context =====
    print("=" * 70)
    print("MÉTODO 2: retrieve_fiscal_context")
    print("=" * 70)
    results = retrieve_fiscal_context(
        index=index,
        descricao=descricao,
        ncm=ncm,
        regime_empresa=regime_empresa,
        cnae_principal=cnae,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        top_k=3
    )

    print(f"\nResultados: {len(results)}\n")
    for i, result in enumerate(results, 1):
        print(f"Resultado {i}:")
        print(f"  Score: {result.get('score', 'N/A')}")
        print(f"  Tipo: {result.get('tipo_regra', 'N/A')}")
        print(f"  Payload keys: {list(result.get('payload', {}).keys())}")
        print(f"  Payload uf_origem: {result.get('payload', {}).get('uf_origem', 'MISSING')}")
        print()

if __name__ == "__main__":
    test_both_methods()
