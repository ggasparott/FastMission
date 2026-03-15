import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from pinecone import Pinecone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))
load_dotenv(os.path.join(BASE_DIR, "..", "..", ".env"))

INDEX_NAME = os.getenv("PINECONE_INDEX", "fiscal-reforma-v1")
INDEX_HOST = os.getenv("PINECONE_HOST", "").strip()
VECTOR_SIZE = int(os.getenv("RAG_VECTOR_SIZE", "512"))
TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def build_query_vector(text: str, size: int = VECTOR_SIZE) -> List[float]:
	"""
	Gera vetor determinístico sem dependência externa de embedding.
	Útil para cenário MVP com retrieval majoritariamente filtrado por metadata.
	"""
	seed = hashlib.sha256((text or "").encode("utf-8")).digest()
	return [((seed[i % len(seed)] / 255.0) * 2.0 - 1.0) for i in range(size)]


def get_pinecone_index():
	api_key = os.getenv("PINECONE_API_KEY", "").strip()
	if not api_key:
		raise ValueError("PINECONE_API_KEY não configurado no .env")

	pc = Pinecone(api_key=api_key)
	if INDEX_HOST:
		return pc.Index(host=INDEX_HOST)
	return pc.Index(INDEX_NAME)



def cnae_prefixes(cnae: str) -> List[str]:
	value = "".join(ch for ch in (cnae or "") if ch.isdigit())
	if not value:
		return []
	prefixes = {value[:2], value[:4], value[:7]}
	return [p for p in prefixes if p]


def _contains_any(values: Any, candidates: List[str]) -> bool:
	if not candidates:
		return True
	if values is None:
		return False
	if isinstance(values, list):
		values_norm = {str(v).upper() for v in values}
		return any(c.upper() in values_norm for c in candidates)
	return str(values).upper() in {c.upper() for c in candidates}


def retrieve_fiscal_context(
	index,
	descricao: str,
	ncm: str,
	regime_empresa: str,
	cnae_principal: str,
	uf_origem: str,
	uf_destino: str,
	top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
	now_iso = datetime.now(timezone.utc).isoformat()
	# Query vector compatível com dimensão do índice (RAG_VECTOR_SIZE)
	query_text = " ".join(filter(None, [descricao, f"NCM {ncm}" if ncm else "", regime_empresa, uf_origem, uf_destino]))
	query_vector = build_query_vector(query_text) if query_text.strip() else [0.0] * VECTOR_SIZE

	base_filter = {"ativo": {"$eq": True}}
	response = index.query(
		vector=query_vector,
		top_k=top_k,
		include_metadata=True,
		filter=base_filter,
	)

	matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
	cnaes = cnae_prefixes(cnae_principal)
	results: List[Dict[str, Any]] = []

	for match in matches:
		metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
		payload = metadata or {}

		if regime_empresa and not _contains_any(payload.get("regime_empresa_aplicavel"), [regime_empresa]):
			continue
		if cnaes and not _contains_any(payload.get("cnae_prefixos"), cnaes):
			continue
		if uf_origem and payload.get("uf_origem") and str(payload.get("uf_origem")).upper() != uf_origem.upper():
			continue
		if uf_destino and payload.get("uf_destino") and str(payload.get("uf_destino")).upper() != uf_destino.upper():
			continue

		vig_inicio = payload.get("vigencia_inicio")
		vig_fim = payload.get("vigencia_fim")
		if vig_inicio and now_iso < str(vig_inicio):
			continue
		if vig_fim and now_iso > str(vig_fim):
			continue

		score = match.get("score") if isinstance(match, dict) else getattr(match, "score", None)
		results.append(
			{
				"score": float(score) if score is not None else None,
				"texto": payload.get("texto"),
				"tipo_regra": payload.get("tipo_regra"),
				"fonte": payload.get("fonte"),
				"payload": payload,
			}
		)

	return results


def test_connection() -> None:
	api_key = os.getenv("PINECONE_API_KEY", "").strip()
	if not api_key:
		raise ValueError("PINECONE_API_KEY não configurado no .env")

	pc = Pinecone(api_key=api_key)
	indexes = pc.list_indexes()
	print("Conexão com Pinecone OK")
	print(indexes)

	# Smoke-test de conexão ao índice configurado
	index = get_pinecone_index()
	_ = index.describe_index_stats()
	print(f"Index Pinecone acessível: {INDEX_NAME if not INDEX_HOST else INDEX_HOST}")


if __name__ == "__main__":
	test_connection()