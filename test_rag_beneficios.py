#!/usr/bin/env python3
"""
Script para testar consulta RAG aos benefícios estaduais ingeridos no Pinecone
"""
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from backend.IA_TAX.RAG.rag import build_query_vector, get_pinecone_index

def test_rag_beneficios():
    """Testa consulta aos benefícios no Pinecone"""
    try:
        index = get_pinecone_index()
        print("✓ Conectado ao Pinecone com sucesso\n")

        # Teste 1: Consulta por cesta básica
        print("=" * 60)
        print("TESTE 1: Busca por benefícios de cesta básica")
        print("=" * 60)
        query1 = "benefícios cesta básica alimentos isenção IBS"
        vector1 = build_query_vector(query1)
        response1 = index.query(vector=vector1, top_k=3, include_metadata=True)

        matches1 = response1.get("matches", []) if isinstance(response1, dict) else getattr(response1, "matches", [])
        print(f"Pergunta: {query1}\n")
        print(f"Resultados encontrados: {len(matches1)}\n")

        for i, match in enumerate(matches1, 1):
            metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
            score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
            print(f"Resultado {i}:")
            print(f"  Score: {score:.4f}")
            print(f"  UF: {metadata.get('uf_origem', 'N/A')}")
            print(f"  Código: {metadata.get('codigo_cbenef', 'N/A')}")
            print(f"  Tipo: {metadata.get('tipo_beneficio', 'N/A')}")
            print(f"  Descrição: {metadata.get('descricao_produto_operacao', '')[:80]}...")
            print()

        # Teste 2: Consulta por medicamentos
        print("=" * 60)
        print("TESTE 2: Busca por benefícios de medicamentos")
        print("=" * 60)
        query2 = "medicamentos farmacêuticos isenção CBS"
        vector2 = build_query_vector(query2)
        response2 = index.query(vector=vector2, top_k=3, include_metadata=True)

        matches2 = response2.get("matches", []) if isinstance(response2, dict) else getattr(response2, "matches", [])
        print(f"Pergunta: {query2}\n")
        print(f"Resultados encontrados: {len(matches2)}\n")

        for i, match in enumerate(matches2, 1):
            metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
            score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
            print(f"Resultado {i}:")
            print(f"  Score: {score:.4f}")
            print(f"  UF: {metadata.get('uf_origem', 'N/A')}")
            print(f"  Código: {metadata.get('codigo_cbenef', 'N/A')}")
            print(f"  Tipo: {metadata.get('tipo_beneficio', 'N/A')}")
            print(f"  Descrição: {metadata.get('descricao_produto_operacao', '')[:80]}...")
            print()

        # Teste 3: Consulta por estado específico (Paraná)
        print("=" * 60)
        print("TESTE 3: Busca por benefícios no estado de SP")
        print("=" * 60)
        query3 = "São Paulo benefícios tributários"
        vector3 = build_query_vector(query3)
        response3 = index.query(vector=vector3, top_k=3, include_metadata=True)

        matches3 = response3.get("matches", []) if isinstance(response3, dict) else getattr(response3, "matches", [])
        print(f"Pergunta: {query3}\n")
        print(f"Resultados encontrados: {len(matches3)}\n")

        for i, match in enumerate(matches3, 1):
            metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
            score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
            print(f"Resultado {i}:")
            print(f"  Score: {score:.4f}")
            print(f"  UF: {metadata.get('uf_origem', 'N/A')}")
            print(f"  Código: {metadata.get('codigo_cbenef', 'N/A')}")
            print(f"  Tipo: {metadata.get('tipo_beneficio', 'N/A')}")
            print(f"  Descrição: {metadata.get('descricao_produto_operacao', '')[:80]}...")
            print()

        # Estatísticas do índice
        print("=" * 60)
        print("ESTATÍSTICAS DO ÍNDICE PINECONE")
        print("=" * 60)
        stats = index.describe_index_stats()
        print(f"Stats: {stats}")

        print("\n✓ Teste RAG concluído com sucesso!")

    except Exception as e:
        print(f"✗ Erro ao testar RAG: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_rag_beneficios()
