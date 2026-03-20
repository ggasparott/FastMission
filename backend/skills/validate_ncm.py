#!/usr/bin/env python
import requests
import json
import sys
"""
Script de IA para validação de NCM.
Roda ISOLADO do FastAPI - chamado via subprocess.

Para MVP: Implementação mock (você vai adicionar LLM real depois)
"""
import sys


def buscar_ncm_sugerido(ncm_original: str) -> str:
    ncm_limpo = validar_ncm(ncm_original)  # Valida formato do NCM antes de consultar a API
    url = f"https://brasilapi.com.br/api/ncm/v1/{ncm_limpo}"
    headers = {
        "User-Agent": "FastTax-Agent/1.0 (Fast Development)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            resultado = {
                "ncm_sugerido": data.get("codigo", ncm_original),
                "descricao": data.get("descricao", ""),
                "data_inicio": data.get("data_inicio"),
                "data_fim": data.get("data_fim"),
                "ato_legal": f"{data.get('tipo_ato')} {data.get('numero_ato')}/{data.get('ano_ato')}",
                "status": "VALIDO"
            }
            return json.dumps(resultado, ensure_ascii=False)
        elif response.status_code == 404:
            return f"Atenção: O NCM {ncm_limpo} não existe ou é inválido segundo a base de dados."

        else:
            return f"Erro ao consultar a Brasil API. Código de estado HTTP: {response   .status_code}"
    except requests.exceptions.RequestException as erro:
        # Captura erros de rede, timeout, ou falhas na ligação à internet
        return f"Falha de comunicação com a API: {str(erro)}"
    
def validar_ncm(ncm_original: str) -> str:
    ncm_limpo = ncm_original.replace(".", "").strip()
    if len(ncm_limpo) != 8 or not ncm_limpo.isdigit():
        return {
            "ncm_sugerido": None,
            "status": "INVALIDO",
            "explicacao": f"O NCM '{ncm_original}' é inválido. Ele deve conter exatamente 8 dígitos numéricos.",
            "confianca": 0
        }
    return ncm_limpo
    





if __name__ == "__main__":
    # Teste de execução rápida (pode descomentar para testar)
    print(buscar_ncm_sugerido("3402.50.00"))
