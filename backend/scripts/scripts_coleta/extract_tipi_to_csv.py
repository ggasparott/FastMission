import pdfplumber
import csv
import re


# Caminho do PDF TIPI
TIPI_PDF = 'tipi.pdf'
TIPI_CSV = 'tipi.csv'

def extract_tipi_to_csv(pdf_path, csv_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                # Captura linhas do tipo: 0201.10.00 - Carcaças e meias-carcaças 0
                match = re.match(r'^(\d{4}(?:\.\d{2})?(?:\.\d{2})?)\s*-\s*(.+?)\s+(\d+)$', line)
                if match:
                    ncm = match.group(1)
                    descricao = match.group(2)
                    aliquota = match.group(3)
                    rows.append([ncm, descricao, aliquota, ''])
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ncm', 'descricao', 'aliquota', 'observacao'])
        writer.writerows(rows)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Uso: python extract_tipi_to_csv.py <input.pdf> <output.csv>")
        sys.exit(1)
    extract_tipi_to_csv(sys.argv[1], sys.argv[2])
