"""Router para indexação e gestão do pipeline RAG."""

import logging

from fastapi import APIRouter, HTTPException, Header, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import RAGIndexRequest, RAGIndexResponse, RAGStatsResponse
from app.routers.evaluate import set_rag_instance, get_rag_instance, resolve_api_key
import config
import security
from rag import AuditRAG

logger = logging.getLogger("kipiai.rag")

router = APIRouter(prefix="/api/rag", tags=["rag"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/index", response_model=RAGIndexResponse)
@limiter.limit("3/minute")
async def index_content(
    request: Request,
    body: RAGIndexRequest,
    authorization: str | None = Header(None),
) -> RAGIndexResponse:
    """Indexa conteúdo de múltiplas páginas para retrieval RAG."""
    api_key = resolve_api_key(body.api_key, authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key não configurada.")

    # Converte schemas para dicts que o AuditRAG espera
    pages = [
        {
            "url": p.url,
            "title": p.title,
            "content": p.content,
            "char_count": p.char_count,
        }
        for p in body.pages
    ]

    try:
        rag = AuditRAG(api_key)
        total_chunks = rag.ingest(pages)

        if total_chunks == 0:
            raise HTTPException(status_code=400, detail="Nenhum chunk gerado. Conteúdo insuficiente.")

        # Registra a instância RAG globalmente
        set_rag_instance(rag)

        stats = rag.get_stats()
        logger.info("RAG indexado: %d chunks, %d páginas", stats["total_chunks"], stats["total_pages"])

        return RAGIndexResponse(
            total_chunks=stats["total_chunks"],
            total_pages=stats["total_pages"],
            chunks_per_page=stats["chunks_per_page"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro na indexação RAG: %s", e)
        raise HTTPException(status_code=500, detail=security.safe_error_message(e))


@router.get("/stats", response_model=RAGStatsResponse)
async def rag_stats() -> RAGStatsResponse:
    """Retorna estatísticas do índice RAG ativo."""
    rag = get_rag_instance()
    if rag is None or not rag.is_ready:
        return RAGStatsResponse(
            total_chunks=0,
            total_pages=0,
            chunks_per_page={},
            is_ready=False,
        )

    stats = rag.get_stats()
    return RAGStatsResponse(
        total_chunks=stats["total_chunks"],
        total_pages=stats["total_pages"],
        chunks_per_page=stats["chunks_per_page"],
        is_ready=True,
    )


@router.delete("/clear")
async def clear_rag():
    """Limpa o índice RAG."""
    rag = get_rag_instance()
    if rag is not None:
        rag.clear()
    set_rag_instance(None)
    return {"status": "ok", "message": "Índice RAG limpo."}
