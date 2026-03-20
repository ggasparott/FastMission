
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