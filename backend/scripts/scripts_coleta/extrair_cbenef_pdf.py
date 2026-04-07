"""
Extrai tabelas cBenef de PDFs oficiais das SEFAZs estaduais e gera CSVs
no padrão do projeto para ingestão no Pinecone.

PDFs suportados (em database_tributaria_*/):
  - Tabela-codigo-de-beneficio-X-CST_versao_2026-03-09.pdf  → RJ
  - Tabela 5.2A (Cbenef).pdf                                 → SC
  - tabela_cbenef_pr_portal_nacional_abril_2025_v25.pdf      → PR

Uso:
    python extrair_cbenef_pdf.py

Saída:
    database_tributaria_*/beneficios_rj.csv
    database_tributaria_*/beneficios_sc.csv
    database_tributaria_*/beneficios_pr.csv
"""

import os
import re
import sys
import csv

import pdfplumber
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATABASE_DIR = next(
    (os.path.join(BASE_DIR, d) for d in sorted(os.listdir(BASE_DIR)) if d.startswith("database_tributaria_")),
    None,
)

if not DATABASE_DIR:
    print("❌ Diretório database_tributaria_* não encontrado.")
    sys.exit(1)

# Mapeamento: nome do PDF → UF
PDFS = {
    "Tabela-codigo-de-beneficio-X-CST_versao_2026-03-09.pdf": "RJ",
    "Tabela 5.2A (Cbenef).pdf": "SC",
    "tabela_cbenef_pr_portal_nacional_abril_2025_v25.pdf": "PR",
}

TIPO_BENEFICIO_MAP = {
    "0": "Não Incidência",
    "1": "Isenção",
    "2": "Redução de Base de Cálculo",
    "3": "Diferimento",
    "4": "Substituição Tributária",
    "5": "Crédito Presumido",
    "6": "Suspensão",
    "9": "Sem Benefício",
}

CST_CSOSN_MAP = {
    "Não Incidência":             ("41",          "400"),
    "Isenção":                    ("40",          "400 ou 103/300"),
    "Redução de Base de Cálculo": ("20",          "500"),
    "Diferimento":                ("51",          "900"),
    "Substituição Tributária":    ("10",          "201 / 202"),
    "Crédito Presumido":          ("00",          "102"),
    "Suspensão":                  ("50",          "400"),
    "Sem Benefício":              ("00 / 10 / 90", "101 / 102 / 500"),
}

RICMS = {
    "RJ": "RICMS-RJ Decreto 27.427/2000",
    "SC": "RICMS-SC Decreto 2.870/2001",
    "PR": "RICMS-PR Decreto 7.871/2017",
}


def mapear_tipo(codigo: str, uf: str) -> str:
    """Infere tipo de benefício pelo dígito após o prefixo UF+8."""
    # Padrão: UF + "8" + tipo + sequencial  (ex: RJ810001 → tipo='1'=Isenção)
    padrao = rf"^{uf}8(\d)"
    m = re.match(padrao, codigo, re.IGNORECASE)
    if m:
        return TIPO_BENEFICIO_MAP.get(m.group(1), "Outros")
    # Fallback: verifica se há 99 no código → sem benefício
    if "99" in codigo:
        return "Sem Benefício"
    return "Outros"


