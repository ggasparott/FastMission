#!/usr/bin/env python3
"""
Script para corrigir apenas os benefícios de SP adicionando uf_origem correto.
Busca todos os cbenef_SP_* no Pinecone, adiciona uf_origem="SP" aos metadados e reingeri.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from backend.IA_TAX.RAG.rag import build_query_vector, get_pinecone_index
import pandas as pd

def find_sp_csv():
    """Encontra o arquivo CSV de SP"""
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(base_dir, "database_tributaria_2026-03-16", "mapeamento_cbenef_cst_regime.csv"),
        os.path.join(base_dir, "database_tributaria_2026-03-16", "mapeamento_cbenef_cst_regime.csv"),
    ]

    for path in candidates:
        if os.path.exists(path):
            print(f"✓ Encontrado: {path}")
            return path

    return None

def fix_sp_metadata():
    """Corrige metadados de SP adicionando uf_origem"""
    index = get_pinecone_index()

    print("=" * 70)
    print("FIX: Adicionando uf_origem aos benefícios de SP")
    print("=" * 70)

    # Encontra arquivo SP
    sp_csv = find_sp_csv()
    if not sp_csv:
        print("❌ Nenhum arquivo de SP encontrado!")
        sys.exit(1)

    print(f"\n📁 Carregando: {sp_csv}")
    df = pd.read_csv(sp_csv, encoding="utf-8-sig")

    print(f"📊 Total de linhas: {len(df)}")

    # Processar linhas
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

        # IMPORTANTE: Force uf_origem = "SP"
        uf_origem = "SP"

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
            "uf_origem": uf_origem,  # ✓ ADICIONADO
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

        # Upload em batch a cada 50 documentos
        if len(batch) >= 50:
            index.upsert(vectors=batch, namespace="")
            print(f"   📤 {total} enviados...")
            batch = []

    # Upload final do batch
    if batch:
        index.upsert(vectors=batch, namespace="")
        print(f"   📤 {total} enviados (final)...")

    print(f"\n✅ SP corrigido!")
    print(f"   Total enviados: {total}")
    print(f"   Total ignorados: {ignorados}")

    # Stats finais
    stats = index.describe_index_stats()
    print(f"   Vetores no índice: {stats.get('total_vector_count', 'N/A')}")

if __name__ == "__main__":
    fix_sp_metadata()
