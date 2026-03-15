#!/usr/bin/env python
"""
Skill de agente consultivo (sem acoplamento com FastAPI/DB).

Entrada: JSON via stdin
Saída: JSON via stdout

Orquestra:
1) validar_produto_reforma
2) retrieve_fiscal_context (RAG Pinecone)
3) chamadas para APIs externas (tools)
"""

import importlib.util
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List

from validate_reforma import validar_produto_reforma


def _load_rag_module():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rag_path = os.path.join(backend_dir, "IA_TAX", "RAG", "RAG.py")

    spec = importlib.util.spec_from_file_location("rag_runtime", rag_path)
    if not spec or not spec.loader:
        raise RuntimeError("Não foi possível carregar módulo RAG")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call_tool_api(tool: Dict[str, Any], base_payload: Dict[str, Any]) -> Dict[str, Any]:
    name = tool.get("name") or "tool_api"
    url = (tool.get("url") or "").strip()
    if not url:
        return {"name": name, "ok": False, "error": "url não informada"}

    method = (tool.get("method") or "POST").upper()
    headers = tool.get("headers") or {}
    payload = {**base_payload, **(tool.get("payload") or {})}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url=url, data=body, method=method)
    request.add_header("Content-Type", "application/json")

    for key, value in headers.items():
        if value is not None:
            request.add_header(str(key), str(value))

    timeout_seconds = int(os.getenv("AGENT_TOOL_API_TIMEOUT", "15"))

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except Exception:
                data = {"raw": raw}
            return {
                "name": name,
                "ok": True,
                "status_code": response.status,
                "data": data,
            }
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "error": str(exc),
        }


def analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    descricao = payload.get("descricao", "")
    ncm = payload.get("ncm", "")
    cest = payload.get("cest")
    regime_empresa = (payload.get("regime_empresa") or "LUCRO_REAL").upper()
    uf_origem = (payload.get("uf_origem") or "SP").upper()
    uf_destino = (payload.get("uf_destino") or "SP").upper()
    cnae_principal = payload.get("cnae_principal", "")
    pergunta = payload.get("pergunta", "")
    top_k = int(payload.get("top_k", 5))
    usar_rag = bool(payload.get("usar_rag", True))
    tool_apis = payload.get("tool_apis") or []

    if not descricao or not ncm:
        raise ValueError("'descricao' e 'ncm' são obrigatórios")

    validacao = validar_produto_reforma(
        descricao=descricao,
        ncm_original=ncm,
        cest_original=cest,
        regime_empresa=regime_empresa,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        cnae_principal=cnae_principal,
    )

    contexto_rag: List[Dict[str, Any]] = []
    if usar_rag:
        try:
            rag_module = _load_rag_module()
            index = rag_module.get_pinecone_index()
            contexto_rag = rag_module.retrieve_fiscal_context(
                index=index,
                descricao=descricao,
                ncm=ncm,
                regime_empresa=regime_empresa,
                cnae_principal=cnae_principal,
                uf_origem=uf_origem,
                uf_destino=uf_destino,
                top_k=top_k,
            )
        except Exception as exc:
            contexto_rag = [{"erro_rag": str(exc)}]

    base_tool_payload = {
        "descricao": descricao,
        "ncm": ncm,
        "ncm_sugerido": validacao.get("ncm_sugerido"),
        "regime_empresa": regime_empresa,
        "uf_origem": uf_origem,
        "uf_destino": uf_destino,
        "cnae_principal": cnae_principal,
        "pergunta": pergunta,
    }

    resultados_tools = [_call_tool_api(tool, base_tool_payload) for tool in tool_apis]

    recomendacoes = [
        f"Status fiscal: {validacao.get('status', 'PENDENTE')}",
        f"NCM sugerido: {validacao.get('ncm_sugerido') or ncm}",
        f"Benefício fiscal: {validacao.get('possui_beneficio_fiscal') or 'NAO'}",
    ]

    if validacao.get("cest_obrigatorio") == "SIM" and not cest:
        recomendacoes.append("Preencher CEST no cadastro para conformidade.")

    if contexto_rag and isinstance(contexto_rag[0], dict) and contexto_rag[0].get("texto"):
        recomendacoes.append("Usar o contexto RAG retornado como suporte consultivo.")

    return {
        "status_analise": "ok",
        "resumo_consultivo": validacao.get("explicacao") or "Análise concluída.",
        "validacao_reforma": validacao,
        "contexto_rag": contexto_rag,
        "resultados_tools": resultados_tools,
        "recomendacoes": recomendacoes,
    }


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        response = analyze(payload)
        print(json.dumps(response, ensure_ascii=False))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status_analise": "erro",
                    "resumo_consultivo": f"Falha na execução da skill: {str(exc)}",
                    "validacao_reforma": {},
                    "contexto_rag": [],
                    "resultados_tools": [],
                    "recomendacoes": [],
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
