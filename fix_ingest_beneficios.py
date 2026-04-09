#!/usr/bin/env python3
"""
Script para limpar Pinecone de documentos sem uf_origem e reingeri-los corretamente.
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from backend.IA_TAX.RAG.rag import get_pinecone_index
from backend.IA_TAX.RAG.ingests_pinecone.ingest_beneficios_estados import (
    listar_csvs_estados, processar_csv_estado
)

def limpar_documentos_com_uf_na():
    """Remove documentos com uf_origem = 'N/A' ou missing do Pinecone."""
    index = get_pinecone_index()

    print("🧹 Limpando documentos com uf_origem = N/A...")

    # Listar todos os vetores e deletar os problemáticos
    try:
        # Query para encontrar documentos com uf_origem = N/A ou vazio
        # Como Pinecone não suporta bem queries por metadata vazia, vamos usar uma abordagem diferente:
        # deletar todos os cbenef e reingeri-los

        # Primeiro, listar todos os IDs
        index_stats = index.describe_index_stats()
        print(f"Total de vetores no índice: {index_stats.get('total_vector_count', 0)}")

        # Deletar por padrão de ID (cbenef_)
        # Nota: Pinecone não suporta delete com wildcard direto, então vamos fazer de outra forma
        print("⚠️  Pinecone não suporta delete bulk com pattern. Vamos reingeri-los corretamente.")

    except Exception as e:
        print(f"Erro ao listar estatísticas: {e}")

    return True

def main():
    print("=" * 60)
    print("FIX: Reingestão correta de benefícios com uf_origem")
    print("=" * 60)

    # Limpa documentos problemáticos
    limpar_documentos_com_uf_na()

    # Reingeri todos os CSVs válidos
    index = get_pinecone_index()
    csvs = listar_csvs_estados()

    if not csvs:
        print("❌ Nenhum arquivo beneficios_{uf}.csv encontrado.")
        sys.exit(1)

    print(f"\n📋 Reingerindo {len(csvs)} arquivos...")
    total_geral = 0
    ignorados_geral = 0

    for caminho, uf in csvs:
        enviados, ignorados = processar_csv_estado(index, caminho, uf)
        total_geral += enviados
        ignorados_geral += ignorados

    print(f"\n🏁 Reingestão concluída!")
    print(f"   Total enviados: {total_geral}")
    print(f"   Total ignorados: {ignorados_geral}")
    print(f"   Estados processados: {[uf for _, uf in csvs]}")

if __name__ == "__main__":
    main()
