import pdfplumber
import os
import re
def extrair_beneficios_fiscais_pdf(pdf_path, termos=["benefício fiscal", "benefícios fiscais", "incentivo fiscal", "isenção", "redução de base", "crédito presumido"]):
    resultados = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            if texto:
                    for termo in termos:
                        if termo.lower() in texto.lower():
                            # Tenta extrair código, artigo e descrição usando regex simples
                            linhas = texto.splitlines()
                            for linha in linhas:
                                if termo.lower() in linha.lower():
                                    # Busca por código (ex: SP010340), artigo e descrição
                                    codigo = ''
                                    artigo = ''
                                    descricao = ''
                                    # Código: começa com SP e números
                                    cod_match = re.search(r'(SP\d{6,})', linha)
                                    if cod_match:
                                        codigo = cod_match.group(1)
                                    # Artigo: busca por "Artigo ... do Anexo ..."
                                    art_match = re.search(r'(Artigo [^\-]+)', linha)
                                    if art_match:
                                        artigo = art_match.group(1)
                                    # Descrição: após "Isenção -" ou "Redução de Base de Cálculo -" ou "Diferimento -" ou "Suspensão -"
                                    desc_match = re.search(r'(Isenção|Redução de Base de Cálculo|Diferimento|Suspensão|Não incidência)\s*-\s*(.*)', linha)
                                    if desc_match:
                                        descricao = desc_match.group(2)
                                    else:
                                        descricao = linha
                                    resultados.append({
                                        "pagina": i + 1,
                                        "termo": termo,
                                        "codigo": codigo,
                                        "artigo": artigo,
                                        "descricao": descricao,
                                        "linha": linha
                                    })
    return resultados

if __name__ == "__main__":
    pdf_path = os.path.join("Tabela-cBenef-SP-v20260313.pdf")
    resultados = extrair_beneficios_fiscais_pdf(pdf_path)
    if resultados:
        for r in resultados:
            print(f"\n--- Página {r['pagina']} (termo: {r['termo']}) ---\n")
            print(r['linha'])  # Mostra até 1500 caracteres do trecho
    else:
        print("Nenhum benefício fiscal encontrado no PDF.")
    import csv

    def salvar_beneficios_csv(resultados, csv_path):
        campos = ["pagina", "termo", "codigo", "artigo", "descricao", "linha"]
        with open(csv_path, "w", newline='', encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for r in resultados:
                writer.writerow(r)

    if __name__ == "__main__":
        pdf_path = os.path.join("Tabela-cBenef-SP-v20260313.pdf")
        resultados = extrair_beneficios_fiscais_pdf(pdf_path)
        if resultados:
            for r in resultados:
                print(f"\n--- Página {r['pagina']} (termo: {r['termo']}) ---\n")
                print(r['linha'])
            # Salva em CSV estruturado
            csv_path = os.path.join("beneficios_fiscais_extraidos.csv")
            salvar_beneficios_csv(resultados, csv_path)
            print(f"\nArquivo CSV salvo em: {csv_path}")
        else:
            print("Nenhum benefício fiscal encontrado no PDF.")
