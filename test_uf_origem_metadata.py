#!/usr/bin/env python3
"""
Script para testar e inspecionar se uf_origem está nos metadados do Pinecone
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from backend.IA_TAX.RAG.rag import build_query_vector, get_pinecone_index

def inspect_metadata():
    """Inspeciona os metadados de documentos no Pinecone"""
    index = get_pinecone_index()

    print("=" * 70)
    print("INSPEÇÃO: Verificando uf_origem nos metadados")
    print("=" * 70)

    # Query simples
    query = "benefícios cesta básica"
    vector = build_query_vector(query)

    print(f"\nBuscando: {query}\n")

    response = index.query(vector=vector, top_k=10, include_metadata=True)
    matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])

    print(f"Resultados encontrados: {len(matches)}\n")

    uf_origem_found = 0
    uf_origem_missing = 0
    all_metadata_keys = set()

    for i, match in enumerate(matches, 1):
        metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
        doc_id = match.get("id") if isinstance(match, dict) else getattr(match, "id", "N/A")
        score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)

        # Coletar todas as chaves de metadados
        all_metadata_keys.update(metadata.keys())

        uf_origin_value = metadata.get("uf_origem", "MISSING")

        print(f"Resultado {i}:")
        print(f"  ID: {doc_id}")
        print(f"  Score: {score:.4f}")
        print(f"  uf_origem: {uf_origin_value}")
        print(f"  codigo_cbenef: {metadata.get('codigo_cbenef', 'N/A')}")
        print(f"  tipo_beneficio: {metadata.get('tipo_beneficio', 'N/A')}")

        if uf_origin_value == "MISSING":
            uf_origem_missing += 1
            print(f"  ⚠️  uf_origem AUSENTE!")
        else:
            uf_origem_found += 1
            print(f"  ✓ uf_origem encontrado")

        print()

    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Documentos COM uf_origem: {uf_origem_found}")
    print(f"Documentos SEM uf_origem: {uf_origem_missing}")
    print(f"\nTodas as chaves de metadados encontradas:")
    for key in sorted(all_metadata_keys):
        print(f"  - {key}")

    print("\n" + "=" * 70)
    if uf_origem_missing == 0:
        print("✅ SUCESSO: Todos os documentos têm uf_origem!")
    else:
        print(f"❌ PROBLEMA: {uf_origem_missing} documentos estão sem uf_origem")
        print("   Ação necessária: Executar reingest_v5_fix.py")
    print("=" * 70)

if __name__ == "__main__":
    inspect_metadata()