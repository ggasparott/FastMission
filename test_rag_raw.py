#!/usr/bin/env python3
"""
Teste RAW direto no Pinecone, sem a função retrieve_fiscal_context
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from backend.IA_TAX.RAG.rag import build_query_vector, get_pinecone_index

def test_raw_query():
    """Query direto sem filtros, mostrando metadados brutos"""
    index = get_pinecone_index()
    print("=" * 60)
    print("TESTE RAW: Query direto no Pinecone")
    print("=" * 60)

    query = "benefícios cesta básica alimentos isenção IBS"
    vector = build_query_vector(query)

    print(f"Pergunta: {query}\n")

    # Query SEM filtros
    response = index.query(vector=vector, top_k=5, include_metadata=True)
    matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])

    print(f"Resultados encontrados: {len(matches)}\n")

    for i, match in enumerate(matches, 1):
        metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
        score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
        doc_id = match.get("id") if isinstance(match, dict) else getattr(match, "id", "N/A")

        print(f"Resultado {i}:")
        print(f"  ID: {doc_id}")
        print(f"  Score: {score:.4f}")
        print(f"  Metadados completos:")
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"    {key}: {value[:80]}...")
            else:
                print(f"    {key}: {value}")
        print()

if __name__ == "__main__":
    test_raw_query()
