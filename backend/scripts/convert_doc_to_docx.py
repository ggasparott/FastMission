import sys
import os

"""
Script para converter arquivos .doc para .docx usando o Microsoft Word via pywin32 (Windows).
Uso:
    python convert_doc_to_docx.py arquivo.doc
O arquivo .docx será salvo no mesmo diretório.
Requer: pip install pywin32
"""

def convert_doc_to_docx(doc_path):
    import win32com.client
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    doc_path = os.path.abspath(doc_path)
    docx_path = os.path.splitext(doc_path)[0] + '.docx'
    try:
        doc = word.Documents.Open(doc_path)
        doc.SaveAs(docx_path, FileFormat=16)  # 16 = wdFormatDocumentDefault (docx)
        doc.Close()
        print(f'Arquivo convertido: {docx_path}')
    except Exception as e:
        print(f'Erro ao converter: {e}')
    finally:
        word.Quit()

def main():
    if len(sys.argv) != 2:
        print('Uso: python convert_doc_to_docx.py arquivo.doc')
        sys.exit(1)
    doc_path = sys.argv[1]
    if not os.path.isfile(doc_path):
        print(f'Arquivo não encontrado: {doc_path}')
        sys.exit(1)
    convert_doc_to_docx(doc_path)

if __name__ == '__main__':
    main()
