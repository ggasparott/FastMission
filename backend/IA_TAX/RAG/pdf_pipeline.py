import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from pypdf import PdfReader

try:
    from .RAG import build_query_vector, get_pinecone_index
except ImportError:
    from RAG import build_query_vector, get_pinecone_index


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    clean = _normalize_space(text)
    if not clean:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(clean)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(0, end - overlap)

    return chunks


def _vector_id(filename: str, page_number: int, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{filename}:{page_number}:{chunk_index}".encode("utf-8")).hexdigest()[:20]
    return f"pdf-{page_number:04d}-{chunk_index:04d}-{digest}"


def _build_metadata(
    text: str,
    source_file: str,
    page_number: int,
    chunk_index: int,
    regime_empresa_aplicavel: Optional[List[str]] = None,
    cnae_prefixos: Optional[List[str]] = None,
    uf_origem: Optional[str] = None,
    uf_destino: Optional[str] = None,
    tipo_regra: str = "pdf_documento",
    fonte: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "texto": text,
        "tipo_regra": tipo_regra,
        "fonte": fonte or source_file,
        "regime_empresa_aplicavel": regime_empresa_aplicavel or [],
        "cnae_prefixos": cnae_prefixos or [],
        "uf_origem": (uf_origem or "").upper(),
        "uf_destino": (uf_destino or "").upper(),
        "vigencia_inicio": now,
        "vigencia_fim": "",
        "ativo": True,
        "source_file": source_file,
        "page": page_number,
        "chunk_index": chunk_index,
    }


def parse_pdf_chunks(pdf_bytes: bytes, chunk_size: int = 1200, overlap: int = 150) -> List[Dict[str, Any]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    rows: List[Dict[str, Any]] = []

    for page_idx, page in enumerate(reader.pages, start=1):
        page_text = _normalize_space(page.extract_text() or "")
        if not page_text:
            continue

        chunks = _chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)
        for chunk_idx, chunk_text in enumerate(chunks, start=1):
            rows.append(
                {
                    "page": page_idx,
                    "chunk_index": chunk_idx,
                    "text": chunk_text,
                }
            )

    return rows


def ingest_pdf_to_pinecone(
    pdf_bytes: bytes,
    filename: str,
    regime_empresa_aplicavel: Optional[List[str]] = None,
    cnae_prefixos: Optional[List[str]] = None,
    uf_origem: Optional[str] = None,
    uf_destino: Optional[str] = None,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> Dict[str, Any]:
    chunks = parse_pdf_chunks(pdf_bytes, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return {
            "filename": filename,
            "chunks_total": 0,
            "upserted": 0,
            "message": "Nenhum texto extraído do PDF.",
        }

    vectors = []
    for entry in chunks:
        text = entry["text"]
        page_number = entry["page"]
        chunk_index = entry["chunk_index"]

        metadata = _build_metadata(
            text=text,
            source_file=filename,
            page_number=page_number,
            chunk_index=chunk_index,
            regime_empresa_aplicavel=regime_empresa_aplicavel,
            cnae_prefixos=cnae_prefixos,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
            fonte=filename,
        )

        vectors.append(
            {
                "id": _vector_id(filename, page_number, chunk_index),
                "values": build_query_vector(text),
                "metadata": metadata,
            }
        )

    index = get_pinecone_index()
    index.upsert(vectors=vectors)

    return {
        "filename": filename,
        "chunks_total": len(chunks),
        "upserted": len(vectors),
        "message": "PDF ingerido no Pinecone com sucesso.",
    }


def ingest_pdf_file_to_pinecone(
    pdf_path: str,
    regime_empresa_aplicavel: Optional[List[str]] = None,
    cnae_prefixos: Optional[List[str]] = None,
    uf_origem: Optional[str] = None,
    uf_destino: Optional[str] = None,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> Dict[str, Any]:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("O arquivo precisa ter extensão .pdf")

    with open(pdf_path, "rb") as f:
        content = f.read()

    if not content:
        raise ValueError("Arquivo PDF vazio")

    return ingest_pdf_to_pinecone(
        pdf_bytes=content,
        filename=os.path.basename(pdf_path),
        regime_empresa_aplicavel=regime_empresa_aplicavel,
        cnae_prefixos=cnae_prefixos,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
        chunk_size=chunk_size,
        overlap=overlap,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python backend/IA_TAX/RAG/pdf_pipeline.py CAMINHO_PDF [REGIMES] [CNAES] [UF_ORIGEM] [UF_DESTINO]"
        )

    pdf_path = sys.argv[1]
    regimes = [item.strip().upper() for item in (sys.argv[2] if len(sys.argv) > 2 else "").split(",") if item.strip()]
    cnaes = [item.strip() for item in (sys.argv[3] if len(sys.argv) > 3 else "").split(",") if item.strip()]
    uf_origem = (sys.argv[4] if len(sys.argv) > 4 else "").strip().upper()
    uf_destino = (sys.argv[5] if len(sys.argv) > 5 else "").strip().upper()

    result = ingest_pdf_file_to_pinecone(
        pdf_path=pdf_path,
        regime_empresa_aplicavel=regimes,
        cnae_prefixos=cnaes,
        uf_origem=uf_origem,
        uf_destino=uf_destino,
    )
    print(result)
