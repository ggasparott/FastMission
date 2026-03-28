def montar_prompt_beneficios_fiscais(contexto_rag, descricao_produto=None, ncm=None, regime_empresa=None, uf_origem=None, uf_destino=None):
    """
    Monta um prompt para a IA consultar o RAG e cruzar benefícios fiscais aplicáveis ao produto/empresa.
    """
    prompt = f"""
    Você é um consultor tributário especialista em benefícios fiscais brasileiros.
    Utilize o contexto legal extraído do RAG abaixo para identificar e cruzar todos os benefícios fiscais, incentivos, isenções, reduções de base de cálculo ou créditos presumidos que possam ser aplicados ao produto e cenário informados.

    Contexto legal extraído do RAG:
    {contexto_rag}

    Dados do produto/empresa:
    """
    if descricao_produto:
        prompt += f"- Descrição do produto: {descricao_produto}\n"
    if ncm:
        prompt += f"- NCM: {ncm}\n"
    if regime_empresa:
        prompt += f"- Regime tributário da empresa: {regime_empresa}\n"
    if uf_origem:
        prompt += f"- UF de origem: {uf_origem}\n"
    if uf_destino:
        prompt += f"- UF de destino: {uf_destino}\n"
    prompt += """

    Instruções:
    - Liste todos os benefícios fiscais encontrados no contexto que possam ser aplicados ao cenário acima.
    - Para cada benefício, explique a fundamentação legal (cite a fonte, lei ou artigo) e as condições para aplicação.
    - Se houver dúvidas ou múltiplas possibilidades, explique as alternativas e oriente o usuário sobre como confirmar a aplicabilidade.
    - Responda de forma objetiva, técnica e cite sempre as fontes legais encontradas.
    - Se não houver benefício aplicável, explique o motivo.
    """
    return prompt

def montar_prompt_llm(contexto_rag, csv_usuario):
    """
    Monta o prompt para o LLM com contexto e instruções para análise de planilha fiscal.
    Adapte as instruções conforme o fluxo desejado.
    """
    prompt = f"""
    Contexto de legislação e regras fiscais:
    {contexto_rag}

    Planilha enviada pelo usuário (colunas: Produto, NCM, CEST, Descrição):
    {csv_usuario}

Sua tarefa:
- Analise cada linha da planilha usando apenas o contexto acima.
- Se identificar que o NCM ou CEST está incorreto, sugira a correção e explique o motivo.
- Se a linha estiver correta, apenas escreva \"OK\".
- Para cada sugestão de alteração, forneça uma justificativa clara baseada no contexto.
- Ao final, devolva a planilha modificada (ou um relatório) com as colunas originais + colunas: Sugestao_NCM, Sugestao_CEST, Justificativa.

Responda apenas com a tabela modificada e as justificativas.
"""
    return prompt

# TODO: Adicione aqui funções utilitárias para outros tipos de prompt, exemplos, few-shot, etc.
# Exemplo:
def montar_prompt_validacao_ncm(ncm, contexto_rag):
    """
    Monta um prompt específico para validação de NCM usando o contexto do RAG.
    """
    prompt = f"""
    Contexto de legislação e regras fiscais:
    {contexto_rag}

    NCM a ser validado: {ncm}
"""
    return prompt

def montar_prompt_justificativa(descricao, ncm, cest, regime_empresa, uf_origem, uf_destino, contexto_rag):
    """
    Monta um prompt para solicitar justificativa detalhada sobre a classificação fiscal de um produto.
    """
    prompt = f"""
    Contexto de legislação e regras fiscais:
    {contexto_rag}

    Produto: {descricao}
    NCM: {ncm}
    CEST: {cest}
    Regime da empresa: {regime_empresa}
    UF Origem: {uf_origem}
    UF Destino: {uf_destino}
"""
    return prompt


# Exemplos few-shot para guiar o LLM
def exemplos_few_shot():
    """
    Retorna exemplos de perguntas e respostas para few-shot learning.
    """
    return [
        {
            "pergunta": "Produto: Correia de transmissão, NCM: 9999.9, CEST: 99.999.99",
            "resposta": "Sugestao_NCM: 4010.3, Sugestao_CEST: 01.006.00, Justificativa: Correia de transmissão corresponde à classificação fiscal conforme contexto."
        },
        {
            "pergunta": "Produto: Parafuso, NCM: 7318.15.00, CEST: 02.001.00",
            "resposta": "OK"
        },
    ]

# Função para montar prompt com exemplos few-shot
def montar_prompt_com_exemplos(contexto_rag, csv_usuario, exemplos):
    """
    Monta um prompt incluindo exemplos few-shot para melhorar a performance do LLM.
    exemplos: lista de dicionários com 'pergunta' e 'resposta'.
    """
    exemplos_str = "\n".join([
        f"Pergunta: {ex['pergunta']}\nResposta: {ex['resposta']}" for ex in exemplos
    ])
    prompt = f"""
Contexto de legislação e regras fiscais:
{contexto_rag}

Exemplos:
{exemplos_str}

Planilha enviada pelo usuário:
{csv_usuario}

Siga as instruções do prompt principal.
"""
    return prompt