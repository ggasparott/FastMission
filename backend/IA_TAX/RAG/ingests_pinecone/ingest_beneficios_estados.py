"""
Ingest unificado de benefícios fiscais de múltiplos estados para o Pinecone.

Lê todos os arquivos beneficios_{uf}.csv do diretório database_tributaria_*
e faz upsert no índice Pinecone com metadata uf_origem para filtro no RAG.

Uso:
    python ingest_beneficios_estados.py [--uf SP,MG,RJ]  # opcional: filtra UFs específicas

Exemplo:
    python ingest_beneficios_estados.py           # todos os estados encontrados
    python ingest_beneficios_estados.py --uf RS   # só RS
"""

import os
import sys
import argparse
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Carrega .env da raiz do projeto
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.env")))

from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

def _encontrar_raiz() -> str:
    """Sobe a árvore de diretórios até encontrar a pasta database_tributaria_*."""
    candidato = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):  # sobe até 6 níveis
        for nome in os.listdir(candidato):
            if nome.startswith("database_tributaria_") and os.path.isdir(os.path.join(candidato, nome)):
                return candidato
        candidato = os.path.dirname(candidato)
    # Fallback: cwd
    return os.getcwd()

BASE_DIR = _encontrar_raiz()
DATABASE_DIR = next(
    (os.path.join(BASE_DIR, d) for d in sorted(os.listdir(BASE_DIR)) if d.startswith("database_tributaria_")),
    None,
)


def listar_csvs_estados(filtro_ufs: list[str] | None = None) -> list[tuple[str, str]]:
    """Retorna lista de (caminho_csv, uf) para todos os beneficios_{uf}.csv encontrados."""
    arquivos = []
    if not DATABASE_DIR or not os.path.isdir(DATABASE_DIR):
        return arquivos

    for nome in sorted(os.listdir(DATABASE_DIR)):
        if nome.startswith("beneficios_") and nome.endswith(".csv"):
            uf = nome.replace("beneficios_", "").replace(".csv", "").upper()
            if filtro_ufs and uf not in [u.upper() for u in filtro_ufs]:
                continue
            arquivos.append((os.path.join(DATABASE_DIR, nome), uf))

    return arquivos


def processar_csv_estado(index, caminho: str, uf: str) -> tuple[int, int]:
    """Lê o CSV do estado e faz upsert no Pinecone. Retorna (enviados, ignorados)."""
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    total = 0
    ignorados = 0

    # Verifica se tem coluna uf_origem; se não, pula o arquivo
    if "uf_origem" not in df.columns:
        print(f"\n⚠️  Estado: {uf} | Arquivo: {os.path.basename(caminho)} | ❌ Sem coluna 'uf_origem' — IGNORADO")
        return 0, len(df)

    print(f"\n🗺️  Estado: {uf} | Arquivo: {os.path.basename(caminho)} | Linhas: {len(df)}")

    for _, row in df.iterrows():
        codigo = str(row.get("codigo_cbenef", "")).strip()
        descricao = str(row.get("descricao_produto_operacao", "")).strip()

        if not codigo or codigo.lower() == "nan":
            ignorados += 1
            continue
        if not descricao or descricao.lower() == "nan":
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
            print(f"   ⚠️  Vetor vazio para: {codigo} — pulando")
            ignorados += 1
            continue

        doc_id = f"cbenef_{uf_origem}_{codigo}"
        # Pinecone v5: usar format correto
        index.upsert(vectors=[{
            "id": doc_id,
            "values": vetor,
            "metadata": metadados,
        }], namespace="")

        total += 1
        if total % 10 == 0:
            print(f"   📤 {total} enviados...")

    print(f"   ✅ {uf}: {total} enviados, {ignorados} ignorados")
    return total, ignorados


def main():
    parser = argparse.ArgumentParser(description="Ingest cBenef multi-estado → Pinecone")
    parser.add_argument("--uf", type=str, default=None, help="UFs a processar separadas por vírgula (ex: RS,RJ)")
    args = parser.parse_args()

    filtro = [u.strip() for u in args.uf.split(",")] if args.uf else None

    csvs = listar_csvs_estados(filtro)
    if not csvs:
        print("❌ Nenhum arquivo beneficios_{uf}.csv encontrado.")
        print(f"   Diretório verificado: {DATABASE_DIR}")
        print("   Execute primeiro: extrair_cbenef_pdf.py e converter_xlsx_para_csv.py")
        sys.exit(1)

    print(f"📁 Database: {DATABASE_DIR}")
    print(f"📋 Arquivos a processar: {[os.path.basename(c) for c, _ in csvs]}")

    index = get_pinecone_index()
    total_geral = 0
    ignorados_geral = 0

    for caminho, uf in csvs:
        enviados, ignorados = processar_csv_estado(index, caminho, uf)
        total_geral += enviados
        ignorados_geral += ignorados

    print(f"\n🏁 Ingest concluído!")
    print(f"   Total enviados ao Pinecone: {total_geral}")
    print(f"   Total ignorados: {ignorados_geral}")
    print(f"   Estados processados: {[uf for _, uf in csvs]}")


if __name__ == "__main__":
    main()