def extrair_tabela_pdf(pdf_path: str, uf: str) -> list[dict]:
    """Extrai linhas de tabela do PDF usando pdfplumber."""
    resultados = []

    # Regex para detectar código cBenef (ex: RJ810001, SC800001, PR830001)
    re_codigo = re.compile(rf"\b{uf}8\d{{5}}\b", re.IGNORECASE)

    print(f"\n📄 Processando: {os.path.basename(pdf_path)} ({uf})")

    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        print(f"   Páginas: {total_paginas}")

        for num, pagina in enumerate(pdf.pages, 1):
            # Tenta extrair tabela estruturada primeiro
            tabelas = pagina.extract_tables()
            if tabelas:
                for tabela in tabelas:
                    for row in tabela:
                        if not row:
                            continue
                        # Converte células para string
                        celulas = [str(c).strip() if c else "" for c in row]
                        linha_str = " | ".join(celulas)

                        # Procura código cBenef na linha
                        m = re_codigo.search(linha_str)
                        if not m:
                            continue

                        codigo = m.group(0).upper()
                        # Remove o código da linha para extrair descrição
                        descricao_raw = linha_str.replace(codigo, "").strip(" |")
                        # Limpa pipes e espaços duplos
                        descricao = re.sub(r"\s*\|\s*", " - ", descricao_raw).strip(" -")
                        descricao = re.sub(r"\s{2,}", " ", descricao)

                        if not descricao or len(descricao) < 3:
                            descricao = f"Benefício {codigo}"

                        tipo = mapear_tipo(codigo, uf)
                        cst, csosn = CST_CSOSN_MAP.get(tipo, ("00", "102"))

                        resultados.append({
                            "codigo_cbenef": codigo,
                            "descricao_produto_operacao": descricao[:250],
                            "tipo_beneficio": tipo,
                            "regime_tributario_permitido": "Ambos (Normal / Simples)",
                            "cst_sugerido_regime_normal": cst,
                            "csosn_sugerido_simples_nacional": csosn,
                            "fundamentacao_legal": RICMS.get(uf, f"RICMS-{uf}"),
                            "regra_validacao_agente_ia": f"Verificar enquadramento do produto no benefício {codigo} conforme {RICMS.get(uf, f'RICMS-{uf}')}.",
                            "uf_origem": uf,
                        })

            else:
                # Fallback: extrai texto puro linha por linha
                texto = pagina.extract_text() or ""
                for linha in texto.splitlines():
                    m = re_codigo.search(linha)
                    if not m:
                        continue

                    codigo = m.group(0).upper()
                    descricao = linha.replace(codigo, "").strip()
                    descricao = re.sub(r"\s{2,}", " ", descricao).strip()

                    if not descricao or len(descricao) < 3:
                        descricao = f"Benefício {codigo}"

                    tipo = mapear_tipo(codigo, uf)
                    cst, csosn = CST_CSOSN_MAP.get(tipo, ("00", "102"))

                    resultados.append({
                        "codigo_cbenef": codigo,
                        "descricao_produto_operacao": descricao[:250],
                        "tipo_beneficio": tipo,
                        "regime_tributario_permitido": "Ambos (Normal / Simples)",
                        "cst_sugerido_regime_normal": cst,
                        "csosn_sugerido_simples_nacional": csosn,
                        "fundamentacao_legal": RICMS.get(uf, f"RICMS-{uf}"),
                        "regra_validacao_agente_ia": f"Verificar enquadramento do produto no benefício {codigo} conforme {RICMS.get(uf, f'RICMS-{uf}')}.",
                        "uf_origem": uf,
                    })

    # Remove duplicatas pelo código
    vistos = set()
    unicos = []
    for r in resultados:
        if r["codigo_cbenef"] not in vistos:
            vistos.add(r["codigo_cbenef"])
            unicos.append(r)

    print(f"   ✅ Extraídos: {len(unicos)} registros únicos")
    return unicos


def salvar_csv(registros: list[dict], uf: str):
    caminho = os.path.join(DATABASE_DIR, f"beneficios_{uf.lower()}.csv")
    campos = [
        "codigo_cbenef", "descricao_produto_operacao", "tipo_beneficio",
        "regime_tributario_permitido", "cst_sugerido_regime_normal",
        "csosn_sugerido_simples_nacional", "fundamentacao_legal",
        "regra_validacao_agente_ia", "uf_origem",
    ]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    print(f"   💾 Salvo: {caminho} ({len(registros)} linhas)")


def main():
    print(f"📁 Database: {DATABASE_DIR}")
    total_geral = 0

    for nome_pdf, uf in PDFS.items():
        pdf_path = os.path.join(DATABASE_DIR, nome_pdf)
        if not os.path.exists(pdf_path):
            print(f"\n⚠️  PDF não encontrado, pulando: {nome_pdf}")
            continue

        registros = extrair_tabela_pdf(pdf_path, uf)

        if registros:
            salvar_csv(registros, uf)
            total_geral += len(registros)
        else:
            print(f"   ⚠️  Nenhum registro extraído de {nome_pdf}")

    print(f"\n🏁 Concluído! Total de registros gerados: {total_geral}")
    print("   Próximo passo: rode o ingest_beneficios_estados.py para enviar ao Pinecone.")


if __name__ == "__main__":
    main()
