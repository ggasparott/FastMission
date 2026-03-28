import docx
import csv
import re
import sys

"""
Script para extrair dados da tabela do arquivo DOC do SPED (Tabela 4.3.13) para CSV.
Uso:
    python extract_sped_4_3_13_to_csv.py Tabela_4_3_13_Versao_1.33.doc output.csv

O script espera que o arquivo DOC contenha uma tabela com as seguintes colunas:
- Código
- Descrição
- Observação (se houver)

Ajuste os índices das colunas conforme necessário.
"""

def extract_table_from_doc(doc_path):
    doc = docx.Document(doc_path)
    # Procura a primeira tabela do documento
    for table in doc.tables:
        # Assume que a primeira tabela relevante é a desejada
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)
        return rows
    return []

def clean_text(text):
    # Remove quebras de linha e espaços extras
    return re.sub(r'\s+', ' ', text).strip()

def main():
    if len(sys.argv) != 3:
        print("Uso: python extract_sped_4_3_13_to_csv.py <input.doc> <output.csv>")
        sys.exit(1)
    input_doc = sys.argv[1]
    output_csv = sys.argv[2]

    rows = extract_table_from_doc(input_doc)
    if not rows or len(rows) < 2:
        print("Tabela não encontrada ou vazia no documento.")
        sys.exit(1)

    # Assume que a primeira linha é o cabeçalho
    header = rows[0]
    data_rows = rows[1:]

    # Ajuste os índices conforme o layout da tabela
    # Exemplo: Código = 0, Descrição = 1, Observação = 2 (se existir)
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['codigo', 'descricao', 'observacao'])
        for row in data_rows:
            codigo = clean_text(row[0]) if len(row) > 0 else ''
            descricao = clean_text(row[1]) if len(row) > 1 else ''
            observacao = clean_text(row[2]) if len(row) > 2 else ''
            writer.writerow([codigo, descricao, observacao])
    print(f"Extração concluída. Dados salvos em {output_csv}")

if __name__ == "__main__":
    main()
