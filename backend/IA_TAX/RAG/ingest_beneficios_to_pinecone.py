import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_cest_csv(diretorio):
    caminho = os.path.join(diretorio, "beneficios_fiscais_extraidos.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig', header=0)  # Garantir que a primeira linha seja tratada como cabeçalho



def processar_e_inserir_cest_debug():
    index = get_pinecone_index()
    # Busca o diretório de dados a partir da raiz do projeto
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    diretorios = [d for d in os.listdir(base_path) if d.startswith('database_tributaria_')]
    diretorio = max(diretorios, default=None)
    if diretorio:
        diretorio = os.path.join(base_path, diretorio)
    if not diretorio or not os.path.isdir(diretorio):
        print("Nenhum diretório de beneficios fiscais encontrado.")
        return
    df = carregar_cest_csv(diretorio)
    total = 0
    ignorados = 0
     
    for _, row in df.iterrows():
        codigo = str(row.get('codigo', '')).strip()
        artigo = str(row.get('artigo', '')).strip()
        descricao = str(row.get('descricao', '')).strip()
        termo = str(row.get('termo', '')).strip()
        pagina = str(row.get('pagina', '')).strip()
        linha = str(row.get('linha', '')).strip()

        if not codigo or not descricao:
            print(f"Ignorado: codigo inválido: '{codigo}' | Artigo: '{artigo}' | Descrição: '{descricao}' | Linha: '{linha}' | Página: '{pagina}' | Termo: '{termo}'")
            ignorados += 1
            continue

        texto = f"codigo: {codigo} | artigo: {artigo} | {descricao} | linha: {linha} | página: {pagina} | termo: {termo}"
        metadados = {
            "codigo": codigo,
            "artigo": artigo,
            "descricao": descricao,
            "fonte": "Tabela cBenef SP",
            "pagina": pagina,
            "termo": termo
        }
        vetor = build_query_vector(texto)
        if not vetor or all(v == 0 for v in vetor):
            print(f"Vetor vazio para: {texto}")
        pinecone_doc = {
            "id": f"beneficio_{codigo}",
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