"""
Converte a tabela cBenef do RS (XLSX) para CSV no padrão do projeto.
Fonte: https://www.estado.rs.gov.br/upload/arquivos/202405/tabela-cbenef-x-cst-17-05-2024.xlsx

Uso:
    python converter_xlsx_para_csv.py

Saída:
    database_tributaria_2026-03-16/beneficios_rs.csv
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATABASE_DIR = next(
    (os.path.join(BASE_DIR, d) for d in os.listdir(BASE_DIR) if d.startswith("database_tributaria_")),
    None,
)

XLSX_PATH = os.path.join(DATABASE_DIR, "tabela-cbenef-x-cst-17-05-2024.xlsx")
CSV_OUT = os.path.join(DATABASE_DIR, "beneficios_rs.csv")

UF = "RS"


def mapear_tipo_beneficio(codigo: str) -> str:
    """Infere o tipo de benefício pelo 3º dígito do código cBenef."""
    if len(codigo) < 4:
        return "Sem Benefício"
    d = codigo[3]  # Ex: RS800001 -> d='0'
    mapa = {
        "0": "Não Incidência",
        "1": "Isenção",
        "2": "Redução de Base de Cálculo",
        "3": "Diferimento",
        "4": "Substituição Tributária",
        "5": "Crédito Presumido",
        "6": "Suspensão",
        "9": "Sem Benefício",
    }
    return mapa.get(d, "Outros")


def inferir_cst_csosn(tipo: str) -> tuple[str, str]:
    """Retorna CST sugerido e CSOSN com base no tipo de benefício."""
    mapa = {
        "Não Incidência":              ("41", "400"),
        "Isenção":                     ("40", "400 ou 103/300"),
        "Redução de Base de Cálculo":  ("20", "500"),
        "Diferimento":                 ("51", "900"),
        "Substituição Tributária":     ("10", "201 / 202"),
        "Crédito Presumido":           ("00", "102"),
        "Suspensão":                   ("50", "400"),
        "Sem Benefício":               ("00 / 10 / 90", "101 / 102 / 500"),
    }
    return mapa.get(tipo, ("00", "102"))


def converter():
    if not os.path.exists(XLSX_PATH):
        print(f"❌ Arquivo não encontrado: {XLSX_PATH}")
        sys.exit(1)

    print(f"📂 Lendo: {XLSX_PATH}")

    # Tenta ler todas as abas
    xls = pd.ExcelFile(XLSX_PATH)
    print(f"   Abas encontradas: {xls.sheet_names}")

    # Lê a primeira aba que tenha dados
    df_raw = None
    for aba in xls.sheet_names:
        df_tmp = pd.read_excel(XLSX_PATH, sheet_name=aba, header=None)
        if df_tmp.shape[0] > 2:
            df_raw = df_tmp
            print(f"   Usando aba: '{aba}' ({df_tmp.shape[0]} linhas)")
            break

    if df_raw is None:
        print("❌ Nenhuma aba com dados encontrada.")
        sys.exit(1)

    # Mostra as primeiras linhas para diagnóstico
    print("\n🔍 Primeiras 5 linhas brutas:")
    print(df_raw.head(5).to_string())

    # Detecta a linha de cabeçalho (procura por "código" ou "cbenef")
    header_row = 0
    for i, row in df_raw.iterrows():
        row_lower = " ".join(str(v).lower() for v in row.values)
        if "benef" in row_lower or "código" in row_lower or "cst" in row_lower:
            header_row = i
            break

    print(f"\n   Cabeçalho detectado na linha: {header_row}")

    df = pd.read_excel(XLSX_PATH, sheet_name=xls.sheet_names[0], header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"\n🏷️  Colunas detectadas: {df.columns.tolist()}")

    # Mapeia colunas automaticamente (nomes variam por versão do arquivo)
    col_codigo = next((c for c in df.columns if "benef" in c.lower() or "código" in c.lower() or "cod" in c.lower()), df.columns[0])
    col_descricao = next((c for c in df.columns if "descri" in c.lower() or "operação" in c.lower() or "produto" in c.lower()), df.columns[1] if len(df.columns) > 1 else col_codigo)
    col_fund = next((c for c in df.columns if "fund" in c.lower() or "legal" in c.lower() or "base" in c.lower()), None)

    print(f"   Coluna código: '{col_codigo}'")
    print(f"   Coluna descrição: '{col_descricao}'")
    print(f"   Coluna fundamentação: '{col_fund}'")

    linhas = []
    ignorados = 0

    for _, row in df.iterrows():
        codigo = str(row.get(col_codigo, "")).strip()
        descricao = str(row.get(col_descricao, "")).strip()
        fundamentacao = str(row.get(col_fund, "")) .strip() if col_fund else ""

        # Filtra linhas inválidas
        if not codigo or codigo.lower() in ("nan", "código", "cod", "cbenef"):
            ignorados += 1
            continue
        if not descricao or descricao.lower() == "nan":
            ignorados += 1
            continue

        # Padroniza o código com prefixo UF
        if not codigo.upper().startswith(UF):
            codigo = f"{UF}{codigo}"

        tipo = mapear_tipo_beneficio(codigo)
        cst, csosn = inferir_cst_csosn(tipo)

        linhas.append({
            "codigo_cbenef": codigo,
            "descricao_produto_operacao": descricao,
            "tipo_beneficio": tipo,
            "regime_tributario_permitido": "Ambos (Normal / Simples)",
            "cst_sugerido_regime_normal": cst,
            "csosn_sugerido_simples_nacional": csosn,
            "fundamentacao_legal": fundamentacao if fundamentacao and fundamentacao != "nan" else f"RICMS-RS Decreto 37.699/1997",
            "regra_validacao_agente_ia": f"Verificar enquadramento do produto no benefício {codigo} conforme RICMS-RS.",
            "uf_origem": UF,
        })

    df_out = pd.DataFrame(linhas)
    df_out.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

    print(f"\n✅ CSV gerado: {CSV_OUT}")
    print(f"   Registros exportados: {len(linhas)}")
    print(f"   Ignorados: {ignorados}")
    print(f"\n📋 Amostra:")
    print(df_out.head(5).to_string())


if __name__ == "__main__":
    converter()
