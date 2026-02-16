#!/usr/bin/env python
"""
Script de IA para validação de produtos na Reforma Tributária.
Valida NCM, CEST, e identifica benefícios fiscais (IBS/CBS).

Roda ISOLADO do FastAPI - chamado via subprocess.
Para MVP: Implementação com regras básicas da Reforma.
"""
import sys
import json


def validar_produto_reforma(descricao: str, ncm_original: str, cest_original: str = None) -> dict:
    """
    Valida produto para conformidade com Reforma Tributária (IBS/CBS).
    
    Verifica:
    1. NCM está correto para a descrição?
    2. CEST está preenchido quando obrigatório?
    3. Produto tem direito a benefício fiscal?
    4. Regime tributário correto?
    5. Alíquotas IBS/CBS aplicáveis
    
    Args:
        descricao: Descrição do produto
        ncm_original: NCM cadastrado
        cest_original: CEST cadastrado (opcional)
    
    Returns:
        dict com validações e sugestões
    """
    
    descricao_lower = descricao.lower()
    
    # Resultado padrão
    resultado = {
        # NCM
        "ncm_sugerido": ncm_original,
        "status": "VALIDO",
        "explicacao": "Classificação fiscal compatível com a descrição.",
        "confianca": 75,
        
        # CEST
        "cest_sugerido": cest_original,
        "cest_obrigatorio": "NAO",
        
        # Regime Tributário
        "regime_tributario": "NORMAL",
        "aliquota_ibs": 26.5,  # Alíquota padrão estimada
        "aliquota_cbs": 0.0,
        
        # Benefícios
        "possui_beneficio_fiscal": "NAO",
        "tipo_beneficio": None,
        "artigo_legal": None
    }
    
    
    # ========================================
    # REGRA 1: CESTA BÁSICA (Alíquota ZERO)
    # ========================================
    produtos_cesta_basica = [
        "arroz", "feijao", "leite", "pao", "farinha", "macarrao",
        "acucar", "sal", "cafe", "oleo", "manteiga", "margarina"
    ]
    
    if any(produto in descricao_lower for produto in produtos_cesta_basica):
        resultado.update({
            "regime_tributario": "IMUNE",
            "aliquota_ibs": 0.0,
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "SIM",
            "tipo_beneficio": "Cesta básica nacional - Alíquota zero",
            "artigo_legal": "LC 214/2025 Art. 18, §1º",
            "explicacao": "Produto da cesta básica tem imunidade tributária (alíquota 0% IBS/CBS).",
            "confianca": 95
        })
        
        # Validar NCM típico de alimentos
        if not ncm_original.startswith(("1006", "1101", "0401", "1507", "1701")):
            resultado["status"] = "DIVERGENTE"
            resultado["explicacao"] += " ATENÇÃO: NCM pode estar incorreto para produto alimentício."
    
    
    # ========================================
    # REGRA 2: MEDICAMENTOS (Redução 60%)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["medicamento", "remedio", "farmacia", "comprimido", "capsula"]):
        resultado.update({
            "regime_tributario": "ALIQUOTA_REDUZIDA",
            "aliquota_ibs": 10.6,  # 60% de redução sobre 26.5%
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "SIM",
            "tipo_beneficio": "Medicamentos - Redução de 60%",
            "artigo_legal": "LC 214/2025 Art. 18, §2º, I",
            "confianca": 90
        })
        
        if not ncm_original.startswith("3004"):
            resultado["status"] = "DIVERGENTE"
            resultado["ncm_sugerido"] = "3004.90.99"
            resultado["explicacao"] = "Medicamentos devem ser classificados no capítulo 30.04 do NCM."
    
    
    # ========================================
    # REGRA 3: DISPOSITIVOS MÉDICOS (Redução 60%)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["seringa", "marca-passo", "protese", "cadeira de rodas", "equipamento medico"]):
        resultado.update({
            "regime_tributario": "ALIQUOTA_REDUZIDA",
            "aliquota_ibs": 10.6,
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "SIM",
            "tipo_beneficio": "Dispositivos médicos - Redução de 60%",
            "artigo_legal": "LC 214/2025 Art. 18, §2º, II",
            "confianca": 88
        })
    
    
    # ========================================
    # REGRA 4: EDUCAÇÃO (Redução 60%)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["livro", "caderno", "material escolar", "apostila"]):
        resultado.update({
            "regime_tributario": "ALIQUOTA_REDUZIDA",
            "aliquota_ibs": 10.6,
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "SIM",
            "tipo_beneficio": "Materiais educacionais - Redução de 60%",
            "artigo_legal": "LC 214/2025 Art. 18, §2º, III",
            "confianca": 85
        })
    
    
    # ========================================
    # REGRA 5: ENERGIA ELÉTRICA (Cashback Baixa Renda)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["energia eletrica", "fornecimento de energia"]):
        resultado.update({
            "regime_tributario": "CASHBACK",
            "aliquota_ibs": 26.5,  # Alíquota normal, mas com devolução
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "POSSIVEL",
            "tipo_beneficio": "Cashback para baixa renda (até 100kWh/mês)",
            "artigo_legal": "LC 214/2025 Art. 19",
            "explicacao": "Energia elétrica tem cashback para famílias de baixa renda inscritas no CadÚnico.",
            "confianca": 80
        })
    
    
    # ========================================
    # REGRA 6: COMBUSTÍVEIS (CEST OBRIGATÓRIO)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["gasolina", "diesel", "etanol", "combustivel", "gnv"]):
        resultado.update({
            "cest_obrigatorio": "SIM",
            "cest_sugerido": "06.001.00" if not cest_original else cest_original,
            "regime_tributario": "NORMAL",
            "aliquota_ibs": 26.5,
            "confianca": 92
        })
        
        if not cest_original:
            resultado["status"] = "DIVERGENTE"
            resultado["explicacao"] = "CEST é OBRIGATÓRIO para combustíveis (Substituição Tributária). Sugestão: 06.001.00"
        
        if not ncm_original.startswith("2710"):
            resultado["ncm_sugerido"] = "2710.12.51"
            resultado["status"] = "DIVERGENTE"
            resultado["explicacao"] += " | NCM incorreto para combustível."
    
    
    # ========================================
    # REGRA 7: BEBIDAS ALCOÓLICAS (CEST + Alíquota Seletiva)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["cerveja", "vinho", "whisky", "vodka", "cachaca"]):
        resultado.update({
            "cest_obrigatorio": "SIM",
            "cest_sugerido": "02.001.00" if not cest_original else cest_original,
            "regime_tributario": "NORMAL",
            "aliquota_ibs": 26.5,
            "explicacao": "Bebidas alcoólicas: CEST obrigatório + Imposto Seletivo adicional.",
            "confianca": 90
        })
        
        if not cest_original:
            resultado["status"] = "DIVERGENTE"
            resultado["explicacao"] += " | CEST obrigatório não informado."
    
    
    # ========================================
    # REGRA 8: PRODUTOS INDUSTRIALIZADOS (CEST em alguns casos)
    # ========================================
    elif any(palavra in descricao_lower for palavra in ["refrigerante", "sorvete", "biscoito wafer"]):
        resultado["cest_obrigatorio"] = "VERIFICAR"
        resultado["explicacao"] = "Produto pode exigir CEST dependendo da operação (verifique legislação estadual)."
    
    
    # ========================================
    # VALIDAÇÕES GERAIS DE NCM
    # ========================================
    
    # Chocolate vs Wafer
    if "chocolate" in descricao_lower and not ncm_original.startswith("1806"):
        resultado["status"] = "DIVERGENTE"
        resultado["ncm_sugerido"] = "1806.32.00"
        resultado["explicacao"] = "Produto descrito como 'chocolate' deve estar no capítulo 18.06 do NCM."
        resultado["confianca"] = 85
    
    # Wafer/Biscoito
    if "wafer" in descricao_lower or "biscoito" in descricao_lower:
        if not ncm_original.startswith("1905"):
            resultado["status"] = "DIVERGENTE"
            resultado["ncm_sugerido"] = "1905.90.00"
            resultado["explicacao"] = "Wafers e biscoitos devem estar no capítulo 19.05 (Produtos de padaria)."
            resultado["confianca"] = 90
    
    # Notebooks/Computadores
    if any(palavra in descricao_lower for palavra in ["notebook", "laptop", "computador"]):
        if not ncm_original.startswith("8471"):
            resultado["status"] = "DIVERGENTE"
            resultado["ncm_sugerido"] = "8471.30.12"
            resultado["explicacao"] = "Computadores portáteis devem estar no capítulo 84.71."
            resultado["confianca"] = 95
    
    
    return resultado


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
        cest = entrada.get('cest', None)
        
        if not descricao or not ncm:
            raise ValueError("Entrada inválida: 'descricao' e 'ncm' são obrigatórios")
        
        # Processar
        resultado = validar_produto_reforma(descricao, ncm, cest)
        
        # Retornar JSON no stdout
        print(json.dumps(resultado, ensure_ascii=False))
        
    except Exception as e:
        # Em caso de erro, retornar JSON de erro
        erro = {
            "ncm_sugerido": None,
            "status": "ERRO",
            "explicacao": f"Erro interno na validação: {str(e)}",
            "confianca": 0,
            "cest_sugerido": None,
            "cest_obrigatorio": "NAO",
            "regime_tributario": "NORMAL",
            "aliquota_ibs": 26.5,
            "aliquota_cbs": 0.0,
            "possui_beneficio_fiscal": "NAO",
            "tipo_beneficio": None,
            "artigo_legal": None
        }
        print(json.dumps(erro, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
