#!/usr/bin/env python
"""
Script de IA para validação de NCM.
Roda ISOLADO do FastAPI - chamado via subprocess.

Para MVP: Implementação mock (você vai adicionar LLM real depois)
"""
import sys
import json


def validar_ncm(descricao: str, ncm_original: str) -> dict:
    """
    Valida se NCM está correto para a descrição do produto.
    
    Para MVP: Retorna mock baseado em regras simples.
    TODO: Integrar com OpenAI/Claude/outro LLM
    """
    
    descricao_lower = descricao.lower()
    
    # === MOCK: Regras simples para demonstração ===
    
    # Regra 1: Chocolate deve começar com 1806
    if 'chocolate' in descricao_lower and not ncm_original.startswith('1806'):
        return {
            "ncm_sugerido": "1806.32.00",
            "status": "DIVERGENTE",
            "explicacao": (
                "Produto descrito como 'chocolate' deve ser classificado no "
                "capítulo 18.06 (Chocolate e outras preparações alimentícias contendo cacau). "
                "NCM atual não corresponde a produtos de chocolate."
            ),
            "confianca": 85
        }
    
    # Regra 2: Wafer deve estar em 1905
    if 'wafer' in descricao_lower and not ncm_original.startswith('1905'):
        return {
            "ncm_sugerido": "1905.90.00",
            "status": "DIVERGENTE",
            "explicacao": (
                "Wafers e bolachas recheadas são classificadas no capítulo 19.05 "
                "(Produtos de padaria). NCM atual não corresponde."
            ),
            "confianca": 90
        }
    
    # Regra 3: Parafusos devem estar em 7318
    if any(palavra in descricao_lower for palavra in ['parafuso', 'porca', 'prego']):
        if not ncm_original.startswith('7318'):
            return {
                "ncm_sugerido": "7318.15.00",
                "status": "DIVERGENTE",
                "explicacao": (
                    "Parafusos, pregos e artigos similares de ferro/aço são "
                    "classificados no capítulo 73.18."
                ),
                "confianca": 95
            }
    
    # Regra 4: Notebooks/computadores em 8471
    if any(palavra in descricao_lower for palavra in ['notebook', 'computador', 'laptop']):
        if not ncm_original.startswith('8471'):
            return {
                "ncm_sugerido": "8471.30.12",
                "status": "DIVERGENTE",
                "explicacao": (
                    "Computadores portáteis (notebooks) são classificados no "
                    "capítulo 84.71 (Máquinas automáticas para processamento de dados)."
                ),
                "confianca": 98
            }
    
    # Se passou por todas as regras, considerar válido
    return {
        "ncm_sugerido": ncm_original,
        "status": "VALIDO",
        "explicacao": "Classificação NCM compatível com a descrição do produto.",
        "confianca": 75
    }


def main():
    """
    Entry point para subprocess.
    Lê JSON do stdin, processa, escreve JSON no stdout.
    """
    try:
        # Ler entrada do stdin
        entrada = json.loads(sys.stdin.read())
        
        descricao = entrada.get('descricao', '')
        ncm = entrada.get('ncm', '')
        
        if not descricao or not ncm:
            raise ValueError("Entrada inválida: 'descricao' e 'ncm' são obrigatórios")
        
        # Processar
        resultado = validar_ncm(descricao, ncm)
        
        # Retornar JSON no stdout
        print(json.dumps(resultado, ensure_ascii=False))
        
    except Exception as e:
        # Em caso de erro, retornar JSON de erro
        erro = {
            "ncm_sugerido": None,
            "status": "ERRO",
            "explicacao": f"Erro interno: {str(e)}",
            "confianca": 0
        }
        print(json.dumps(erro, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
