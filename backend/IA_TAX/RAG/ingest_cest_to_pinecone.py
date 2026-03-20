import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_cest_csv(diretorio):
    caminho = os.path.join(diretorio, "tabela_cest_consolidada.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig', header=1)  # Garantir que a primeira linha seja tratada como cabeçalho

def is_cest_valido(cest):
    # CEST válido: não vazio, não texto, geralmente formato numérico com pontos
    return isinstance(cest, str) and cest.replace('.', '').isdigit() and len(cest) > 0

def processar_e_inserir_cest_debug():
    index = get_pinecone_index()
    diretorio = max([d for d in os.listdir('.') if d.startswith('database_tributaria_')], default=None)
    if not diretorio:
        print("Nenhum diretório de dados tributários encontrado.")
        return
    df = carregar_cest_csv(diretorio)
    total = 0
    ignorados = 0
     
    for _, row in df.iterrows():
        cest = str(row.get('CEST', '')).strip()
        ncm = str(row.get('NCM/SH', '')).strip()
        descricao = str(row.get('DESCRIÇÃO', '')).strip()
        if not is_cest_valido(cest) or not ncm or not descricao:
            print(f"Ignorado: CEST inválido: '{cest}' | NCM: '{ncm}' | Descrição: '{descricao}'")
            ignorados += 1
            continue
        texto = f"CEST: {cest} | NCM: {ncm} | {descricao}"
        metadados = {
            "cest": cest,
            "ncm": ncm,
            "descricao": descricao,
            "fonte": "CONFAZ"
        }
        vetor = build_query_vector(texto)
        if not vetor or all(v == 0 for v in vetor):
            print(f"Vetor vazio para: {texto}")
        pinecone_doc = {
            "id": f"cest_{cest}",
            "values": vetor,
            "metadata": metadados
        }
        print(f"Enviando: {pinecone_doc}")
        index.upsert([pinecone_doc])
        total += 1
    print(f"Total enviados: {total}, Ignorados: {ignorados}")
    print("Colunas:", df.columns.tolist())  # Debug: mostrar colunas para verificar nomes corretos
    print(df.head(10))  #
if __name__ == "__main__":
    processar_e_inserir_cest_debug()