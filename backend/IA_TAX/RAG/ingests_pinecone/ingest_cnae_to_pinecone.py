import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_cnae_csv(diretorio):
    caminho = os.path.join(diretorio, "lista_cnae_subclasses.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig')

def processar_e_inserir_cnae():
    index = get_pinecone_index()
    diretorio = max([d for d in os.listdir('.') if d.startswith('database_tributaria_')], default=None)
    if not diretorio:
        print("Nenhum diretório de dados tributários encontrado.")
        return
    df = carregar_cnae_csv(diretorio)
    for _, row in df.iterrows():
        cnae_id = str(row.get('id', '')).strip()
        descricao = str(row.get('descricao', '')).strip()
        atividades = str(row.get('atividades', '')).strip()
        texto = f"CNAE: {cnae_id} | {descricao} | Atividades: {atividades}"
        # Limitar o texto para não estourar o limite do modelo de embedding
        texto = texto[:4000]
        metadados = {
            "cnae": cnae_id,
            "descricao": descricao,
            "atividades": atividades,
            "fonte": "IBGE/CONCLA"
        }
        vetor = build_query_vector(texto)
        pinecone_doc = {
            "id": f"cnae_{cnae_id}",
            "values": vetor,
            "metadata": metadados
        }
        index.upsert([pinecone_doc])
        print(f"Enviado: {pinecone_doc['id']}")

if __name__ == "__main__":
    processar_e_inserir_cnae()
