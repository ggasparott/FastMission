
import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_tipi_csv(diretorio):
    caminho = os.path.join(diretorio, "tipi.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig', header=0)

def processar_e_inserir_tipi ():
    index = get_pinecone_index()
    # Busca o diretório de dados a partir da raiz do projeto
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    diretorios = [d for d in os.listdir(base_path) if d.startswith('database_tributaria_')]
    diretorio = max(diretorios, default=None)
    if diretorio:
        diretorio = os.path.join(base_path, diretorio)
    if not diretorio or not os.path.isdir(diretorio):
        print("Nenhum diretório de mapeamento tipi encontrado.")
        return
    df = carregar_tipi_csv(diretorio)
    total = 0
    ignorados = 0
    for _, row in df.iterrows():
        ncm = str(row.get('ncm', '')).strip()
        descricao = str(row.get('descricao', '')).strip()
        aliquota = str(row.get('aliquota', '')).strip()
        codigo_ex = str(row.get('codigo_ex', '')).strip()
        observacao = str(row.get('observacao', '')).strip()
        if not ncm or not descricao:
            print(f"Ignorado: NCM inválido: '{ncm}' | Descrição: '{descricao}'")
            ignorados += 1
            continue

        texto = f"cbenef: {ncm} | {descricao} | observação: {observacao}"
        metadados = {
            "ncm": ncm,
            "descricao": descricao,
            "aliquota": aliquota,
            "observacao": observacao,
        }
        vetor = build_query_vector(texto)
        if not vetor or all(v == 0 for v in vetor):
            print(f"Vetor vazio para: {texto}")
        pinecone_doc = {
            "id": f"tipi_{ncm}",
            "values": vetor,
            "metadata": metadados
        }
        print(f"Enviando: {pinecone_doc}")
        index.upsert([pinecone_doc])
        total += 1
    print(f"Total enviados: {total}, Ignorados: {ignorados}")
    print("Colunas:", df.columns.tolist())
    print(df.head(10))

if __name__ == "__main__":
    processar_e_inserir_tipi()
