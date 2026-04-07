"""
Mescla os arquivos cbenef_{UF}.csv (raiz) com beneficios_{uf}.csv (database),
remove duplicatas pela coluna codigo_cbenef e salva o resultado consolidado
em database_tributaria_*/beneficios_{uf}.csv.

UFs processadas: SC, PR, RJ, RS, GO

Uso:
    python merge_beneficios_estados.py
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATABASE_DIR = next(
    (os.path.join(BASE_DIR, d) for d in sorted(os.listdir(BASE_DIR)) if d.startswith("database_tributaria_")),
    None,
)

if not DATABASE_DIR:
    print("❌ Diretório database_tributaria_* não encontrado.")
    sys.exit(1)

UFS = ["SC", "PR", "RJ", "RS", "GO"]


def merge_uf(uf: str):
    raiz = os.path.join(BASE_DIR, f"cbenef_{uf}.csv")
    database = os.path.join(DATABASE_DIR, f"beneficios_{uf.lower()}.csv")
    saida = os.path.join(DATABASE_DIR, f"beneficios_{uf.lower()}.csv")

    frames = []

    if os.path.exists(raiz):
        df_raiz = pd.read_csv(raiz, encoding="utf-8-sig", dtype=str)
        df_raiz.columns = df_raiz.columns.str.strip()
        frames.append(df_raiz)
        print(f"  📂 raiz:     {len(df_raiz):>5} linhas")
    else:
        print(f"  📂 raiz:     NÃO EXISTE")

    if os.path.exists(database):
        df_db = pd.read_csv(database, encoding="utf-8-sig", dtype=str)
        df_db.columns = df_db.columns.str.strip()
        frames.append(df_db)
        print(f"  📂 database: {len(df_db):>5} linhas")
    else:
        print(f"  📂 database: NÃO EXISTE")

    if not frames:
        print(f"  ⚠️  Nenhum arquivo encontrado para {uf}, pulando.")
        return

    df_merged = pd.concat(frames, ignore_index=True)

    # Garante que uf_origem está preenchido
    df_merged["uf_origem"] = df_merged["uf_origem"].fillna(uf).replace("nan", uf).str.strip().str.upper()

    # Remove duplicatas: prioriza o registro com mais campos preenchidos
    df_merged["_score"] = df_merged.apply(
        lambda r: sum(1 for v in r if str(v).strip() not in ("", "nan", "-")), axis=1
    )
    df_merged = df_merged.sort_values("_score", ascending=False)
    df_merged = df_merged.drop_duplicates(subset=["codigo_cbenef"], keep="first")
    df_merged = df_merged.drop(columns=["_score"])

    # Ordena pelo código
    df_merged = df_merged.sort_values("codigo_cbenef").reset_index(drop=True)

    df_merged.to_csv(saida, index=False, encoding="utf-8-sig")
    print(f"  ✅ Resultado: {len(df_merged):>5} registros únicos → {os.path.basename(saida)}")


def main():
    print(f"Base:     {BASE_DIR}")
    print(f"Database: {DATABASE_DIR}\n")

    for uf in UFS:
        print(f"=== {uf} ===")
        merge_uf(uf)
        print()

    print("Merge concluido! Arquivos prontos para ingestao no Pinecone.")
    print("Proximo passo: python ingest_beneficios_estados.py")


if __name__ == "__main__":
    main()