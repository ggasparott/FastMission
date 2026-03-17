import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
import sys
import warnings

# Silencia avisos do Pydantic
warnings.filterwarnings("ignore", category=UserWarning, module='pydantic')

# Ajuste de path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.function import Function  # Forma recomendada de envolver funções

# Suas importações locais
from backend.skills import validate_ncm
from backend.skills.validate_reforma import validar_produto_reforma
# Importa funções do RAG (arquivo rag.PY)
from backend.IA_TAX.RAG.rag import retrieve_fiscal_context, get_pinecone_index


def consultar_rag(descricao, ncm, regime_empresa, cnae, uf_origem, uf_destino, top_k=3):
    """Consulta regras fiscais relevantes para um produto usando RAG."""
    index = get_pinecone_index()
    return retrieve_fiscal_context(
        index=index,
        descricao=descricao,
        ncm=ncm,
        regime_empresa=regime_empresa,
        cnae_principal=cnae,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        top_k=top_k
    )

AGNO_API_KEY = os.getenv("OPENAI_API_KEY")

# 1. Configuração do Modelo (Corrigido)
model = OpenAIChat(id="gpt-4o", api_key=AGNO_API_KEY)

# 2. Configuração do Agente
FastTax = Agent(
    name="FastTax Agent",
    model=model,
    tools=[
        validar_produto_reforma, 
        validate_ncm, 
        consultar_rag # Passando a função diretamente (o Agno extrai a docstring)
    ],
    instructions=[
        "Você é um especialista em tributação brasileira.",
        "Sempre valide o NCM antes de sugerir regras fiscais.",
        "Use a ferramenta consultar_rag para obter embasamento legal atualizado."
    ],
    markdown=True
)

if __name__ == "__main__":
    prompt = (
        "Analise o produto: Camiseta de algodão, NCM: 6109.10.00, "
        "Regime: LUCRO_REAL, Origem: SP, Destino: RJ, CNAE: 1411-3/01. "
        "A classificação NCM está correta? Quais regras fiscais se aplicam?"
    )
    
    # Use .print_response para ver a saída formatada ou .run()
    FastTax.print_response(prompt)