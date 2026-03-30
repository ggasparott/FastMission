
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

def carregar_ncm_json(diretorio):
    """Carrega o arquivo tabela_ncm_hierarquica.json gerado pelo coletor."""
    caminho = os.path.join(diretorio, "tabela_ncm_hierarquica.json")
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)

def processar_e_inserir_ncm():
    index = get_pinecone_index()
    diretorio = max([d for d in os.listdir('.') if d.startswith('database_tributaria_')], default=None)
    if not diretorio:
        print("Nenhum diretório de dados tributários encontrado.")
        return
    dados = carregar_ncm_json(diretorio)
    for item in dados:
        texto = f"NCM: {item.get('codigo', '')} - {item.get('descricao', '')}"
        metadados = {
            "ncm": item.get('codigo'),
            "descricao": item.get('descricao'),
            "fonte": "Siscomex",
        }
        vetor = build_query_vector(texto)
        pinecone_doc = {
            "id": f"ncm_{item.get('codigo')}",
            "values": vetor,
            "metadata": metadados
        }
        index.upsert([pinecone_doc])
        print(f"Enviado: {pinecone_doc['id']}")

if __name__ == "__main__":
    processar_e_inserir_ncm()
