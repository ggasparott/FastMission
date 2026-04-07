import docx
import csv
import re
import sys

"""
Script para extrair dados da tabela do arquivo DOC do SPED (Tabela 4.3.10) para CSV.
Uso:
    python extract_sped_4_3_10_to_csv.py Tabela_4_3_10_Versao_1.24.doc output.csv

O script espera que o arquivo DOC contenha uma tabela com as seguintes colunas:
- Código
- Descrição
- Observação (se houver)

Ajuste os índices das colunas conforme necessário.
"""


def extract_table_from_docx(docx_path):
    doc = docx.Document(docx_path)
    # Procura a primeira tabela do documento
    for table in doc.tables:
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
        print("\n[ERRO] Número de argumentos inválido.")
        print(f"Argumentos recebidos: {sys.argv[1:]}")
        print("\nUso correto:")
        print("    python extract_sped_4_3_10_to_csv.py Tabela_4_3_10_Versao_1.24.docx tabela_4_3_10.csv")
        print("\nCertifique-se de passar o caminho correto do arquivo DOCX e o nome do CSV de saída.")
        sys.exit(1)
    input_docx = sys.argv[1]
    output_csv = sys.argv[2]

    rows = extract_table_from_docx(input_docx)
    if not rows or len(rows) < 2:
        print("Tabela não encontrada ou vazia no documento.\nVerifique se o arquivo está no formato esperado.")
        sys.exit(1)

    # Assume que a primeira linha é o cabeçalho
    header = rows[0]
    data_rows = rows[1:]

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
