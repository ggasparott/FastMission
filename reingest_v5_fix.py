#!/usr/bin/env python3
"""
Script para reingerir benefícios usando Pinecone v5 API corretamente.
Deleta o índice e cria um novo, ou limpa e reingeri.
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector
from backend.IA_TAX.RAG.ingests_pinecone.ingest_beneficios_estados import listar_csvs_estados
import pandas as pd

def reingest_with_v5_api():
    """Reingestão com API v5 correta"""
    index = get_pinecone_index()

    print("=" * 70)
    print("REINGESTÃO: Benefícios com Pinecone v5 API")
    print("=" * 70)

    csvs = listar_csvs_estados()
    if not csvs:
        print("❌ Nenhum arquivo beneficios_{uf}.csv encontrado.")
        sys.exit(1)

    total_geral = 0
    ignorados_geral = 0

    for caminho, uf in csvs:
        print(f"\n🗺️  Processando: {uf} ({os.path.basename(caminho)})")

        df = pd.read_csv(caminho, encoding="utf-8-sig")

        # Validar coluna uf_origem
        if "uf_origem" not in df.columns:
            print(f"   ⚠️  Arquivo sem coluna 'uf_origem' — PULANDO")
            ignorados_geral += len(df)
            continue

        total = 0
        ignorados = 0
        batch = []

        for _, row in df.iterrows():
            codigo = str(row.get("codigo_cbenef", "")).strip()
            descricao = str(row.get("descricao_produto_operacao", "")).strip()

            if not codigo or codigo.lower() == "nan" or not descricao or descricao.lower() == "nan":
                ignorados += 1
                continue

            tipo_beneficio = str(row.get("tipo_beneficio", "")).strip()
            regime = str(row.get("regime_tributario_permitido", "")).strip()
            cst = str(row.get("cst_sugerido_regime_normal", "")).strip()
            csosn = str(row.get("csosn_sugerido_simples_nacional", "")).strip()
            fundamentacao = str(row.get("fundamentacao_legal", "")).strip()
            regra = str(row.get("regra_validacao_agente_ia", "")).strip()
            uf_origem = str(row.get("uf_origem", uf)).strip().upper()

            texto = (
                f"cbenef: {codigo} | {descricao} | tipo: {tipo_beneficio} | "
                f"regime: {regime} | CST: {cst} | CSOSN: {csosn} | "
                f"fundamentação: {fundamentacao} | regra: {regra} | UF: {uf_origem}"
            )

            metadados = {
                "codigo_cbenef": codigo,
                "descricao_produto_operacao": descricao,
                "tipo_beneficio": tipo_beneficio,
                "regime_tributario_permitido": regime,
                "cst_sugerido_regime_normal": cst,
                "csosn_sugerido_simples_nacional": csosn,
                "fundamentacao_legal": fundamentacao,
                "regra_validacao_agente_ia": regra,
                "uf_origem": uf_origem,
                "fonte": f"Tabela cBenef {uf_origem}",
                "tipo_regra": "beneficio_fiscal",
            }

            vetor = build_query_vector(texto)
            if not vetor or all(v == 0 for v in vetor):
                ignorados += 1
                continue

            doc_id = f"cbenef_{uf_origem}_{codigo}"

            # Pinecone v5 format
            batch.append({
                "id": doc_id,
                "values": vetor,
                "metadata": metadados,
            })

            total += 1

            # Upload em batch a cada 100 documentos
            if len(batch) >= 100:
                index.upsert(vectors=batch, namespace="")
                print(f"   📤 {total} enviados...")
                batch = []

        # Upload final do batch
        if batch:
            index.upsert(vectors=batch, namespace="")
            print(f"   📤 {total} enviados (final)...")

        print(f"   ✅ {uf}: {total} enviados, {ignorados} ignorados")
        total_geral += total
        ignorados_geral += ignorados

    print(f"\n🏁 Reingestão concluída!")
    print(f"   Total enviados: {total_geral}")
    print(f"   Total ignorados: {ignorados_geral}")

    # Stats finais
    stats = index.describe_index_stats()
    print(f"   Vetores no índice: {stats.get('total_vector_count', 'N/A')}")

if __name__ == "__main__":
    reingest_with_v5_api()
