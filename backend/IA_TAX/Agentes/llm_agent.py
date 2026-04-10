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

import re
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


from backend.IA_TAX.RAG.rag import retrieve_fiscal_context, get_pinecone_index


# Importa prompts
from backend.IA_TAX.Agentes.prompts import montar_prompt_llm, exemplos_few_shot, montar_prompt_com_exemplos
from pinecone import ServerlessSpec
from agno.vectordb.pineconedb.pineconedb import PineconeDb

from agno.knowledge.knowledge import Knowledge
from backend.IA_TAX.RAG.rag import retrieve_fiscal_context, get_pinecone_index

# Knowledge customizado para busca fiscal com filtros
class FiscalContextResult:
    def __init__(self, data):
        self.data = data
    def to_dict(self):
        return self.data

class CustomKnowledge(Knowledge):
    def search(self, query, **kwargs):
        descricao = kwargs.get("descricao", "")
        ncm = kwargs.get("ncm", "")
        regime_empresa = kwargs.get("regime_empresa", "")
        cnae_principal = kwargs.get("cnae_principal", "")
        uf_origem = kwargs.get("uf_origem", "")
        uf_destino = kwargs.get("uf_destino", "")
        top_k = kwargs.get("top_k", 5)
        index = get_pinecone_index()
        # Melhoria: extrair só termos técnicos para busca semântica
        def extract_technical_terms(text):
            stopwords = set([
                "qual", "é", "o", "a", "melhor", "para", "como", "deve", "usar", "utilizar", "ncm", "importado", "produto",
                "classificação", "meu", "minha", "uma", "um", "ser", "com", "que", "do", "dos", "das", "no", "na", "se", "por",
                "sugiro", "recomendo", "confirme", "procure", "contato", "direto", "verifique", "fornecedor", "fabricante", "profissional"
            ])
            text = re.sub(r"[\.,;:!?]", "", text.lower())
            terms = [w for w in text.split() if w not in stopwords and len(w) > 2]
            return " ".join(terms)
        if not any([descricao, ncm, regime_empresa, cnae_principal, uf_origem, uf_destino]):
            descricao = extract_technical_terms(str(query))
        else:
            descricao = extract_technical_terms(descricao)
        results = retrieve_fiscal_context(
            index=index,
            descricao=descricao,
            ncm=ncm,
            regime_empresa=regime_empresa,
            cnae_principal=cnae_principal,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
            top_k=top_k
        )
        return [FiscalContextResult(r) for r in results]
def preprocess_query(text):
    stopwords = [
        r"\bqual(\s+é|\s+o|\s+a)?\b", r"\bmelhor\b", r"\bpara\b", r"\bcomo\b", r"\bdeve\b", r"\busar\b", r"\butilizar\b",
        r"\bNCM\b", r"\bimportado\b", r"\bproduto\b", r"\bclassifica(c|ç)ão\b", r"\bmeu\b", r"\bminha\b", r"\buma\b", r"\bum\b",
        r"\bser\b", r"\bcom\b", r"\bque\b", r"\bdo\b", r"\bdos\b", r"\bdas\b", r"\bno\b", r"\bna\b", r"\bse\b", r"\bpor\b"
    ]
    text = text.lower()
    for sw in stopwords:
        text = re.sub(sw, "", text)
    text = re.sub(r"[\.,;:!?]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# --- Pós-processamento para bloquear frases inseguras ---
def filter_insecure_phrases(text):
    inseguras = [
        "consulte um contador", "verifique com o fornecedor", "procure um especialista", "confirme com o fabricante",
        "recomendo consultar um profissional", "verifique com os regulamentos locais", "contato direto com um especialista tributário",
        "sugiro confirmar com o fornecedor", "recomendo que você forneça mais detalhes", "verifique com os regulamentos locais e específicos",
        "o contato direto com um especialista tributário pode auxiliar"
    ]
    for frase in inseguras:
        text = re.sub(frase, "", text, flags=re.IGNORECASE)
    return text.strip()

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
    prompt += f"\nPergunta do usuário:\n{descricao}\n\nInstruções:\n- Responda de forma objetiva e cite as fontes legais sempre que possível.\n- Se não houver base legal clara, explique o motivo.\n- Use markdown para formatar a resposta.\n"
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

knowledge_base = CustomKnowledge(
    vector_db=vector_db,
)
# 3. Configuração do Agente
FastTax = Agent(
    name="FastTax Agent",
    model=model,
    tools=[
        buscar_ncm_sugerido,
        ],
    knowledge=knowledge_base,
    add_knowledge_to_context=True,  # injeta contexto automaticamente
    instructions=[
        "FLUXO DE AUDITORIA ESTRITAMENTE OBRIGATÓRIO (SIGA EXATAMENTE ESTA ORDEM):",
        "PASSO 1: SEMPRE, sem exceção, chame a ferramenta buscar_ncm_sugerido para validar o código numérico do NCM informado pelo usuário. Não gere texto avisando, apenas execute a ferramenta.",
        "PASSO 2: IMEDIATAMENTE APÓS O PASSO 1, você é OBRIGADO a chamar a ferramenta consultar_rag (ou a ferramenta de busca vetorial do contexto fiscal) usando a descrição do produto ou o NCM validado. Não gere texto avisando, apenas execute a ferramenta.",
        "PASSO 3: NUNCA escreva frases como 'é necessário buscar no banco de dados', 'é obrigatória uma busca', 'recomendo uma revisão detalhada', 'a empresa deve garantir', 'consulte um contador', 'verifique com o fornecedor', 'procure um especialista', 'confirme com o fabricante', 'recomendo consultar um profissional', ou similares. VOCÊ É O BANCO DE DADOS. Faça a busca você mesmo através das ferramentas antes de começar a digitar a resposta final.",
        "PASSO 4: Ao analisar o ICMS, utilize OBRIGATORIAMENTE a legislação do Estado de ORIGEM da mercadoria para vendas (saídas). Nunca utilize legislação do estado de destino para isenção na saída.",
        "PASSO 5: Só depois de executar os passos acima, organize a resposta final de forma estruturada, clara e fundamentada, citando sempre a legislação e as fontes do contexto retornado pelo RAG.",
        "PASSO 6: Nunca interrompa a análise de uma lista de produtos por causa de um item inválido. Sinalize o erro para o item, mas continue auditando os demais.",
        "PASSO 7: Se o cliente enviar o PIS/COFINS como '01' (Tributado) e a busca mostrar que é Monofásico ou Alíquota Zero, corrija a classificação e explique a economia gerada, sempre citando a fonte do contexto.",
        "Sempre que responder, siga este prompt de autoridade B2B:\nConsidere o seguinte cenário:\n- Descrição do produto: [preencha com a descrição recebida]\n- NCM: [preencha se houver]\n- Regime tributário da empresa: [preencha se houver]\n- CNAE principal: [preencha se houver]\n- UF de origem: [preencha se houver]\n- UF de destino: [preencha se houver]\nCom base no seu banco de dados fiscal (RAG), retorne:\n- O(s) NCM(s) mais adequados para esse produto\n- A fundamentação legal encontrada\n- Se possível, cite exemplos de decisões fiscais ou instruções normativas relevantes\nResponda apenas com base no contexto encontrado no RAG."
    ],
    markdown=True,
    
)

if __name__ == "__main__":
    # Teste: busca relevante baseada na pergunta do usuário
    pergunta = "Quais regras fiscais se aplicam para venda de camiseta de algodão de SP para RJ?"
    resposta = FastTax.cli_app()