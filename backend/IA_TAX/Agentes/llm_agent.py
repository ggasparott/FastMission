# Busca relevante no RAG baseada na pergunta do usuário
def consultar_rag_pergunta_usuario(pergunta_usuario, top_k=10):
    from backend.IA_TAX.RAG.rag import build_query_vector, get_pinecone_index
    index = get_pinecone_index()
    query_vector = build_query_vector(pergunta_usuario)
    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
    contexto = [m.get("metadata", {}).get("descricao", "") for m in matches if m.get("metadata", {}).get("descricao")]
    return contexto
import warnings
warnings.filterwarnings("ignore", message='Field "model_id" has conflict with protected namespace "model_"')
warnings.filterwarnings("ignore", message='Field "model_provider" has conflict with protected namespace "model_"')

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
import sys
import warnings
from agno.agent import Agent
from agno.knowledge import Knowledge


# Silencia avisos do Pydantic
warnings.filterwarnings("ignore", category=UserWarning, module='pydantic')

# Ajuste de path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.tools.function import Function  # Forma recomendada de envolver funções

# Suas importações locais
from backend.skills.validate_ncm import buscar_ncm_sugerido 
from backend.skills.validate_reforma import validar_produto_reforma

from backend.IA_TAX.RAG.rag import retrieve_fiscal_context, get_pinecone_index


# Importa prompts
from backend.IA_TAX.Agentes.prompts import montar_prompt_llm, exemplos_few_shot, montar_prompt_com_exemplos
from pinecone import ServerlessSpec
from agno.vectordb.pineconedb.pineconedb import PineconeDb
from agno.knowledge.knowledge import Knowledge
def consultar_rag(descricao, ncm, regime_empresa, cnae, uf_origem, uf_destino, csv_usuario=None, top_k=10, usar_exemplos=True):
    """
    Consulta regras fiscais relevantes para um produto usando RAG e monta o prompt para o LLM.
    Se csv_usuario for fornecido, inclui a planilha no prompt.
    Se usar_exemplos=True, inclui exemplos few-shot no prompt.
    """
    print("descricao:", descricao)
    print("ncm:", ncm)
    print("regime_empresa:", regime_empresa)
    print("cnae:", cnae)
    print("uf_origem:", uf_origem)
    print("uf_destino:", uf_destino)
    print("top_k:", top_k)
    index = get_pinecone_index()
    matches = retrieve_fiscal_context(
        index=index,
        descricao=descricao,
        ncm=ncm,
        regime_empresa=regime_empresa,
        cnae_principal=cnae,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        top_k=top_k
    )
    # Extrai descrições e fontes para montar contexto
    contexto_textos = []
    fontes = []
    for m in matches:
        desc = m.get("descricao") or m.get("texto") or ""
        fonte = m.get("fonte")
        if desc:
            contexto_textos.append(desc)
        if fonte:
            fontes.append(fonte)
    contexto_rag = "\n".join(contexto_textos) if contexto_textos else "[Nenhum contexto legal encontrado no RAG]"
    fontes_str = ", ".join(set(fontes)) if fontes else None
    # Monta prompt aprimorado
    prompt = f"""
Contexto legal extraído do RAG:
{contexto_rag}
"""
    if fontes_str:
        prompt += f"\nFontes legais: {fontes_str}\n"
    prompt += f"\nPergunta do usuário:\n{{descricao}}\n\nInstruções:\n- Responda de forma objetiva e cite as fontes legais sempre que possível.\n- Se não houver base legal clara, explique o motivo.\n- Use markdown para formatar a resposta.\n"
    if csv_usuario:
        if usar_exemplos:
            exemplos = exemplos_few_shot()
            prompt = montar_prompt_com_exemplos(contexto_textos, csv_usuario, exemplos)
        else:
            prompt = montar_prompt_llm(contexto_textos, csv_usuario)
        return {
            "prompt": prompt,
            "matches": matches,
            "contexto_usado": bool(contexto_textos)
        }
    else:
        return {
            "prompt": prompt,
            "matches": matches,
            "contexto_usado": bool(contexto_textos)
        }

AGNO_API_KEY = os.getenv("OPENAI_API_KEY")

# 1. Configuração do Modelo (Corrigido)
model = OpenAIChat(id="gpt-4o", api_key=AGNO_API_KEY)


# 2. Knowledge para o Agente usando Pinecone
vector_db = PineconeDb(
    name="fiscal-reforma-v1",
    api_key=os.getenv("PINECONE_API_KEY", "").strip(),
    dimension=512,  # Dimensão padrão do text-embedding-3-small / ada-002
    spec=ServerlessSpec(
        cloud="aws", 
        region="us-east-1"  # Ajuste para a região onde seu índice foi criado
    ),
    embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=512)
    )

knowledge_base = Knowledge(
    vector_db=vector_db,
)
# 3. Configuração do Agente
FastTax = Agent(
    name="FastTax Agent",
    model=model,
    tools=[
        validar_produto_reforma, 
        buscar_ncm_sugerido, 
        ],
    knowledge=knowledge_base,
    add_knowledge_to_context=True,  # injeta contexto automaticamente
    instructions=[
        "Você é um consultor tributário sênior, extremamente técnico e rigoroso com a legislação brasileira.",
        
        "REGRA 1 - VALIDAÇÃO OBRIGATÓRIA: SEMPRE valide o NCM fornecido pelo usuário usando a ferramenta 'buscar_ncm_sugerido'. Nunca pule esta etapa.",
        
        "REGRA 2 - BLOQUEIO DE NCM INVÁLIDO: Se a ferramenta retornar que o NCM é 'INVALIDO' ou 'não encontrado', VOCÊ DEVE PARAR IMEDIATAMENTE. Não sugira CFOP, não sugira CST e não calcule impostos. Apenas informe ao usuário que o NCM não existe e peça para ele corrigir o código antes de prosseguir.",
        
        "REGRA 3 - CÁLCULO: Apenas após confirmar que o NCM é 'VALIDO', utilize a ferramenta 'validar_produto_reforma' e o seu conhecimento (RAG) para sugerir regras fiscais, CFOP, alíquotas e benefícios.",
        
        "Não faça suposições de NCM baseado apenas na descrição do produto se o usuário tiver fornecido um código numérico. Siga a estrita legalidade."
    ],
    markdown=True
)

if __name__ == "__main__":
    # Teste: busca relevante baseada na pergunta do usuário
    pergunta = "Quais regras fiscais se aplicam para venda de camiseta de algodão de SP para RJ?"
    resposta = FastTax.cli_app()
    print(resposta)