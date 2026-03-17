import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_cest_csv(diretorio):
    caminho = os.path.join(diretorio, "tabela_cest_consolidada.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig')

def processar_e_inserir_cest():
    index = get_pinecone_index()
    diretorio = max([d for d in os.listdir('.') if d.startswith('database_tributaria_')], default=None)
    if not diretorio:
        print("Nenhum diretório de dados tributários encontrado.")
        return
    df = carregar_cest_csv(diretorio)
    for _, row in df.iterrows():
        cest = str(row.get('CEST', '')).strip()
        ncm = str(row.get('NCM/SH', '')).strip()
        descricao = str(row.get('DESCRIÇÃO', '')).strip()
        texto = f"CEST: {cest} | NCM: {ncm} | {descricao}"
        metadados = {
            "cest": cest,
            "ncm": ncm,
            "descricao": descricao,
            "fonte": "CONFAZ"
        }
        vetor = build_query_vector(texto)
        pinecone_doc = {
            "id": f"cest_{cest}",
            "values": vetor,
            "metadata": metadados
        }
        index.upsert([pinecone_doc])
        print(f"Enviado: {pinecone_doc['id']}")

if __name__ == "__main__":
    processar_e_inserir_cest()
