from datetime import datetime, timezone
from typing import Any, Dict, List

from RAG import build_query_vector, get_pinecone_index


def _rule_id(prefix: str, idx: int) -> str:
    return f"{prefix}-{idx:03d}"


def seed_rules() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return [
        {
            "id": _rule_id("reforma", 1),
            "texto": "Para empresas do Simples Nacional no varejo alimentar, manter atenção ao período de transição da CBS e IBS e validação de alíquota por estado de destino.",
            "tipo_regra": "reforma_tributaria",
            "fonte": "EC 132/2023 - resumo operacional",
            "regime_empresa_aplicavel": ["SIMPLES"],
            "cnae_prefixos": ["47", "4711", "4711301"],
            "uf_origem": None,
            "uf_destino": None,
            "vigencia_inicio": now,
            "vigencia_fim": None,
            "ativo": True,
        },
        {
            "id": _rule_id("reforma", 2),
            "texto": "No Lucro Presumido, revisar parametrização de CST e natureza de receita para coexistência de tributos legados e novos durante a transição.",
            "tipo_regra": "reforma_tributaria",
            "fonte": "Guia interno FastMission v1",
            "regime_empresa_aplicavel": ["LUCRO_PRESUMIDO"],
            "cnae_prefixos": ["46", "4639", "4639701"],
            "uf_origem": None,
            "uf_destino": None,
            "vigencia_inicio": now,
            "vigencia_fim": None,
            "ativo": True,
        },
        {
            "id": _rule_id("ncm", 1),
            "texto": "NCM 2203 (cervejas de malte) exige validação de classificação fiscal e regras estaduais de ICMS-ST quando aplicável.",
            "tipo_regra": "ncm",
            "fonte": "Tabela NCM + prática fiscal",
            "regime_empresa_aplicavel": ["SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"],
            "cnae_prefixos": ["11", "1105", "1105000"],
            "uf_origem": None,
            "uf_destino": None,
            "vigencia_inicio": now,
            "vigencia_fim": None,
            "ativo": True,
        },
        {
            "id": _rule_id("interestadual", 1),
            "texto": "Operações de saída SP para MG podem demandar validação de diferencial de alíquotas conforme destinatário e enquadramento da operação.",
            "tipo_regra": "interestadual",
            "fonte": "Procedimento operacional fiscal",
            "regime_empresa_aplicavel": ["SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"],
            "cnae_prefixos": ["47", "46"],
            "uf_origem": "SP",
            "uf_destino": "MG",
            "vigencia_inicio": now,
            "vigencia_fim": None,
            "ativo": True,
        },
        {
            "id": _rule_id("geral", 1),
            "texto": "Sempre validar consistência entre descrição do item, NCM informado e CFOP antes do cálculo tributário final.",
            "tipo_regra": "compliance",
            "fonte": "Checklist fiscal FastMission",
            "regime_empresa_aplicavel": ["SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"],
            "cnae_prefixos": [],
            "uf_origem": None,
            "uf_destino": None,
            "vigencia_inicio": now,
            "vigencia_fim": None,
            "ativo": True,
        },
    ]


def to_vector_record(rule: Dict[str, Any]) -> Dict[str, Any]:
    query_base = " ".join(
        filter(
            None,
            [
                rule.get("texto", ""),
                rule.get("tipo_regra", ""),
                " ".join(rule.get("regime_empresa_aplicavel", [])),
                " ".join(rule.get("cnae_prefixos", [])),
                rule.get("uf_origem") or "",
                rule.get("uf_destino") or "",
            ],
        )
    )
    return {
        "id": rule["id"],
        "values": build_query_vector(query_base),
        "metadata": {
            "texto": rule.get("texto"),
            "tipo_regra": rule.get("tipo_regra"),
            "fonte": rule.get("fonte"),
            "regime_empresa_aplicavel": rule.get("regime_empresa_aplicavel", []),
            "cnae_prefixos": rule.get("cnae_prefixos", []),
            "uf_origem": rule.get("uf_origem") or "",
            "uf_destino": rule.get("uf_destino") or "",
            "vigencia_inicio": rule.get("vigencia_inicio"),
            "vigencia_fim": rule.get("vigencia_fim") or "",
            "ativo": bool(rule.get("ativo", True)),
        },
    }


def populate() -> int:
    index = get_pinecone_index()
    records = [to_vector_record(rule) for rule in seed_rules()]
    index.upsert(vectors=records)
    return len(records)


if __name__ == "__main__":
    inserted = populate()
    print(f"Pinecone populado com {inserted} registros.")
