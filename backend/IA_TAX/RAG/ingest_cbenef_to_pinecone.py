
import os
import sys
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.IA_TAX.RAG.rag import get_pinecone_index, build_query_vector

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def carregar_cbenef_csv(diretorio):
    caminho = os.path.join(diretorio, "mapeamento_cbenef_cst_regime.csv")
    return pd.read_csv(caminho, encoding='utf-8-sig', header=0)

def processar_e_inserir_cbenef():
    index = get_pinecone_index()
    # Busca o diretório de dados a partir da raiz do projeto
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    diretorios = [d for d in os.listdir(base_path) if d.startswith('database_tributaria_')]
    diretorio = max(diretorios, default=None)
    if diretorio:
        diretorio = os.path.join(base_path, diretorio)
    if not diretorio or not os.path.isdir(diretorio):
        print("Nenhum diretório de mapeamento cbenef encontrado.")
        return
    df = carregar_cbenef_csv(diretorio)
    total = 0
    ignorados = 0
    for _, row in df.iterrows():
        codigo_cbenef = str(row.get('codigo_cbenef', '')).strip()
        descricao = str(row.get('descricao_produto_operacao', '')).strip()
        tipo_beneficio = str(row.get('tipo_beneficio', '')).strip()
        regime = str(row.get('regime_tributario_permitido', '')).strip()
        cst = str(row.get('cst_sugerido_regime_normal', '')).strip()
        csosn = str(row.get('csosn_sugerido_simples_nacional', '')).strip()
        fundamentacao = str(row.get('fundamentacao_legal', '')).strip()
        regra = str(row.get('regra_validacao_agente_ia', '')).strip()

        if not codigo_cbenef or not descricao:
            print(f"Ignorado: codigo_cbenef inválido: '{codigo_cbenef}' | Descrição: '{descricao}'")
            ignorados += 1
            continue

        texto = f"cbenef: {codigo_cbenef} | {descricao} | tipo: {tipo_beneficio} | regime: {regime} | CST: {cst} | CSOSN: {csosn} | fundamentação: {fundamentacao} | regra: {regra}"
        metadados = {
            "codigo_cbenef": codigo_cbenef,
            "descricao_produto_operacao": descricao,
            "tipo_beneficio": tipo_beneficio,
            "regime_tributario_permitido": regime,
            "cst_sugerido_regime_normal": cst,
            "csosn_sugerido_simples_nacional": csosn,
            "fundamentacao_legal": fundamentacao,
            "regra_validacao_agente_ia": regra
        }
        vetor = build_query_vector(texto)
        if not vetor or all(v == 0 for v in vetor):
            print(f"Vetor vazio para: {texto}")
        pinecone_doc = {
            "id": f"cbenef_{codigo_cbenef}",
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
    processar_e_inserir_cbenef()
